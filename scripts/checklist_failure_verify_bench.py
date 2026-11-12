# -*- coding: utf-8 -*-
"""PRD-383/T2（trend issue #1887 的 T2 环节）：checklist 失败验证台最小实现。

按 T1 设计（docs/plans/2026-11-12-prd-383-checklist-failure-verification-bench-design.md）
§4 落地：

  - verify_failure(failure, checkers, recheck_fn)：逐条失败复跑验证
    ——recheck_fn 注入式重跑同一 checker（checkers 只读，零新增检查规则
    R2）；复跑结果与失败项一致（同 check_id+状态 fail）→ VERIFIED，否则
    UNVERIFIED（词表封闭）；checkers 指纹 sha16: 前缀确定性；
  - verify_failures(failures, checkers, recheck_fn)：人工拍板来源包装
    （接入点：run_checklist 失败项之后、decision_inbox.collect
    (manual_reviews) 之前）——UNVERIFIED 拦下不进人工拍板（R1）；
  - FailureBenchLedger：机器可读 JSONL 落账（路径注入，append-only R3/R4）；
    八件套缺一 BENCH_INCOMPLETE 拒绝入账；
  - reverify：checkers 变更二次验证——指纹不符 → BENCH_STALE 拒绝复用旧
    验证（R4 关闭以最新 VERIFIED 为准）。

零 checklist 状态改写零注册表写（TAMPERED 红线不变）；零网络零子进程；
示例全虚构占位。
测试：tests/test_prd383_t2_checklist_failure_verify_bench.py
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

BENCH_SCHEMA = "checklist-failure-verify-bench/v1"
VERDICTS = ("VERIFIED", "UNVERIFIED")
ERROR_CODES = ("BENCH_INCOMPLETE", "BENCH_REPRO_MISMATCH", "BENCH_STALE")


class FailureBenchError(ValueError):
    """验证台违规——显形拒绝。"""


def checkers_fingerprint(checkers: dict[str, Callable[[], Any]]) -> str:
    """checker 集指纹（sha16: 前缀，checker 名清单 canonical JSON 摘要）。"""
    names = sorted(checkers or {})
    canon = json.dumps(names, ensure_ascii=False, separators=(",", ":"))
    return "sha16:" + hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]


def _recusal(code: str, detail: str) -> dict[str, Any]:
    return {"schema": BENCH_SCHEMA, "refused": code, "detail": detail,
            "verdict": None}


def _reproduced(failure: dict[str, Any],
                rerun: list[dict[str, Any]]) -> bool:
    """复现判定：重跑结果中存在同 check_id+状态 fail 的失败项。"""
    for r in rerun:
        if (str(r.get("id")) == str(failure.get("check_id"))
                and r.get("state") == failure.get("state")):
            return True
    return False


def verify_failure(failure: dict[str, Any],
                   checkers: dict[str, Callable[[], Any]],
                   recheck_fn: Callable[[dict], list[dict[str, Any]]],
                   *, at: str = "") -> dict[str, Any]:
    """逐条失败复跑验证（R1/R2）：重跑同一 checker，复现 → VERIFIED。"""
    if not isinstance(failure, dict):
        return _recusal("BENCH_INCOMPLETE", "failure 非对象")
    missing = [k for k in ("failure_id", "check_id", "kind", "source_ref",
                           "state") if not failure.get(k)]
    if missing:
        return _recusal("BENCH_INCOMPLETE", f"八件套缺 {missing}")
    if not callable(recheck_fn):
        return _recusal("BENCH_INCOMPLETE", "recheck_fn 未注入")
    rerun = recheck_fn(copy.deepcopy(checkers)) or []
    match = _reproduced(failure, rerun)
    return {
        "schema": BENCH_SCHEMA,
        "failure_id": failure["failure_id"],
        "check_id": failure["check_id"],
        "kind": failure["kind"],
        "source_ref": failure["source_ref"],
        "checkers_fingerprint": checkers_fingerprint(checkers),
        "failure": copy.deepcopy(failure),
        "reproduce": {"rerun_match": match,
                      "detail": f"复跑 {len(rerun)} 项（占位）"},
        "verdict": "VERIFIED" if match else "UNVERIFIED",
        "at": at,
    }


def verify_failures(failures: list[dict[str, Any]],
                    checkers: dict[str, Callable[[], Any]],
                    recheck_fn: Callable[[dict], list[dict[str, Any]]],
                    *, at: str = "") -> dict[str, Any]:
    """人工拍板来源包装（接入点）：UNVERIFIED 拦下不进人工拍板（R1）。"""
    verified: list[dict[str, Any]] = []
    unverified: list[dict[str, Any]] = []
    for f in failures or []:
        out = verify_failure(f, checkers, recheck_fn, at=at)
        if out.get("refused") or out["verdict"] == "UNVERIFIED":
            unverified.append(out)
        else:
            verified.append(out)
    return {"schema": BENCH_SCHEMA, "verified": verified,
            "unverified": unverified, "unverified_count": len(unverified)}


class FailureBenchLedger:
    """验证账本（R3/R4）：JSONL append-only；八件套缺一拒绝入账。"""

    _REQUIRED = ("failure_id", "check_id", "kind", "source_ref",
                 "checkers_fingerprint", "failure", "verdict")

    def __init__(self, path: str | Path | None = None) -> None:
        self._records: list[dict[str, Any]] = []
        self._path = Path(path) if path else None

    def record(self, out: dict[str, Any], *, at: str = "") -> dict[str, Any]:
        if out.get("refused"):
            raise FailureBenchError(f"{out['refused']}：{out['detail']}")
        rec = dict(out, at=at)
        missing = [k for k in self._REQUIRED if rec.get(k) in (None, "")]
        if missing:
            raise FailureBenchError(f"BENCH_INCOMPLETE：账目缺 {missing}")
        if rec["verdict"] not in VERDICTS:
            raise FailureBenchError(f"BENCH_INCOMPLETE：verdict 词表外 "
                                    f"{rec['verdict']!r}")
        if rec["verdict"] == "VERIFIED" and not rec["reproduce"]["rerun_match"]:
            raise FailureBenchError("BENCH_REPRO_MISMATCH：声称 VERIFIED 但"
                                    "复跑 match=false——验证结论与复现证据"
                                    "不一致")
        self._records.append(copy.deepcopy(rec))
        if self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False,
                                    sort_keys=True) + "\n")
        return dict(rec)

    def entries(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self._records]

    def latest_for(self, failure_id: str) -> dict[str, Any] | None:
        found = [r for r in self._records if r["failure_id"] == failure_id]
        return dict(found[-1]) if found else None

    def reverify(self, failure_id: str,
                 checkers: dict[str, Callable[[], Any]],
                 recheck_fn: Callable[[dict], list[dict[str, Any]]],
                 *, at: str = "") -> dict[str, Any]:
        """checkers 变更二次验证（R4）：指纹不符 → BENCH_STALE 拒绝复用。"""
        prior = self.latest_for(failure_id)
        fp_now = checkers_fingerprint(checkers)
        if prior and prior["checkers_fingerprint"] != fp_now:
            return _recusal("BENCH_STALE",
                            f"{failure_id} 旧验证 checkers 指纹与当前不符——"
                            "机检器变更后须重新验证，旧 VERIFIED 不复用")
        base = {"failure_id": failure_id,
                "check_id": (prior or {}).get("check_id") or "",
                "kind": (prior or {}).get("kind") or "",
                "source_ref": (prior or {}).get("source_ref") or "",
                "state": ((prior or {}).get("failure") or {}).get("state")}
        return self.record(verify_failure(base, checkers, recheck_fn,
                                          at=at), at=at)
