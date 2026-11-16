# -*- coding: utf-8 -*-
"""PRD-452/T4 测试（trend #2158 的 T4 环节）：翻译监督台划界断言。
运行：uv run --with pytest python -m pytest tests/test_prd452_t4_translation_supervision_boundary.py -q
覆盖（T1 §3 边界）：人工拍板收件箱零触碰+checklist 引擎/失败验证/收件箱
本体零导入+借鉴词零出现+标准库-only+AST 零网络+R1 未点头不进收件箱+
闸门不信 status 位+留痕红线钉值。零网络；全合成占位。
"""
import ast
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from translation_supervision_bench import (  # noqa: E402
    TranslationSupervisionBench, TranslationSupervisionLedger)
from translation_supervision_gate import admit_via_gate  # noqa: E402

NOW = "2026-11-15T09:00:00Z"
MODULES = ["translation_supervision_bench.py",
           "translation_supervision_gate.py"]


def _imports_of(path: Path) -> set:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    return imported


def _code_names(path: Path) -> set:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


class TestBoundary(unittest.TestCase):
    def test_inbox_authority_untouched(self):
        """人工拍板收件箱零触碰：零收件箱写入/裁决函数定义（AST 扫描）。"""
        scripts = Path(__file__).resolve().parents[1] / "scripts"
        for mod in MODULES:
            tree = ast.parse((scripts / mod).read_text(encoding="utf-8"))
            funcs = {n.name.lower() for n in ast.walk(tree)
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            for banned in ("submit_to_inbox", "approve_inbox", "reject_inbox"):
                self.assertNotIn(banned, funcs, f"{mod} 定义 {banned}")

    def test_no_downstream_imports(self):
        """checklist 引擎（PRD-341）/失败验证（PRD-383）/收件箱（PRD-369）零导入。"""
        scripts = Path(__file__).resolve().parents[1] / "scripts"
        for mod in MODULES:
            imported = _imports_of(scripts / mod)
            for banned in ("checklist_failure_verify_bench",
                           "translation_supervision_bench"
                           if mod.endswith("gate.py") else
                           "translation_supervision_gate",
                           "checklist_inbox", "cn_skill_sync_check"):
                self.assertNotIn(banned, imported, f"{mod} 导入 {banned}")

    def test_borrowed_zero_symbols(self):
        """借鉴仓（plannotator/ag-ui，Apache-2.0/MIT 实测）零符号——只借形态。"""
        scripts = Path(__file__).resolve().parents[1] / "scripts"
        for mod in MODULES:
            names = {n.lower() for n in _code_names(scripts / mod)}
            for word in ("plannotator", "ag_ui"):
                self.assertNotIn(word, names, f"{mod} 出现 {word}")

    def test_stdlib_only_and_ast_redline(self):
        scripts = Path(__file__).resolve().parents[1] / "scripts"
        allowed = {"__future__", "copy", "json", "re", "pathlib", "typing"}
        for mod in MODULES:
            imported = _imports_of(scripts / mod)
            self.assertLessEqual(imported - allowed, set(), mod)
            self.assertFalse(imported & {"urllib", "requests", "socket",
                                         "http", "subprocess"}, mod)


class TestBehaviorPins(unittest.TestCase):
    def test_r1_unapproved_blocked(self):
        b = TranslationSupervisionBench(source_seq="S（占位）",
                                        translator="a（占位）", created_at=NOW,
                                        source_text="原文（占位）")
        b.submit_draft(version="v1", text="x（占位）")
        out = b.outlet()
        self.assertEqual(out["passed"], [])

    def test_gate_overrides_status_bit(self):
        b = TranslationSupervisionBench(source_seq="S（占位）",
                                        translator="a（占位）", created_at=NOW,
                                        source_text="原文（占位）")
        b.submit_draft(version="v1", text="x（占位）")
        b.status = "已点头"   # 手写 status 位
        out = admit_via_gate(b)
        self.assertEqual(out["passed"], [])

    def test_r3_ledger_surface_closed(self):
        led = TranslationSupervisionLedger(None)
        methods = {n for n in dir(led) if not n.startswith("_")}
        self.assertLessEqual(methods, {"record", "entries"}, methods)

    def test_attribution_required(self):
        b = TranslationSupervisionBench(source_seq="S（占位）",
                                        translator="a（占位）", created_at=NOW,
                                        source_text="原文（占位）")
        b.submit_draft(version="v1", text="x（占位）")
        from translation_supervision_bench import SupervisionError
        with self.assertRaisesRegex(SupervisionError, "SUPERVISION_INCOMPLETE"):
            b.annotate(author="", at=NOW, anchor="x（占位）", atype="通过",
                       text="t（占位）", version="v1")
        with self.assertRaisesRegex(SupervisionError, "SUPERVISION_INCOMPLETE"):
            b.approve(approver="乙（占位）", at="", version="v1")


if __name__ == "__main__":
    unittest.main()
