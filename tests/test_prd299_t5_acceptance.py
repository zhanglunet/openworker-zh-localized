# -*- coding: utf-8 -*-
"""PRD-299/T5 测试（trend #1500）：验收试运行——样例全流程回放 + 歧义/失败
演练 + 文档无密钥。

运行：uv run --with pytest python -m pytest tests/test_prd299_t5_acceptance.py -q

验收标准（trend #1500）：**引用解析全链通过；红线断言全过；文档无密钥**。

回放：中文指令含 @写周报（歧义两条同名）→ InstructionGate 列候选 → 用户
人工消歧 chosen 留痕 → @整理客户档案 唯一命中直接 resolved → 歧义/失败
演练（NOT_FOUND/AMBIGUOUS/SYNTAX 全触发）→ 文档无密钥。
零网络；全合成占位。
"""
import ast
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from zh_ref_gates import InstructionGate  # noqa: E402
from zh_skill_ref import ERROR_CODES, resolve  # noqa: E402

SKILLS = [
    {"name": "写周报", "pack": "hr", "positioning": "生成周报初稿（占位）"},
    {"name": "寫周報", "pack": "sales", "positioning": "销售侧周报（占位）"},
    {"name": "整理客户档案", "pack": "sales", "positioning": "客户档案整理（占位）"},
]
INSTRUCTION_REFS = ["@写周报", "@整理客户档案"]


class 全链回放Tests(unittest.TestCase):
    def test_full_chain_replay_with_human_disambiguation(self):
        """样例全流程：歧义列候选 → 人工消歧 chosen 留痕 → 唯一名直接命中。"""
        gate = InstructionGate()
        ambiguous = gate.check("@写周报", SKILLS, at="2026-11-04T09:00:00Z")
        self.assertFalse(ambiguous["allow"])
        self.assertEqual(len(ambiguous["candidates"]), 2)
        from zh_skill_ref import resolve
        outcome = resolve("@写周报", SKILLS)
        pick = gate.choose("@写周报", outcome, "寫周報", at="2026-11-04T09:01:00Z")
        self.assertEqual(pick["chosen_from_candidates"], "寫周報")
        unique = gate.check("@整理客户档案", SKILLS, at="2026-11-04T09:02:00Z")
        self.assertTrue(unique["allow"])
        # 审计：refused+chosen+resolved 全留痕
        self.assertEqual([r["status"] for r in gate.audit.records if "status" in r],
                         ["refused", "resolved", "resolved"])
        self.assertEqual(gate.audit.records[-2].get("chosen_from_candidates"),
                         "寫周報")

    def test_replay_deterministic(self):
        def run():
            gate = InstructionGate()
            gate.check("@写周报", SKILLS, at="2026-11-04T09:00:00Z")
            gate.check("@整理客户档案", SKILLS, at="2026-11-04T09:01:00Z")
            return str(gate.audit.records)
        self.assertEqual(run(), run())


class 歧义失败演练Tests(unittest.TestCase):
    def test_all_failures_block(self):
        """三码全触发（NOT_FOUND/AMBIGUOUS/SYNTAX_ERROR）。"""
        gate = InstructionGate()
        for raw, want in (("@不存在的技能", "REF_NOT_FOUND"),
                          ("@写周报", "REF_AMBIGUOUS"),
                          ("@写*报", "REF_SYNTAX_ERROR")):
            out = gate.check(raw, SKILLS, at="2026-11-04T09:00:00Z")
            self.assertFalse(out["allow"], raw)
            self.assertEqual(out["error_code"], want, raw)


class 红线终检Tests(unittest.TestCase):
    def test_three_codes_closed(self):
        self.assertEqual(sorted(ERROR_CODES),
                         ["REF_AMBIGUOUS", "REF_NOT_FOUND", "REF_SYNTAX_ERROR"])

    def test_ast_zero_generation_upgrade(self):
        banned = {"zh_skill_draft", "zh_sources", "zh_skill_subpack"}
        for name in ("zh_skill_ref.py", "zh_ref_gates.py"):
            tree = ast.parse((REPO / "scripts" / name).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                mods = []
                if isinstance(node, ast.Import):
                    mods = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    mods = [node.module.split(".")[0]]
                for mod in mods:
                    self.assertNotIn(mod, banned)


class 文档无密钥Tests(unittest.TestCase):
    def test_design_doc_no_secrets(self):
        secret_re = re.compile(r"(sk-[A-Za-z0-9]{8,}|ghp_[A-Za-z0-9]{8,}|"
                               r"AKIA[0-9A-Z]{16}|password\s*[:=]\s*['\"][^'\"]{4,})",
                               re.IGNORECASE)
        docs = list((REPO / "docs" / "plans").glob("2026-11-04-prd-299-*.md"))
        self.assertTrue(docs, "T1 设计文档在位")
        for doc in docs:
            blob = doc.read_text(encoding="utf-8")
            self.assertFalse(secret_re.findall(blob), doc.name)
            for host in re.findall(r"https?://([a-z0-9.-]+)", blob, re.IGNORECASE):
                self.assertTrue(host.endswith(("github.com", "example.com",
                                               "example.invalid", "synthetic",
                                               "local")), f"{doc.name} {host}")


if __name__ == "__main__":
    unittest.main()
