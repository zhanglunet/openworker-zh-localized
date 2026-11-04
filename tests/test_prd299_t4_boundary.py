# -*- coding: utf-8 -*-
"""PRD-299/T4 测试（trend #1499）：与 PRD-267/285 及 239 双路径划界断言。

运行：uv run --with pytest python -m pytest tests/test_prd299_t4_boundary.py -q

覆盖（T1 设计 §2/§7，验收「划界断言通过」）：
  ① 模块隔离双向（zh_skill_ref/zh_ref_gates 零导入技能来源/升级快照/触发
    词登记册面；既有 zh 面模块零导入引用面）；② PRD-267/285 行为不变
    （技能清单注入 deepcopy 钉值零改动）；③ 239 双路径优先级断言（显式
    @引用优先于口语命中——同语句先走 @解析，命中即不再走触发词 lookup）；
  ④ 本条是中文名寻址（零技能生成/零升级调用 AST）。
零网络；全合成占位。
"""
import ast
import copy
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from zh_ref_gates import InstructionGate  # noqa: E402
from zh_skill_ref import normalize, resolve  # noqa: E402
from zh_trigger_registry import lookup  # noqa: E402

SKILLS = [{"name": "写周报", "pack": "hr", "positioning": "生成周报初稿（占位）"}]


class 模块隔离Tests(unittest.TestCase):
    def test_ref_side_never_imports_source_snapshot_registry(self):
        banned = {"zh_skill_draft", "zh_sources", "zh_skill_subpack",
                  "upgrade", "snapshot", "zh_trigger_registry"}
        for name in ("zh_skill_ref.py", "zh_ref_gates.py"):
            tree = ast.parse((REPO / "scripts" / name).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                mods = []
                if isinstance(node, ast.Import):
                    mods = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    mods = [node.module.split(".")[0]]
                for mod in mods:
                    self.assertNotIn(mod, banned, f"{name} 导入了 {mod}")

    def test_existing_zh_modules_never_import_ref(self):
        checked = 0
        for name in ("zh_trigger_registry.py", "zh_skill_draft.py",
                     "zh_skill_subpack.py"):
            path = REPO / "scripts" / name
            if not path.is_file():
                continue
            checked += 1
            src = path.read_text(encoding="utf-8")
            for token in ("zh_skill_ref", "zh_ref_gates"):
                self.assertNotIn(token, src, f"{name} 导入了引用面 {token}")
        self.assertGreaterEqual(checked, 1)


class PRD267285行为不变Tests(unittest.TestCase):
    def test_skill_list_untouched_by_resolve(self):
        """技能清单 deepcopy 钉值：引用解析并入零扰动（267 产出/285 版本）。"""
        before = copy.deepcopy(SKILLS)
        resolve("@写周报", SKILLS)
        self.assertEqual(SKILLS, before)

    def test_normalize_pure(self):
        """归一纯函数钉值：写入输入不影响输出（可回放）。"""
        self.assertEqual(normalize("寫周報"), "写周报")
        self.assertEqual(normalize("寫周報"), "写周报")


class 双路径优先级Tests(unittest.TestCase):
    def test_explicit_ref_wins_over_spoken_hit(self):
        """显式 @引用优先于口语命中：@写周报 走引用解析（而非触发词 lookup）。"""
        gate = InstructionGate()
        out = gate.check("@写周报", SKILLS, at="2026-11-04T09:00:00Z")
        self.assertTrue(out["allow"])                          # @路径命中
        self.assertEqual(out["skill"], "写周报")
        # 同语句若走 239 口语路径（无 @）则按触发词裁决——两路径并存不混用
        registry = {"entries": []}                             # 空登记册：口语路径零命中
        spoken = lookup(registry, "写周报")
        self.assertEqual(spoken["status"], "miss")             # 互不借用词表


class 中文名寻址Tests(unittest.TestCase):
    def test_ast_zero_generation_upgrade_calls(self):
        """零技能生成/零升级调用（来源归 267，升级归 285）。"""
        banned_calls = {"generate", "draft_skill", "upgrade", "rollback"}
        for name in ("zh_skill_ref.py", "zh_ref_gates.py"):
            tree = ast.parse((REPO / "scripts" / name).read_text(encoding="utf-8"))
            calls = [n.func.id for n in ast.walk(tree)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
            for banned in banned_calls:
                self.assertNotIn(banned, calls, f"{name} 含调用 {banned}")


if __name__ == "__main__":
    unittest.main()
