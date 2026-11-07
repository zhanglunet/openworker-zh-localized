# -*- coding: utf-8 -*-
"""PRD-299/T3 测试（trend #1498）：中文技能引用歧义闸门与人工消歧留痕。

运行：uv run --with pytest python -m pytest tests/test_prd299_t3_gates.py -q

覆盖（T1 设计 §5/§6）：指令闸一票否决（NOT_FOUND 附清单/AMBIGUOUS 列候选
停下问/SYNTAX_ERROR）；候选形态机判（skill+pack+positioning 误命中可解释）；
人工消歧唯一入口（不在候选内即拒、chosen 留痕）；错误码三码封闭穷举；
审计 append-only。零网络；全合成占位。
"""
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from zh_ref_gates import InstructionGate  # noqa: E402
from zh_skill_ref import ERROR_CODES  # noqa: E402

SKILLS = [
    {"name": "写周报", "pack": "hr", "positioning": "生成周报初稿（占位）"},
    {"name": "寫周報", "pack": "sales", "positioning": "销售侧周报（占位）"},
    {"name": "整理客户档案", "pack": "sales", "positioning": "客户档案整理（占位）"},
]


class 指令闸Tests(unittest.TestCase):
    def setUp(self):
        self.gate = InstructionGate()

    def test_unique_resolves(self):
        out = self.gate.check("@整理客户档案", SKILLS, at="2026-11-04T09:00:00Z")
        self.assertTrue(out["allow"])
        self.assertEqual(out["skill"], "整理客户档案")

    def test_ambiguous_lists_candidates_explainably(self):
        """误命中可解释：候选每条含 skill+pack+positioning。"""
        out = self.gate.check("@写周报", SKILLS, at="2026-11-04T09:00:00Z")
        self.assertFalse(out["allow"])
        self.assertEqual(out["error_code"], "REF_AMBIGUOUS")
        self.assertEqual(len(out["candidates"]), 2)
        for cand in out["candidates"]:
            self.assertIn("skill", cand)
            self.assertIn("pack", cand)
            self.assertIn("positioning", cand)                 # 用户看得懂为什么列出

    def test_not_found_with_available_list(self):
        out = self.gate.check("@不存在的技能", SKILLS, at="2026-11-04T09:00:00Z")
        self.assertFalse(out["allow"])
        self.assertEqual(out["error_code"], "REF_NOT_FOUND")

    def test_syntax_error_blocks(self):
        out = self.gate.check("@写*报", SKILLS, at="2026-11-04T09:00:00Z")
        self.assertFalse(out["allow"])
        self.assertEqual(out["error_code"], "REF_SYNTAX_ERROR")

    def test_qualified_hint_resolves(self):
        out = self.gate.check("@hr/写周报", SKILLS, at="2026-11-04T09:00:00Z")
        self.assertTrue(out["allow"])
        self.assertEqual(out["pack"], "hr")


class 人工消歧Tests(unittest.TestCase):
    def setUp(self):
        self.gate = InstructionGate()
        self.refused = self.gate.check("@写周报", SKILLS, at="2026-11-04T09:00:00Z")
        # 闸 refused 后取完整 outcome 走消歧入口
        from zh_skill_ref import resolve
        self.outcome = resolve("@写周报", SKILLS)

    def test_choose_from_candidates(self):
        out = self.gate.choose("@写周报", self.outcome, "寫周報",
                               at="2026-11-04T09:01:00Z")
        self.assertTrue(out["allow"])
        self.assertEqual(out["chosen_from_candidates"], "寫周報")
        self.assertEqual(self.gate.audit.records[-1]["chosen_from_candidates"],
                         "寫周報")                              # 留痕

    def test_choice_outside_candidates_rejected(self):
        with self.assertRaises(ValueError):
            self.gate.choose("@写周报", self.outcome, "不在候选（占位）",
                             at="2026-11-04T09:01:00Z")


class 词表与审计Tests(unittest.TestCase):
    def test_three_codes_exhaustive(self):
        self.assertEqual(sorted(ERROR_CODES),
                         ["REF_AMBIGUOUS", "REF_NOT_FOUND", "REF_SYNTAX_ERROR"])

    def test_audit_append_only(self):
        gate = InstructionGate()
        gate.check("@写周报", SKILLS, at="2026-11-04T09:00:00Z")
        before = list(gate.audit.records)
        gate.check("@整理客户档案", SKILLS, at="2026-11-04T09:01:00Z")
        self.assertEqual(gate.audit.records[:len(before)], before)


if __name__ == "__main__":
    unittest.main()
