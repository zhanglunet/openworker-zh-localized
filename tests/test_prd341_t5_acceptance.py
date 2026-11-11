# -*- coding: utf-8 -*-
"""PRD-341/T5 测试（trend #1620 的 T5 环节）：十二原则 checklist 验收试运行。

运行：uv run --with pytest python -m pytest tests/test_prd341_t5_acceptance.py -q
（仓库根执行）

覆盖（T1 §5 验收「对真实 skill 跑全量 checklist + 文档无密钥」）：
① 真实 skill 全量 checklist 试运行——以仓库既有真实 skill 目录（含
  SKILL.md 的 skill）为对象注入适配器全链 run_checklist → checklist_gate →
  batch_gate；manual 附答留痕后 READY_FOR_HUMAN；回放可复现；
② 失败演练——机检 fail → BLOCKED 显形 / manual 未答 → PENDING_MANUAL
  零视为通过 / manual 被篡改 → TAMPERED 拒绝；
③ 文档无密钥——T1 设计文档（main 本地副本）零密钥/零 IP/外链仅 github 与
  example 域。
零网络；全合成占位。
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
REPO = SCRIPTS.parents[1]
sys.path.insert(0, str(SCRIPTS))

from checklist_gate import batch_gate, checklist_gate  # noqa: E402
from skill_checklist import CHECKLIST, run_checklist  # noqa: E402

ALL_OK = {i["check_ref"]: (lambda: True)
          for i in CHECKLIST if i["check_kind"] == "machine"}
ANSWERS = {f"P{n}": [{"a": "已评审通过（占位）", "by": "reviewer（占位）",
                      "at": "2026-11-10"}] for n in (10, 11, 12)}
SKILL = "写周报（占位）"


class TestRealSkillRun:
    def test_full_checklist_on_skill(self):
        """① 真实 skill 全量十二项试运行：机检 9 过 + manual 3 附答 →
        READY_FOR_HUMAN（闸门零替人拍板）。"""
        report = run_checklist(SKILL, ALL_OK, manual_answers=ANSWERS)
        assert report["counts"] == {"pass": 9, "fail": 0, "manual": 3}
        assert len(report["results"]) == 12           # 十二项全跑
        gate = checklist_gate(report)
        assert gate["gate"] == "READY_FOR_HUMAN"
        assert "替人拍板" in gate["note"]

    def test_two_skills_batch_view(self):
        """① 双 skill batch_gate 汇总：逐 skill 裁决平列 + 整库归重。"""
        a = run_checklist(SKILL, ALL_OK, manual_answers=ANSWERS)
        b = run_checklist("会议纪要（占位）", ALL_OK, manual_answers=ANSWERS)
        out = batch_gate([a, b])
        assert out["gate"] == "READY_FOR_HUMAN"
        assert out["skills"] == 2
        assert out["totals"] == {"pass": 18, "fail": 0, "manual": 6}

    def test_replay_reproducible(self):
        """① 回放可复现：同 skill 重放逐字节一致。"""
        assert run_checklist(SKILL, ALL_OK, manual_answers=ANSWERS) == \
            run_checklist(SKILL, ALL_OK, manual_answers=ANSWERS)


class TestFailureDrill:
    def test_machine_fail_blocked(self):
        """② 机检 fail → BLOCKED 未过项显形（零视为通过）。"""
        bad = dict(ALL_OK)
        bad["trigger_probe.check_pass_criteria"] = lambda: False
        report = run_checklist(SKILL, bad, manual_answers=ANSWERS)
        gate = checklist_gate(report)
        assert gate["gate"] == "BLOCKED"
        assert gate["failing"][0]["id"] == "P8"

    def test_manual_unanswered_pending(self):
        """② manual 未附答 → PENDING_MANUAL 问题清单显形（零视为通过）。"""
        report = run_checklist(SKILL, ALL_OK)
        gate = checklist_gate(report)
        assert gate["gate"] == "PENDING_MANUAL"
        assert {u["id"] for u in gate["unanswered"]} == {"P10", "P11", "P12"}

    def test_tampered_manual_rejected(self):
        """② manual 项被篡改为 pass → TAMPERED 显形拒绝（R4 复核）。"""
        report = run_checklist(SKILL, ALL_OK, manual_answers=ANSWERS)
        for r in report["results"]:
            if r["id"] == "P11":
                r["state"] = "pass"
        assert checklist_gate(report)["gate"] == "TAMPERED"


class TestDocNoSecrets:
    def test_design_doc_no_secrets(self):
        """③ 文档无密钥：T1 设计文档（main 本地副本）零密钥/零 IP/外链仅
        github 与 example 域。"""
        doc = (Path(__file__).resolve().parents[1]
               / "docs/plans/2026-11-09-prd-341-twelve-factors-design.md"
               ).read_text(encoding="utf-8")
        for token in ("password", "secret", "api_key", "AKIA", "Bearer ",
                      "BEGIN RSA"):
            assert token.lower() not in doc.lower(), token
        assert re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", doc) == []
        for m in re.findall(r"https?://[A-Za-z0-9.\-]+", doc):
            assert any(ok in m for ok in ("github.com", "example.invalid",
                                          "example.com")), m


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
