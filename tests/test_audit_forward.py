"""Audit forwarding to a SIEM.

Three promises, in priority order, and each one is a test here:

1. a turn never waits on the collector,
2. a down collector never breaks the agent,
3. the local log stays the source of truth.

The interesting failures are all in the "sink misbehaves" direction — hangs, 500s, being
slower than events arrive — so that's what these drive.
"""

from __future__ import annotations

import threading
import time

import pytest

from coworker.audit import AuditStore
from coworker.audit_forward import AuditForwarder, forwarder_from_config


class Sink:
    """A stand-in collector. `delay` and `fail` reproduce the sad paths."""

    def __init__(self, delay: float = 0.0, fail: bool = False):
        self.batches: list[list[dict]] = []
        self.delay = delay
        self.fail = fail
        self._lock = threading.Lock()

    def __call__(self, batch):
        if self.delay:
            time.sleep(self.delay)
        if self.fail:
            raise RuntimeError("collector is down")
        with self._lock:
            self.batches.append(list(batch))

    @property
    def events(self) -> list[dict]:
        with self._lock:
            return [e for b in self.batches for e in b]


@pytest.fixture
def forwarder():
    made: list[AuditForwarder] = []

    def build(sink, **kw):
        fwd = AuditForwarder("https://siem.invalid/ingest", sender=sink, **kw)
        made.append(fwd)
        return fwd

    yield build
    for f in made:
        f.close(timeout=1)


def test_events_reach_the_sink(forwarder):
    sink = Sink()
    fwd = forwarder(sink, batch=2)
    for i in range(4):
        fwd.send({"tool": f"t{i}"})
    assert fwd.flush(timeout=3)
    assert [e["tool"] for e in sink.events] == ["t0", "t1", "t2", "t3"]


def test_send_does_not_wait_on_a_slow_sink(forwarder):
    """Promise 1. A collector taking half a second per batch must cost the turn nothing."""
    fwd = forwarder(Sink(delay=0.5), batch=1)
    start = time.time()
    for i in range(20):
        fwd.send({"tool": f"t{i}"})
    assert time.time() - start < 0.1, "send() blocked on the collector"


def test_a_failing_sink_never_raises(forwarder):
    """Promise 2."""
    fwd = forwarder(Sink(fail=True), batch=1)
    for i in range(5):
        fwd.send({"tool": f"t{i}"})  # must not raise
    fwd.flush(timeout=2)


def test_queue_is_bounded_and_keeps_the_newest(forwarder):
    """A full queue means the sink is behind; the recent events are what an investigation
    starts from, and unbounded growth in a long-lived desktop process is worse than a gap."""
    sink = Sink(delay=5)  # never drains during the test
    fwd = forwarder(sink, batch=1, max_queue=10)
    for i in range(200):
        fwd.send({"tool": f"t{i}"})
    assert fwd.dropped > 0
    # Whatever is still queued is from the tail of the stream, not the head.
    remaining = [fwd._q.get_nowait()["tool"] for _ in range(fwd._q.qsize())]
    assert remaining and all(int(t[1:]) > 100 for t in remaining), remaining[:5]


def test_local_log_is_written_even_when_forwarding_fails(tmp_path):
    """Promise 3: a dropped forward is a gap in the SIEM, never in the audit trail."""

    class Exploding:
        def send(self, event):
            raise RuntimeError("boom")

    store = AuditStore(tmp_path / "audit.db", forwarder=Exploding())
    store.append({"session_id": "s1", "tool": "write_file", "stage": "finished"})
    rows = store.list()
    assert len(rows) == 1 and rows[0]["tool"] == "write_file"


def test_forwarded_payload_is_the_sanitized_one(tmp_path):
    """Whatever is redacted on disk must be redacted on the wire — same rule set, not a
    second one that can drift."""
    seen: list[dict] = []

    class Capture:
        def send(self, event):
            seen.append(event)

    store = AuditStore(tmp_path / "audit.db", forwarder=Capture())
    store.append(
        {
            "session_id": "s1",
            "tool": "http_request",
            "arguments": {"url": "https://x", "api_key": "sk-live-secret"},
            "stage": "finished",
        }
    )
    assert seen and seen[0]["args"]["api_key"] == "[redacted]"
    assert "sk-live-secret" not in str(seen[0])


def test_no_forwarder_when_unconfigured():
    class Cfg:
        audit_forward_url = ""

    assert forwarder_from_config(Cfg()) is None


def test_non_http_url_is_refused():
    class Cfg:
        audit_forward_url = "file:///etc/passwd"

    assert forwarder_from_config(Cfg()) is None


def test_token_can_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("CORP_SIEM_TOKEN", "from-env")
    fwd = AuditForwarder("https://siem.invalid", token="${CORP_SIEM_TOKEN}", sender=Sink())
    try:
        assert fwd.token == "from-env"
    finally:
        fwd.close(timeout=1)


def test_kill_switch(monkeypatch):
    class Cfg:
        audit_forward_url = "https://siem.invalid/ingest"

    monkeypatch.setenv("COWORKER_DISABLE_AUDIT_FORWARD", "1")
    assert forwarder_from_config(Cfg()) is None


def test_audit_store_without_config_has_no_forwarder(tmp_path, monkeypatch):
    monkeypatch.setenv("COWORKER_DISABLE_AUDIT_FORWARD", "1")
    store = AuditStore(tmp_path / "audit.db")
    store.append({"tool": "x", "stage": "finished"})
    assert store.list()[0]["tool"] == "x"
