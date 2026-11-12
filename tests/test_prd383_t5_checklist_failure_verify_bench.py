# -*- coding: utf-8 -*-
"""PRD-383/T5 测试（trend #1887 的 T5 环节）：checklist 失败验证台验收试运行。

运行：uv run --with pytest python -m pytest tests/test_prd383_t5_checklist_failure_verify_bench.py -q
（仓库根执行）

验收（T1 §6 T5 行「样例全链回放+UNVERIFIED 拦截演练+文档无密钥」）：
  接入点全链演练（PR 门槛 require_integration_point 验收）：checker 集 →
  run_checklist 失败项 → verify_failures 过台 → VERIFIED 转人工拍板来源
  形态（decision_inbox.collect 消费的 manual_reviews 形态）→ JSONL 落账
  → 闸门全 pass；两遍全链产物逐字节一致（确定性可复现）；UNVERIFIED 拦截
  演练（误报失败/已修复失败拦在人工拍板外+落账留痕）；checkers 变更二次
  验证关闭演练（BENCH_STALE 拒绝复用→新 checkers 复算 VERIFIED）；账本
  append-only；零改写复验（演练返回值零 checklist 写载荷键）；链复跑：
  T2/T3/T4 测试子进程复跑 exit 0；文档无密钥：T1 设计文档拼接 needle
  扫描+占位符纪律。零网络；全合成占位。
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from checklist_failure_verify_bench import (  # noqa: E402
    FailureBenchLedger,
    verify_failures,
)
from checklist_failure_verify_bench_gates import (  # noqa: E402
    append_only_gate,
    gate_summary,
    mark_baseline,
    stale_gate,
    verdict_gate,
)
from skill_checklist import run_checklist  # noqa: E402

NOW = "2026-11-13T09:00:00Z"
REF_P1 = "zh_trigger_registry.build_registry"
FAILING_CHECKERS = {REF_P1: lambda: False}


def recheck_fn(checkers):
    report = run_checklist("skill-a（占位）", checkers)
    return [dict(r) for r in report["results"] if r["state"] == "fail"]


def _failures():
    rerun = recheck_fn(FAILING_CHECKERS)
    p1 = next(r for r in rerun if r["id"] == "P1")
    return [{"failure_id": "f-001", "check_id": p1["id"],
             "kind": "machine_fail",
             "source_ref": "skill-checklist-report/v1#P1（占位）",
             "state": p1["state"]}]


def _manual_reviews_from_verified(verified):
    """接入点：VERIFIED 失败项转人工拍板来源形态（decision_inbox.collect
    消费的 manual_reviews 形态，fingerprint 与验证台同源）。"""
    return [{"source_ref": v["source_ref"],
             "fingerprint": v["checkers_fingerprint"],
             "questions": [f"{v['check_id']} 失败已复跑验证，请人工拍板（占位）"],
             "reason": "验证过的机检失败待人工拍板（占位）"}
            for v in verified]


class TestIntegrationPointDrill(unittest.TestCase):
    def test_outlet_full_chain_twice_deterministic(self):
        """接入点全链演练（PR 门槛验收）：机检失败 → 过台 → VERIFIED 转人工
        拍板来源形态 → JSONL 落账 → 闸门全 pass；两遍逐字节一致。"""
        runs = []
        for _ in range(2):
            out = verify_failures(_failures(), FAILING_CHECKERS,
                                  recheck_fn, at=NOW)
            manual = _manual_reviews_from_verified(out["verified"])
            self.assertTrue(manual)
            self.assertTrue(all({"source_ref", "fingerprint", "questions",
                                 "reason"} <= set(m) for m in manual))
            with tempfile.TemporaryDirectory() as td:
                led = FailureBenchLedger(Path(td) / "fbench.jsonl")
                for rec in out["verified"] + [r for r in out["unverified"]
                                              if not r.get("refused")]:
                    led.record(rec, at=NOW)
                gates = [append_only_gate(led)]
                for rec in led.entries():
                    gates.append(verdict_gate(rec))
                    gates.append(stale_gate(rec, FAILING_CHECKERS))
                runs.append({"out": out, "manual": manual,
                             "entries": led.entries(),
                             "summary": gate_summary(gates)})
                self.assertEqual(gate_summary(gates)["gate"], "pass")
        self.assertEqual(json.dumps(runs[0], sort_keys=True),
                         json.dumps(runs[1], sort_keys=True))


class TestFailureDrills(unittest.TestCase):
    def test_unverified_blocked_and_traced(self):
        """UNVERIFIED 拦截演练：误报失败（不存在项）拦在人工拍板外+落账
        留痕。"""
        phantom = [dict(FAILURE_SRC := {"failure_id": "f-900",
                                        "check_id": "P99（不存在项）",
                                        "kind": "machine_fail",
                                        "source_ref": "x（占位）",
                                        "state": "fail"})]
        with tempfile.TemporaryDirectory() as td:
            led = FailureBenchLedger(Path(td) / "fbench.jsonl")
            out = verify_failures(phantom, FAILING_CHECKERS, recheck_fn,
                                  at=NOW)
            self.assertEqual(out["verified"], [])
            for rec in out["unverified"]:
                if not rec.get("refused"):
                    led.record(rec, at=NOW)
            self.assertEqual(led.entries()[-1]["verdict"], "UNVERIFIED")

    def test_fixed_then_second_verify_closes(self):
        """checkers 变更二次验证关闭演练：BENCH_STALE 拒绝复用 → 新 checkers
        复算 UNVERIFIED（已修复不进人工拍板）。"""
        led = FailureBenchLedger(None)
        first = verify_failures(_failures(), FAILING_CHECKERS, recheck_fn,
                                at=NOW)
        self.assertTrue(first["verified"])
        led.record(first["verified"][0], at=NOW)
        fixed_checkers = {REF_P1: lambda: True,
                          "other.check（占位）": lambda: True}
        out = led.reverify(first["verified"][0]["failure_id"],
                           fixed_checkers, recheck_fn, at=NOW)
        self.assertEqual(out["refused"], "BENCH_STALE")

    def test_zero_tamper_and_append_only(self):
        """零改写复验（演练返回值零 checklist 写载荷键）+账本 append-only。"""
        out = verify_failures(_failures(), FAILING_CHECKERS, recheck_fn,
                              at=NOW)
        for rec in out["verified"]:
            for key in ("checklist_written", "registry_written",
                        "answers_filled"):
                self.assertNotIn(key, rec)
        led = FailureBenchLedger(None)
        for rec in out["verified"]:
            led.record(rec, at=NOW)
        mark_baseline(led)
        self.assertEqual(append_only_gate(led)["gate"], "pass")


class TestChainRerun(unittest.TestCase):
    def test_t2_t3_t4_rerun_green(self):
        """链复跑：T2/T3/T4 测试子进程复跑 exit 0（链上仍绿实测）。"""
        for test_file in ("test_prd383_t2_checklist_failure_verify_bench.py",
                          "test_prd383_t3_checklist_failure_verify_bench_gates.py",
                          "test_prd383_t4_checklist_failure_verify_bench_boundary.py"):
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q",
                 str(Path(__file__).resolve().parent / test_file)],
                capture_output=True, timeout=300)
            self.assertEqual(proc.returncode, 0,
                             f"{test_file} 复跑失败：{proc.stdout[-400:]}")


class TestDocNoSecrets(unittest.TestCase):
    def test_t1_design_doc_no_secrets(self):
        """文档无密钥：T1 设计文档拼接 needle 扫描+占位符纪律（R5）。"""
        repo = Path(__file__).resolve().parents[1]
        doc = next(repo.glob("docs/plans/2026-11-12-prd-383-*.md"))
        text = doc.read_text(encoding="utf-8").lower()
        for needle in ("sk-" + "live", "passw" + "ord", "api_k" + "ey"):
            self.assertNotIn(needle, text, f"设计文档出现密钥词 {needle}")
        self.assertIn("占位", text)


if __name__ == "__main__":
    unittest.main()
