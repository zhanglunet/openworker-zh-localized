# -*- coding: utf-8 -*-
"""PRD-341/T2 测试（trend #1620 的 T2 环节）：十二原则 checklist 引擎。

运行：uv run --with pytest python -m pytest tests/test_prd341_t2_checklist.py -q
（仓库根执行）

覆盖（T1 §3/§4/§6 + R1/R2/R3/R4）：数据形态封闭（P1–P12 完整、check_kind
∈{machine,manual}）/check_ref 全部指向 scripts/ 既有模块（R1 零发明机检器）/
honest 三态映射（None=clean、真值 pass、假值 fail 带 reason、异常 fail 显形、
未注册 fail 显形——零视为通过 R4）/manual 只留痕不改状态 + JSON 附答显形
拒绝非法指向（§6.2）/每 skill 一份 + 全库汇总视图（§6.1）/引擎零硬编码
（R3：run_checklist 源码零原则 id 零机检器名）/模块零网络零仓库内部依赖
（R2 零复用预埋）。零网络；全合成占位。
"""
import ast
import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from skill_checklist import (  # noqa: E402
    CHECKLIST,
    MANUAL_IDS,
    run_checklist,
    summarize,
)

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
ALL_OK = {i["check_ref"]: (lambda: True)
          for i in CHECKLIST if i["check_kind"] == "machine"}


class TestDataShape:
    def test_twelve_items_complete(self):
        assert [i["id"] for i in CHECKLIST] == [f"P{n}" for n in range(1, 13)]
        assert len(MANUAL_IDS) == 3
        assert MANUAL_IDS == {"P10", "P11", "P12"}

    def test_check_kind_closed_vocabulary(self):
        for item in CHECKLIST:
            assert item["check_kind"] in {"machine", "manual"}
            if item["check_kind"] == "machine":
                assert item.get("check_ref"), item["id"]
            else:
                assert item.get("manual_questions"), item["id"]

    def test_check_ref_points_at_existing_modules(self):
        """R1：check_ref 全部是 `<scripts/ 既有模块>.<函数>` 形态——零发明。"""
        for item in CHECKLIST:
            if item["check_kind"] != "machine":
                continue
            module_name = item["check_ref"].split(".")[0]
            assert (SCRIPTS / f"{module_name}.py").exists(), item["check_ref"]


class TestHonestTriState:
    def test_all_pass_adapters(self):
        report = run_checklist("写周报（占位）", ALL_OK)
        assert report["counts"] == {"pass": 9, "fail": 0, "manual": 3}
        assert report["all_machine_pass"] is True

    def test_failing_adapter_fail_with_reason(self):
        checkers = dict(ALL_OK)
        checkers["trigger_probe.check_pass_criteria"] = lambda: False
        report = run_checklist("写周报（占位）", checkers)
        fail = next(r for r in report["results"] if r["state"] == "fail")
        assert fail["id"] == "P8"
        assert "未过" in fail["reason"]

    def test_raising_adapter_fail_visible(self):
        """R4：机检器异常如实 fail 显形，零伪装。"""
        def boom():
            raise RuntimeError("探针环境不可用（占位）")
        checkers = dict(ALL_OK)
        checkers["zh_sources.validate_source"] = boom
        report = run_checklist("写周报（占位）", checkers)
        fail = next(r for r in report["results"] if r["id"] == "P3")
        assert fail["state"] == "fail"
        assert "异常" in fail["reason"] and "占位" in fail["reason"]

    def test_unregistered_check_ref_fail_not_pass(self):
        """R4：check_ref 未注册 → fail 显形（零视为通过路径）。"""
        report = run_checklist("写周报（占位）", {})
        assert sum(1 for r in report["results"] if r["state"] == "fail") == 9
        assert report["all_machine_pass"] is False
        assert "未注册" in next(
            r for r in report["results"] if r["id"] == "P1")["reason"]

    def test_none_return_is_clean_pass(self):
        """适配器契约：None = clean（check_conflicts 无冲突即 None 返回）。"""
        checkers = dict(ALL_OK)
        checkers["zh_trigger_registry.check_conflicts"] = lambda: None
        report = run_checklist("写周报（占位）", checkers)
        assert next(r for r in report["results"]
                    if r["id"] == "P2")["state"] == "pass"

    def test_result_shape_closed(self):
        report = run_checklist("写周报（占位）", {})
        for r in report["results"]:
            assert r["state"] in {"pass", "fail", "manual"}
            if r["state"] == "fail":
                assert r["reason"]
            if r["state"] == "manual":
                assert r["questions"]


class TestManualTrace:
    def test_manual_never_auto_pass_and_carries_questions(self):
        report = run_checklist("写周报（占位）", ALL_OK)
        for r in report["results"]:
            if r["id"] in MANUAL_IDS:
                assert r["state"] == "manual"          # 引擎零视为通过
                assert r["questions"]

    def test_json_answers_attach_without_state_change(self):
        """§6.2 裁决：JSON 附答只留痕，状态保持 manual。"""
        answers = {"P10": [{"q": "何时用？", "a": "能说清（占位）",
                            "by": "reviewer（占位）", "at": "2026-11-10"}]}
        report = run_checklist("写周报（占位）", ALL_OK, manual_answers=answers)
        p10 = next(r for r in report["results"] if r["id"] == "P10")
        assert p10["state"] == "manual"
        assert p10["answers"][0]["a"] == "能说清（占位）"

    def test_answers_to_unknown_or_machine_id_rejected(self):
        with pytest.raises(ValueError):
            run_checklist("写周报（占位）", ALL_OK,
                          manual_answers={"P99": "不存在"})
        with pytest.raises(ValueError):
            run_checklist("写周报（占位）", ALL_OK,
                          manual_answers={"P1": "机检项不接受附答"})


class TestGranularitySummary:
    def test_per_skill_reports_independent(self):
        """§6.1 裁决：每 skill 一份报告，互不串味。"""
        ok = run_checklist("写周报（占位）", ALL_OK)
        bad = dict(ALL_OK)
        bad["zh_intake_gate.intake"] = lambda: False
        bad_report = run_checklist("会议纪要（占位）", bad)
        assert ok["counts"]["fail"] == 0
        assert bad_report["counts"]["fail"] == 1
        assert ok["skill"] != bad_report["skill"]

    def test_summary_view_aggregates_failing(self):
        good = run_checklist("写周报（占位）", ALL_OK)
        bad = dict(ALL_OK)
        bad["trigger_probe.check_pass_criteria"] = lambda: False
        bad_report = run_checklist("会议纪要（占位）", bad)
        summary = summarize([good, bad_report])
        assert summary["schema"] == "skill-checklist-summary/v1"
        assert summary["skills"] == 2
        assert summary["totals"]["fail"] == 1
        assert summary["all_machine_pass"] is False
        assert summary["failing"] == [{"skill": "会议纪要（占位）", "id": "P8",
                                       "reason": bad_report["results"][7]["reason"]}]


class TestRedlines:
    def test_engine_zero_hardcode(self):
        """R3：引擎零 checklist 硬编码——run_checklist 源码零原则 id、
        零机检器名（数据与逻辑分离）。"""
        src = inspect.getsource(run_checklist)
        for n in range(1, 13):
            assert f'"P{n}"' not in src and f"'P{n}'" not in src
        for item in CHECKLIST:
            if item["check_kind"] == "machine":
                assert item["check_ref"] not in src

    def test_module_zero_network_zero_internal_imports(self):
        """R2 预埋：模块只 import stdlib（__future__/typing）——零网络、
        零仓库内部复用、零借鉴仓符号。"""
        tree = ast.parse((SCRIPTS / "skill_checklist.py").read_text(
            encoding="utf-8"))
        allowed = {"__future__", "typing"}
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module.split(".")[0]]
            for mod in mods:
                assert mod in allowed, f"skill_checklist.py 导入了 {mod}"


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
