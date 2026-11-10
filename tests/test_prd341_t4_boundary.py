# -*- coding: utf-8 -*-
"""PRD-341/T4 测试（trend #1620 的 T4 环节）：十二原则 checklist 划界断言。

运行：uv run --with pytest python -m pytest tests/test_prd341_t4_boundary.py -q
（仓库根执行）

覆盖（T1 §5/R2/R3 + §2 划界）：R3 数据驱动断言（引擎源码零原则 id 零机检
器名复钉 + 数据驱动单向——gate 引 MANUAL_IDS 来自数据模块 + 增补原则演练：
运行时向 CHECKLIST 追加 P13 后 run_checklist 即覆盖新条目零改引擎代码）；
R2 零复用抽样断言（十二条 principle 全中文原创表述含 CJK 零英文 factor 术
语符号；两模块零借鉴仓符号 humanlayer/12-factor）；R1 复钉（check_ref 全部
指向 scripts/ 既有模块文件）；与 PRD-199/227/303 划界（checklist 零重复实现
机检判定——引擎零判定逻辑只有 honest 映射 AST 粗断言零 if-ok-then-pass 之
外判定符号）。零网络；全合成占位。
"""
import ast
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import skill_checklist  # noqa: E402
from skill_checklist import CHECKLIST, MANUAL_IDS, run_checklist  # noqa: E402

ALL_OK = {i["check_ref"]: (lambda: True)
          for i in CHECKLIST if i["check_kind"] == "machine"}


class TestR3DataDriven:
    def test_engine_zero_hardcode_recheck(self):
        """R3 复钉：run_checklist/checklist_gate 源码零原则 id 零机检器名。"""
        import inspect
        from checklist_gate import checklist_gate
        for fn in (run_checklist, checklist_gate):
            src = inspect.getsource(fn)
            for n in range(1, 13):
                assert f'"P{n}"' not in src and f"'P{n}'" not in src
            for item in CHECKLIST:
                if item["check_kind"] == "machine":
                    assert item["check_ref"] not in src

    def test_gate_imports_vocab_from_data_module(self):
        """数据驱动单向：闸门的 manual 词表来自数据模块（is 断言）。"""
        from checklist_gate import MANUAL_IDS as GATE_IDS
        assert GATE_IDS is MANUAL_IDS

    def test_adding_principle_needs_data_only(self):
        """R3 演练：运行时追加 P13 → run_checklist 即覆盖，零改引擎。"""
        extra = {"id": "P13", "principle": "演练新增（占位）",
                 "check_kind": "machine", "check_ref": "演练机检器（占位）"}
        CHECKLIST.append(extra)
        try:
            report = run_checklist("写周报（占位）",
                                   dict(ALL_OK, **{"演练机检器（占位）": lambda: True}))
            ids = [r["id"] for r in report["results"]]
            assert "P13" in ids                       # 新原则被数据驱动覆盖
            assert report["counts"]["pass"] == 10     # 9 机检 + 演练 1
        finally:
            CHECKLIST.remove(extra)                   # 还原数据（演练零残留）


class TestR2ZeroReuse:
    def test_principles_original_chinese(self):
        """R2 抽样断言：十二条 principle 全中文原创表述（含 CJK，零英文
        factor 术语）。"""
        for item in CHECKLIST:
            text = item["principle"]
            assert any("\u4e00" <= ch <= "\u9fff" for ch in text), item["id"]
            assert "factor" not in text.lower()
            assert "humanlayer" not in text.lower()

    def test_modules_zero_borrowed_symbols(self):
        """R2 AST：两模块零借鉴仓符号（humanlayer/12-factor/swe-agent）。"""
        for name in ("skill_checklist.py", "checklist_gate.py"):
            src = (SCRIPTS / name).read_text(encoding="utf-8").lower()
            for token in ("humanlayer", "12-factor", "12factor", "swe-agent"):
                assert token not in src, f"{name} 出现借鉴仓符号 {token}"


class TestR1AndBoundary:
    def test_check_ref_points_at_existing_modules(self):
        """R1 复钉：check_ref 全部是 scripts/ 既有模块。"""
        for item in CHECKLIST:
            if item["check_kind"] == "machine":
                module = item["check_ref"].split(".")[0]
                assert (SCRIPTS / f"{module}.py").exists(), item["check_ref"]

    def test_gate_module_one_way_consumption(self):
        """划界：checklist_gate 只读消费 checklist 产物（零 import
        skill_checklist 之外的机检器模块）。"""
        tree = ast.parse((SCRIPTS / "checklist_gate.py").read_text(
            encoding="utf-8"))
        banned = {"urllib", "requests", "socket", "http", "subprocess",
                  "zh_trigger_registry", "zh_sources", "consistency_check",
                  "zh_skill_ref", "skillpack_snapshot", "cn_skill_sync_check",
                  "trigger_probe", "zh_intake_gate"}
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module.split(".")[0]]
            for mod in mods:
                assert mod not in banned, f"checklist_gate 导入了 {mod}"


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
