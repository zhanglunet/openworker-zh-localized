# -*- coding: utf-8 -*-
"""PRD-299/T2 测试（trend #1497）：@中文技能名引用解析最小实现。

运行：uv run --with pytest python -m pytest tests/test_prd299_t2_zh_skill_ref.py -q

覆盖（T1 设计 §3/§4/§5/§6）：归一四规则确定性（全半角/繁简/去首尾空白/
不合并中间空白）+ normalized 可回放；parse 两形态与禁止形态；resolve 归一
后精确匹配→确定技能、歧义列候选请用户选不猜、NOT_FOUND 附清单、显式
限定优先；人工消歧 chosen 留痕；二值返回；RefAudit append-only。
零网络；全合成占位。
"""
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from zh_skill_ref import (  # noqa: E402
    RefAudit,
    RefSyntaxError,
    normalize,
    parse,
    resolve,
)

SKILLS = [
    {"name": "写周报", "pack": "hr", "positioning": "生成周报初稿（占位）"},
    {"name": "寫周報", "pack": "sales", "positioning": "销售侧周报（占位）"},
    {"name": "整理客户档案", "pack": "sales", "positioning": "客户档案整理（占位）"},
]


class TestNormalize(unittest.TestCase):
    def test_deterministic_rules(self):
        self.assertEqual(normalize("＠写周报"), "@写周报")     # 全角 @ 一并归一
        self.assertEqual(normalize("写周报 "), "写周报")        # 去首尾空白
        self.assertEqual(normalize("寫周報"), "写周报")          # 繁→简固定映射
        self.assertEqual(normalize("Ｗｒｉｔｅ"), "Write")       # 全角→半角
        self.assertEqual(normalize("周 报"), "周 报")            # 中间空白不合并

    def test_normalized_replayable(self):
        self.assertEqual(normalize("寫周報"), normalize("寫周報"))


class TestParse(unittest.TestCase):
    def test_two_forms(self):
        self.assertEqual(parse("@写周报"),
                         {"kind": "skill", "name": "写周报", "pack_hint": None})
        self.assertEqual(parse("@hr/写周报"),
                         {"kind": "qualified", "name": "写周报", "pack_hint": "hr"})

    def test_prohibited_forms(self):
        for bad in ("@写周报 v2", "@写*周报", "@写周报  v2", "@@双写", "@写 周 报"):
            with self.assertRaises(RefSyntaxError):
                parse(bad)


class TestResolve(unittest.TestCase):
    def test_resolves_to_skill_with_positioning(self):
        out = resolve("@写周报", SKILLS)
        self.assertEqual(out["resolution"]["status"], "refused")   # 繁简两条同名 → 歧义
        self.assertEqual(out["resolution"]["error_code"], "REF_AMBIGUOUS")
        self.assertEqual(len(out["meta_summary"]["candidates"]), 2)
        for cand in out["meta_summary"]["candidates"]:
            self.assertIn("positioning", cand)                     # 候选带一句话定位

    def test_unique_name_resolves(self):
        out = resolve("@整理客户档案", SKILLS)
        self.assertEqual(out["resolution"]["status"], "resolved")
        self.assertEqual(out["skill"], "整理客户档案")
        self.assertEqual(out["meta_summary"]["positioning"], "客户档案整理（占位）")

    def test_qualified_hint_disambiguates(self):
        """显式限定 = 用户自己消歧（不算猜）。"""
        out = resolve("@hr/写周报", SKILLS)
        self.assertEqual(out["resolution"]["status"], "resolved")
        self.assertEqual(out["pack"], "hr")

    def test_not_found_with_available_list(self):
        out = resolve("@不存在的技能", SKILLS)
        self.assertEqual(out["resolution"]["error_code"], "REF_NOT_FOUND")
        self.assertTrue(out["meta_summary"]["available"])

    def test_binary_return(self):
        for raw in ("@写周报", "@整理客户档案", "@不存在"):
            out = resolve(raw, SKILLS)
            self.assertIn(out["resolution"]["status"], ("resolved", "refused"))


class TestChoiceAndAudit(unittest.TestCase):
    def test_human_choice_logged(self):
        audit = RefAudit()
        out = audit.resolve_logged("@写周报", SKILLS, at="2026-11-04T09:00:00Z")
        self.assertTrue(out["refused"])
        pick = audit.log_choice("@写周报", out["outcome"], "写周报",
                                at="2026-11-04T09:01:00Z")
        self.assertEqual(pick["resolution"]["skill"], "写周报")
        self.assertEqual(pick["resolution"]["resolution"]["strategy"], "user_choice")
        self.assertEqual(audit.records[-1]["chosen_from_candidates"], "写周报")

    def test_choice_outside_candidates_rejected(self):
        audit = RefAudit()
        out = audit.resolve_logged("@写周报", SKILLS, at="2026-11-04T09:00:00Z")
        with self.assertRaises(ValueError):
            audit.log_choice("@写周报", out["outcome"], "不在候选（占位）",
                             at="2026-11-04T09:01:00Z")

    def test_append_only_and_syntax_logged(self):
        audit = RefAudit()
        audit.resolve_logged("@写*报", SKILLS, at="2026-11-04T09:00:00Z")
        self.assertEqual(audit.records[0]["error_code"], "REF_SYNTAX_ERROR")
        before = list(audit.records)
        audit.resolve_logged("@写周报", SKILLS, at="2026-11-04T09:01:00Z")
        self.assertEqual(audit.records[:len(before)], before)


if __name__ == "__main__":
    unittest.main()
