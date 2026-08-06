"""Ship audit events to an enterprise log sink (SIEM).

The local audit log answers "what did the agent do on this machine". Compliance asks a
different question — "show me every action across the fleet" — and that needs the events
somewhere central.

Three constraints shape this, in priority order:

1. **A turn must never wait on the SIEM.** Forwarding happens on a background thread;
   ``send`` only enqueues. An endpoint that takes 30s to answer costs the user nothing.
2. **A down SIEM must never break the agent.** Every failure path swallows and logs. There
   is no configuration in which "the log collector is unreachable" stops someone working.
3. **The local log stays the source of truth.** Events are written to SQLite first and
   forwarded after. A dropped forward is a gap in the SIEM, never in the audit trail.

The queue is bounded and drops the OLDEST event when full, counting the drops. An unbounded
queue would trade a visible gap for invisible memory growth in a long-lived desktop process,
and a full queue means the sink is already behind — the newest events are the ones worth
keeping.

Configuration (global config only — it decides where activity data goes):

    audit_forward_url     = "https://siem.corp.internal/ingest"
    audit_forward_token   = "${CORP_SIEM_TOKEN}"   # sent as Bearer; ${VAR} resolved
    audit_forward_batch   = 50                     # events per POST
    audit_forward_timeout = 5                      # seconds

The payload is ``{"events": [...]}`` — the same sanitized shape the local log stores, so a
secret redacted on disk is redacted on the wire.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import re
import threading
import time
from typing import Any, Optional

logger = logging.getLogger("coworker.audit")

DEFAULT_BATCH = 50
DEFAULT_TIMEOUT = 5.0
MAX_QUEUE = 5000
# Don't narrate every failure of an endpoint that's been down for an hour.
_LOG_EVERY = 60.0

_ENV_REF = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$")


def _resolve(value: str) -> str:
    """``${CORP_SIEM_TOKEN}`` → the environment value, so a token need not sit in config."""
    match = _ENV_REF.match((value or "").strip())
    if match:
        return os.environ.get(match.group(1), "")
    return value or ""


class AuditForwarder:
    def __init__(
        self,
        url: str,
        *,
        token: str = "",
        batch: int = DEFAULT_BATCH,
        timeout: float = DEFAULT_TIMEOUT,
        max_queue: int = MAX_QUEUE,
        sender=None,
    ) -> None:
        self.url = url
        self.token = _resolve(token)
        self.batch = max(1, int(batch or DEFAULT_BATCH))
        self.timeout = float(timeout or DEFAULT_TIMEOUT)
        self._q: queue.Queue = queue.Queue(maxsize=max(10, int(max_queue)))
        self._sender = sender or self._post
        self._stop = threading.Event()
        self._dropped = 0
        self._last_error_at = 0.0
        self._thread = threading.Thread(
            target=self._run, name="coworker-audit-forward", daemon=True
        )
        self._thread.start()

    # -- producer side (called on the turn's thread; must stay cheap) ----------------

    def send(self, event: dict[str, Any]) -> None:
        try:
            self._q.put_nowait(event)
        except queue.Full:
            # Drop the oldest, keep the newest: a full queue means the sink is behind, and
            # recent activity is what an investigation starts from.
            try:
                self._q.get_nowait()
                self._dropped += 1
                self._q.put_nowait(event)
            except (queue.Empty, queue.Full):  # pragma: no cover - lost a race, fine
                self._dropped += 1

    @property
    def dropped(self) -> int:
        return self._dropped

    def close(self, timeout: float = 2.0) -> None:
        self._stop.set()
        self._thread.join(timeout=timeout)

    def flush(self, timeout: float = 2.0) -> bool:
        """Wait for the queue to drain — for tests and for a clean shutdown."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._q.empty():
                time.sleep(0.02)  # let an in-flight batch finish posting
                return True
            time.sleep(0.01)
        return False

    # -- consumer side --------------------------------------------------------------

    def _run(self) -> None:
        while not self._stop.is_set():
            batch = self._drain()
            if not batch:
                time.sleep(0.05)
                continue
            self._deliver(batch)
        remaining = self._drain()
        if remaining:
            self._deliver(remaining)

    def _drain(self) -> list[dict[str, Any]]:
        batch: list[dict[str, Any]] = []
        while len(batch) < self.batch:
            try:
                batch.append(self._q.get_nowait())
            except queue.Empty:
                break
        return batch

    def _deliver(self, batch: list[dict[str, Any]]) -> None:
        try:
            self._sender(batch)
        except Exception as exc:  # noqa: BLE001 - constraint 2: never break the agent
            now = time.time()
            if now - self._last_error_at > _LOG_EVERY:
                self._last_error_at = now
                logger.warning(
                    "audit forwarding failed (%s); %d event(s) lost, %d dropped so far",
                    exc,
                    len(batch),
                    self._dropped,
                )

    def _post(self, batch: list[dict[str, Any]]) -> None:
        import urllib.request

        payload = json.dumps({"events": batch}, ensure_ascii=False).encode()
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(self.url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            if resp.status >= 400:  # pragma: no cover - urllib raises for these
                raise RuntimeError(f"HTTP {resp.status}")


def forwarder_from_config(cfg=None) -> Optional[AuditForwarder]:
    """Build a forwarder from the global config, or None when forwarding is off."""
    if os.environ.get("COWORKER_DISABLE_AUDIT_FORWARD"):
        return None
    if cfg is None:
        from .config import load_config

        cfg = load_config()
    url = (getattr(cfg, "audit_forward_url", "") or "").strip()
    if not url:
        return None
    if not url.lower().startswith(("http://", "https://")):
        logger.warning("audit_forward_url must be http(s); forwarding disabled")
        return None
    try:
        return AuditForwarder(
            url,
            token=getattr(cfg, "audit_forward_token", "") or "",
            batch=getattr(cfg, "audit_forward_batch", DEFAULT_BATCH),
            timeout=getattr(cfg, "audit_forward_timeout", DEFAULT_TIMEOUT),
        )
    except Exception as exc:  # noqa: BLE001 - misconfiguration must not stop startup
        logger.warning("could not start audit forwarding (%s); continuing without it", exc)
        return None


__all__ = ["AuditForwarder", "forwarder_from_config"]
