# -*- coding: utf-8 -*-
"""PRD-341/T3 测试（trend #1620 的 T3 环节）：十二原则 checklist 通过闸门。

运行：uv run --with pytest python -m pytest tests/test_prd341_t3_gate.py -q
（仓库根执行）

覆盖（T1 §5/R4）：GATE_CODES 四码封闭；checklist_gate（机检 fail → BLOCKED
failing 显形/manual 未附答 → PENDING_MANUAL 问题清单显形零视为通过/机检全
过且附答齐 → READY_FOR_HUMAN 荐人工拍板闸门零替人拍板/manual 状态被篡改 →
TAMPERED R4 复核拒绝）；batch_gate 全库归重（任一 BLOCKED 整库不 READY）；
与 T2 串联（真实 run_checklist 产物直接过闸）。零网络；全合成占位。
"""
import ast
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from checklist_gate import batch_gate, checklist_gate  # noqa: E402
from skill_checklist import run_checklist  # noqa: E402

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
ALL_OK = {"zh_trigger_registry.build_registry": lambda: True,
          "zh_trigger_registry.check_conflicts": lambda: None,
          "zh_sources.validate_source": lambda: True,
          "consistency_check.check_consistency": lambda: True,
          "zh_skill_ref.resolve": lambda: True,
          "skillpack_snapshot.restore": lambda: True,
          "cn_skill_sync_check.run_check": lambda: True,
          "trigger_probe.check_pass_criteria": lambda: True,
          "zh_intake_gate.intake": lambda: True}
ANSWERS = {f"P{n}": [{"a": "已评审（占位）", "by": "reviewer（占位）"}]
           for n in (10, 11, 12)}


class TestCodes:
    def test_four_codes_closed(self):
        from checklist_gate import GATE_CODES
        assert set(GATE_CODES) == {"READY_FOR_HUMAN", "PENDING_MANUAL",
                                   "BLOCKED", "TAMPERED"}


class TestChecklistGate:
    def test_blocked_when_machine_fail(self):
        bad = dict(ALL_OK)
        bad["trigger_probe.check_pass_criteria"] = lambda: False
        report = run_checklist("写周报（占位）", bad)
        out = checklist_gate(report)
        assert out["gate"] == "BLOCKED"
        assert out["failing"][0]["id"] == "P8"
        assert "未过" in out["failing"][0]["reason"]

    def test_pending_manual_zero_auto_pass(self):
        """R4：机检全过但 manual 未附答 → PENDING_MANUAL（零视为通过）。"""
        report = run_checklist("写周报（占位）", ALL_OK)
        out = checklist_gate(report)
        assert out["gate"] == "PENDING_MANUAL"
        assert {u["id"] for u in out["unanswered"]} == {"P10", "P11", "P12"}
        assert all(u["questions"] for u in out["unanswered"])

    def test_ready_for_human_with_answers(self):
        report = run_checklist("写周报（占位）", ALL_OK, manual_answers=ANSWERS)
        out = checklist_gate(report)
        assert out["gate"] == "READY_FOR_HUMAN"
        assert "替人拍板" in out["note"]

    def test_tampered_manual_rejected(self):
        """R4 复核：manual 项状态被改为 pass/fail → TAMPERED 显形拒绝。"""
        report = run_checklist("写周报（占位）", ALL_OK, manual_answers=ANSWERS)
        for r in report["results"]:
            if r["id"] == "P10":
                r["state"] = "pass"       # 篡改
        out = checklist_gate(report)
        assert out["gate"] == "TAMPERED"
        assert out["tampered"] == [{"id": "P10", "state": "pass"}]

    def test_unregistered_checker_blocks(self):
        report = run_checklist("写周报（占位）", {})
        assert checklist_gate(report)["gate"] == "BLOCKED"


class TestBatchGate:
    def test_batch_worst_wins(self):
        """全库归重：任一 skill BLOCKED → 整库不 READY。"""
        good = run_checklist("写周报（占位）", ALL_OK, manual_answers=ANSWERS)
        bad = dict(ALL_OK)
        bad["zh_intake_gate.intake"] = lambda: False
        bad_report = run_checklist("会议纪要（占位）", bad, manual_answers=ANSWERS)
        out = batch_gate([good, bad_report])
        assert out["gate"] == "BLOCKED"
        assert out["skills"] == 2
        assert {v["gate"] for v in out["verdicts"]} == {"READY_FOR_HUMAN",
                                                        "BLOCKED"}

    def test_batch_all_ready(self):
        a = run_checklist("写周报（占位）", ALL_OK, manual_answers=ANSWERS)
        b = run_checklist("会议纪要（占位）", ALL_OK, manual_answers=ANSWERS)
        out = batch_gate([a, b])
        assert out["gate"] == "READY_FOR_HUMAN"
        assert out["totals"]["manual"] == 6   # 2 skill × 3 manual 项


class TestChainAndRedline:
    def test_chain_with_t2_products(self):
        """与 T2 串联：真实 run_checklist 三种产物逐一过闸。"""
        reports = [run_checklist("写周报（占位）", ALL_OK),
                   run_checklist("写周报（占位）", ALL_OK, manual_answers=ANSWERS),
                   run_checklist("会议纪要（占位）", {})]
        gates = [checklist_gate(r)["gate"] for r in reports]
        assert gates == ["PENDING_MANUAL", "READY_FOR_HUMAN", "BLOCKED"]

    def test_gate_module_readonly_zero_network(self):
        banned = {"urllib", "requests", "socket", "http", "subprocess"}
        tree = ast.parse((SCRIPTS / "checklist_gate.py").read_text(
            encoding="utf-8"))
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module.split(".")[0]]
            for mod in mods:
                assert mod not in banned
                assert mod not in {"zh_trigger_registry", "zh_sources",
                                   "consistency_check", "zh_skill_ref",
                                   "skillpack_snapshot", "cn_skill_sync_check",
                                   "trigger_probe", "zh_intake_gate"}


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
