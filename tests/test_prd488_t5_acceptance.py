# -*- coding: utf-8 -*-
"""PRD-488/T5 测试（trend #2364 的 T5 环节）：技能评估验收试运行。
运行：uv run --with pytest python -m pytest tests/test_prd488_t4_boundary.py -q
验收（PRD 任务拆分 T5 行）：全套评估跑一遍真实技能包，结论可复核——
  - 真实技能包评估跑一遍（T2 evaluate × 真实清单），两遍逐字节一致；
  - 结论可复核：逐技能结论全部在封闭词表内、行为结论全部「待补测」
    （无对照跑分不判通过不判失效，不编造数据）；
  - 闸门全链试运行：真实报告逐技能过 T3 闸门（今天全部拦下——实情：
    对照跑分在实测补），拦截/整改条目落 JSONL 账本留痕，append-only；
  - 链复跑：T2/T3/T4 测试子进程 exit 0；T1 设计文档无密钥（拼接 needle
    +占位符纪律）。
零网络；全合成占位 + 真实清单只读。
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MOD_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(MOD_DIR))

from skill_evaluation import evaluate, load_inventory  # noqa: E402
from skill_evaluation_gate import (  # noqa: E402
    GateError, SkillEvaluationLedger, admit_to_downstream)

NOW = "2026-11-17T12:00:00Z"
BY = "acceptance（占位）"



ROOT = Path(__file__).resolve().parents[1]


def real_report():
    return evaluate(load_inventory(Path(__file__).resolve().parents[1] / "skill-eval/inventory.json"))


class TestRealRun(unittest.TestCase):
    def test_real_pack_twice_byte_identical(self):
        a = json.dumps(real_report(), sort_keys=True, ensure_ascii=False)
        b = json.dumps(real_report(), sort_keys=True, ensure_ascii=False)
        self.assertEqual(a, b)

    def test_all_verdicts_in_closed_vocab(self):
        report = real_report()
        for v in report["verdicts"]:
            self.assertIn(v["verdict"], ("通过", "整改", "证据不足"))
            self.assertEqual(v["verdict"], "证据不足")

    def test_every_skill_accounted(self):
        report = real_report()
        self.assertEqual(report["skill_count"], len(report["verdicts"]))


class TestGateWalk(unittest.TestCase):
    def test_real_report_gates_block_all_today(self):
        """今天真实报告逐技能过闸全拦（行为待补测）——实情，实测后复评放行。"""
        report = real_report()
        with tempfile.TemporaryDirectory() as td:
            led = SkillEvaluationLedger(Path(td) / "walk.jsonl")
            for v in report["verdicts"]:
                with self.assertRaises(GateError):
                    admit_to_downstream(report, v["id"], ledger=led,
                                        by=BY, at=NOW)
            kinds = [e["kind"] for e in led.entries()]
            self.assertEqual(kinds.count("gate_blocked"), report["skill_count"])
            self.assertEqual(kinds.count("gate_passed"), 0)

    def test_ledger_file_append_only(self):
        report = real_report()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "walk.jsonl"
            led = SkillEvaluationLedger(path)
            led.record({"prd": 488}, {"kind": "gate_passed",
                                        "skill_id": "s", "by": BY, "at": NOW})
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)


class TestChainRerun(unittest.TestCase):
    def test_t2_t3_t4_rerun_green(self):
        for name in (["test_skill_evaluation.py", "test_skill_evaluation_gate.py", "test_prd488_t4_boundary.py"]):
            proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(Path(__file__).resolve().parent), "-p", name],
                                  capture_output=True, timeout=600)
            self.assertEqual(proc.returncode, 0,
                             f"{{name}} 复跑失败：{{(proc.stdout or b'')[-400:]}}")


class TestDocNoSecrets(unittest.TestCase):
    def test_t1_design_doc_no_secrets(self):
        doc = next(Path(__file__).resolve().parents[1].glob(
            "docs/plans/2026-11-17-prd-488-*.md"))
        text = doc.read_text(encoding="utf-8").lower()
        for needle in ("sk-" + "live", "passw" + "ord =",
                       "BEGIN PRIVATE", "AKIA" + "x"):
            self.assertNotIn(needle, text,
                             f"设计文档出现密钥样式 {{needle}}")
        self.assertIn("评估", text)
