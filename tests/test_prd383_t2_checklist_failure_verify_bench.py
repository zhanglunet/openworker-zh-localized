# -*- coding: utf-8 -*-
"""PRD-383/T2 测试（trend #1887 的 T2 环节）：checklist 失败验证台。

运行：uv run --with pytest python -m pytest tests/test_prd383_t2_checklist_failure_verify_bench.py -q
（仓库根执行）

覆盖（T1 §4 + R1~R4）：verify_failure 八件套校验（缺一 BENCH_INCOMPLETE）；
真实机检器串联（run_checklist 失败项重跑复现 → VERIFIED；复现不出 →
UNVERIFIED 词表封闭）；verify_failures 人工拍板来源包装（UNVERIFIED 拦下）；
FailureBenchLedger JSONL 真实落库+八件套缺一/词表外/REPRO_MISMATCH 声称
拒绝；reverify checkers 变更二次验证（指纹不符 BENCH_STALE 拒绝复用/一致
正常复验）；AST 零 LLM 零网络零子进程零 checklist 写词面+TAMPERED 红线
不变。零网络；全合成占位。
"""
import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from checklist_failure_verify_bench import (  # noqa: E402
    BENCH_SCHEMA,
    ERROR_CODES,
    FailureBenchError,
    FailureBenchLedger,
    VERDICTS,
    checkers_fingerprint,
    verify_failure,
    verify_failures,
)
from skill_checklist import run_checklist  # noqa: E402

NOW = "2026-11-13T09:00:00Z"

# 真实 check_ref（引擎按 check_ref 适配既有模块）；P1 fail 为复现源
REF_P1 = "zh_trigger_registry.build_registry"
FAILING_CHECKERS = {REF_P1: lambda: False}
PASSING_CHECKERS = {REF_P1: lambda: True}
FAILURE = {"failure_id": "f-001", "check_id": "P1", "kind": "machine_fail",
           "source_ref": "skill-checklist-report/v1#P1（占位）",
           "state": "fail"}


def recheck_fn(checkers):
    """注入式机检重跑（复用 run_checklist 引擎形态）。"""
    report = run_checklist("skill-a（占位）", checkers)
    return [dict(r) for r in report["results"] if r["state"] == "fail"]


class TestVerifyFailure(unittest.TestCase):
    def test_verified_with_real_rerun(self):
        """真实机检器串联：P1 失败项与重跑结果一致 → VERIFIED；checkers
        指纹 sha16: 前缀确定性。"""
        out = verify_failure(FAILURE, FAILING_CHECKERS, recheck_fn, at=NOW)
        self.assertEqual(out["verdict"], "VERIFIED")
        self.assertEqual(out["schema"], BENCH_SCHEMA)
        fp = checkers_fingerprint(FAILING_CHECKERS)
        self.assertTrue(fp.startswith("sha16:"))
        self.assertEqual(out["checkers_fingerprint"], fp)

    def test_unverified_when_fixed(self):
        """机检器已修复（P1 转 pass）→ 复现不出 → UNVERIFIED（防误报失败
        进人工拍板）。"""
        out = verify_failure(FAILURE, PASSING_CHECKERS, recheck_fn, at=NOW)
        self.assertEqual(out["verdict"], "UNVERIFIED")
        self.assertFalse(out["reproduce"]["rerun_match"])

    def test_incomplete_refused(self):
        bad = dict(FAILURE)
        del bad["state"]
        out = verify_failure(bad, FAILING_CHECKERS, recheck_fn, at=NOW)
        self.assertEqual(out["refused"], "BENCH_INCOMPLETE")
        out2 = verify_failure(FAILURE, FAILING_CHECKERS, None, at=NOW)
        self.assertEqual(out2["refused"], "BENCH_INCOMPLETE")

    def test_verdict_vocab_closed(self):
        self.assertEqual(set(VERDICTS), {"VERIFIED", "UNVERIFIED"})


class TestVerifyFailures(unittest.TestCase):
    def test_outlet_blocks_unverified(self):
        """人工拍板来源包装：UNVERIFIED 拦下不进人工拍板（R1）。"""
        failures = [FAILURE, dict(FAILURE, failure_id="f-002",
                                  check_id="P99（不存在项）")]
        out = verify_failures(failures, FAILING_CHECKERS, recheck_fn, at=NOW)
        self.assertEqual(len(out["verified"]), 1)
        self.assertEqual(out["unverified_count"], 1)
        self.assertEqual(out["unverified"][0]["failure_id"], "f-002")


class TestFailureBenchLedger(unittest.TestCase):
    def test_jsonl_persistence_append_only(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "fbench" / "ledger.jsonl"
            led = FailureBenchLedger(path)
            led.record(verify_failure(dict(FAILURE, failure_id="f-001"),
                                      FAILING_CHECKERS, recheck_fn, at=NOW),
                       at=NOW)
            led.record(verify_failure(dict(FAILURE, failure_id="f-002"),
                                      FAILING_CHECKERS, recheck_fn, at=NOW),
                       at=NOW)
            self.assertEqual(len(led.entries()), 2)
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0])["failure_id"], "f-001")

    def test_record_refusals(self):
        led = FailureBenchLedger(None)
        with self.assertRaisesRegex(FailureBenchError, "BENCH_INCOMPLETE"):
            led.record({"schema": BENCH_SCHEMA}, at=NOW)
        with self.assertRaisesRegex(FailureBenchError, "BENCH_REPRO_MISMATCH"):
            bad = verify_failure(dict(FAILURE, failure_id="f-001"),
                                 FAILING_CHECKERS, recheck_fn, at=NOW)
            bad = dict(bad, verdict="VERIFIED",
                       reproduce={"rerun_match": False, "detail": "改（占位）"})
            led.record(bad, at=NOW)


class TestReverify(unittest.TestCase):
    def test_stale_refuses_reuse(self):
        """checkers 变更 → BENCH_STALE 拒绝复用旧 VERIFIED。"""
        led = FailureBenchLedger(None)
        led.record(verify_failure(dict(FAILURE, failure_id="f-001"),
                                  FAILING_CHECKERS, recheck_fn, at=NOW),
                   at=NOW)
        new_checkers = {"P1": lambda: True}
        out = led.reverify("f-001", new_checkers, recheck_fn, at=NOW)
        self.assertEqual(out["refused"], "BENCH_STALE")

    def test_same_checkers_reverify_ok(self):
        led = FailureBenchLedger(None)
        led.record(verify_failure(dict(FAILURE, failure_id="f-001"),
                                  FAILING_CHECKERS, recheck_fn, at=NOW),
                   at=NOW)
        out = led.reverify("f-001", FAILING_CHECKERS, recheck_fn, at=NOW)
        self.assertEqual(out["verdict"], "VERIFIED")


class TestRedline(unittest.TestCase):
    def test_ast_zero_llm_zero_network_zero_tamper(self):
        """AST：零 LLM 零网络零子进程零 checklist 写/注册表写词面（TAMPERED
        红线不变）。"""
        banned = {"urllib", "requests", "socket", "http", "subprocess",
                  "openai", "anthropic", "zh_trigger_registry",
                  "zh_skill_ref"}
        src = SCRIPTS / "checklist_failure_verify_bench.py"
        tree = ast.parse(src.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertFalse(imported & banned, imported & banned)
        names = {n.id.lower() for n in ast.walk(tree)
                 if isinstance(n, ast.Name)}
        names |= {n.attr.lower() for n in ast.walk(tree)
                  if isinstance(n, ast.Attribute)}
        for word in ("write_checklist", "write_registry", "fill_answers"):
            self.assertNotIn(word, names, f"出现改写词面 {word}")

    def test_error_codes_closed(self):
        self.assertEqual(set(ERROR_CODES),
                         {"BENCH_INCOMPLETE", "BENCH_REPRO_MISMATCH",
                          "BENCH_STALE"})


if __name__ == "__main__":
    unittest.main()
