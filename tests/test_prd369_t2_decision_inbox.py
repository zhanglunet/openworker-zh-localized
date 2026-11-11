# -*- coding: utf-8 -*-
"""PRD-369/T2 测试（trend #1648 的 T2 环节）：人工拍板收件箱。

运行：uv run --with pytest python -m pytest tests/test_prd369_t2_decision_inbox.py -q
（仓库根执行）

覆盖（T1 §3.1/§3.2/§4 + R1–R4）：collect 三源只读汇聚（词表封闭+五件套缺一
INBOX_ITEM_INCOMPLETE 显形拒绝入箱+manual 项 questions 引用 PRD-341 附答留
痕 answers_ref）；InboxLedger 状态机（approve/reject 人批留痕/重复裁决/未知
id/AUTO_EXEC 携带 checklist 写/注册表写/附答代填载荷拒绝——零 checklist 状态
改写 R1 TAMPERED 红线继续/歧义项 approve 必带选中候选且候选须在列表内
CHOICE_REQUIRED）；append-only；view kind 过滤；与 PRD-341 run_checklist
串联（P10–P12 manual 项直接入箱）；AST 零网络零子进程。零网络；全合成占位。
"""
import ast
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from decision_inbox import (  # noqa: E402
    ERROR_CODES,
    ITEM_KINDS,
    InboxError,
    InboxLedger,
    collect,
)
from skill_checklist import run_checklist  # noqa: E402

NOW = "2026-11-11T09:00:00Z"
FP = "sha16:checklist（占位）"
QUESTIONS = ["给三个新用户读 description，能否不动手册说清何时用？（占位）"]
MANUAL = [{"source_ref": "skill-checklist-report/v1#P10（占位）",
           "fingerprint": FP, "questions": QUESTIONS,
           "reason": "P10 人工评审项（占位）"}]
ANSWERS = [{"source_ref": "manual-answers（占位）", "fingerprint": FP,
            "answers_ref": "manual_answers.json（占位）",
            "reason": "附答后确认（占位）"}]
DISAMb = [{"source_ref": "ref-resolution/v1（占位）", "fingerprint": FP,
           "candidates": ["技能包A（占位）", "技能包B（占位）"],
           "reason": "歧义候选（占位）"}]
ALL_OK = {i["check_ref"]: (lambda: True)
          for i in __import__("skill_checklist").CHECKLIST
          if i["check_kind"] == "machine"}
ANSWERS_MAP = {f"P{n}": [{"a": "已评审（占位）", "by": "r（占位）"}]
               for n in (10, 11, 12)}


class TestCollect:
    def test_three_sources_closed_vocab(self):
        items = collect(manual_reviews=MANUAL, answer_confirms=ANSWERS,
                        zh_disambiguations=DISAMb, fingerprint=FP, at=NOW)
        assert [it["kind"] for it in items] == ["manual_review",
                                                "answer_confirm",
                                                "zh_disambiguation"]
        assert set(ITEM_KINDS) == {"manual_review", "answer_confirm",
                                   "zh_disambiguation"}

    def test_manual_questions_and_answers_ref(self):
        """R3：manual 项 questions 引用 PRD-341 问题清单；附答 answers_ref
        引用留痕。"""
        items = collect(manual_reviews=MANUAL, answer_confirms=ANSWERS,
                        at=NOW)
        assert items[0]["questions"] == QUESTIONS
        assert items[1]["answers_ref"] == "manual_answers.json（占位）"

    def test_incomplete_branch_defensive(self):
        """R3：INBOX_ITEM_INCOMPLETE 为防御分支——公开 API 三源均带默认文案，
        kind 由分支钉死；防御路径经 monkeypatch 词表触发。"""
        import decision_inbox
        orig = decision_inbox.ITEM_KINDS
        decision_inbox.ITEM_KINDS = ("not_a_kind（占位）",)   # 临时收窄词表
        try:
            with pytest.raises(InboxError, match="INBOX_ITEM_INCOMPLETE"):
                collect(manual_reviews=MANUAL, fingerprint=FP, at=NOW)
        finally:
            decision_inbox.ITEM_KINDS = orig

    def test_chain_with_341_checklist(self):
        """与 PRD-341 串联：run_checklist P10–P12 manual 项直接入箱。"""
        report = run_checklist("写周报（占位）", ALL_OK)
        manuals = [{"source_ref": f"skill-checklist-report/v1#{r['id']}",
                    "fingerprint": FP, "questions": r["questions"],
                    "reason": f"{r['id']} 人工评审项（占位）"}
                   for r in report["results"] if r["state"] == "manual"]
        items = collect(manual_reviews=manuals, fingerprint=FP, at=NOW)
        assert len(items) == 3
        assert {it["source_ref"].split("#")[1] for it in items} == \
            {"P10", "P11", "P12"}


class TestLedger:
    def _ledger(self):
        led = InboxLedger()
        led.add(collect(manual_reviews=MANUAL, answer_confirms=ANSWERS,
                        zh_disambiguations=DISAMb, fingerprint=FP, at=NOW))
        return led

    def test_approve_reject_state_machine(self):
        led = self._ledger()
        a = led.approve("item-001", by="owner（占位）", at=NOW)
        assert a["state"] == "approved"
        c = led.approve("item-003", by="owner（占位）", at=NOW,
                        choice="技能包A（占位）")
        assert c["chosen_candidate"] == "技能包A（占位）"
        r = led.reject("item-002", by="owner（占位）", at=NOW,
                       reason="补答再确认（占位）")
        assert r["state"] == "rejected"

    def test_choice_required_and_validated(self):
        led = self._ledger()
        with pytest.raises(InboxError, match="INBOX_CHOICE_REQUIRED"):
            led.approve("item-003", by="o（占位）", at=NOW)
        with pytest.raises(InboxError, match="INBOX_CHOICE_REQUIRED"):
            led.approve("item-003", by="o（占位）", at=NOW,
                        choice="不在列表（占位）")
        a = led.approve("item-003", by="o（占位）", at=NOW,
                        choice="技能包B（占位）")
        assert a["chosen_candidate"] == "技能包B（占位）"

    def test_double_and_unknown_visible(self):
        led = self._ledger()
        led.approve("item-001", by="o（占位）", at=NOW)
        with pytest.raises(InboxError, match="INBOX_DOUBLE_DECIDE"):
            led.reject("item-001", by="o（占位）", at=NOW)
        with pytest.raises(InboxError, match="未知"):
            led.approve("item-999", by="o（占位）", at=NOW)

    def test_auto_exec_write_payloads_rejected(self):
        """R1：checklist 写/注册表写/附答代填载荷 → AUTO_EXEC 显形拒绝。"""
        led = self._ledger()
        with pytest.raises(InboxError, match="INBOX_AUTO_EXEC_ATTEMPT"):
            led.approve("item-001", by="o（占位）", at=NOW,
                        payload={"write_checklist": "P10 pass（占位）"})
        with pytest.raises(InboxError, match="INBOX_AUTO_EXEC_ATTEMPT"):
            led.reject("item-003", by="o（占位）", at=NOW,
                       payload={"write_registry": "新包（占位）"})
        with pytest.raises(InboxError, match="INBOX_AUTO_EXEC_ATTEMPT"):
            led.reject("item-002", by="o（占位）", at=NOW,
                       payload={"fill_answers": {"P10": "代填（占位）"}})
        assert led.view()[0]["state"] == "pending"   # 零状态变化

    def test_append_only_and_view_filter(self):
        led = self._ledger()
        led.approve("item-001", by="o（占位）", at=NOW)
        before = [dict(e) for e in led.events]
        led.reject("item-002", by="o（占位）", at=NOW, reason="r（占位）")
        assert led.events[:len(before)] == before
        assert len(led.events) == len(before) + 1
        assert len(led.view("zh_disambiguation")) == 1
        assert len(led.view()) == 3


class TestRedline:
    def test_error_codes_closed(self):
        assert set(ERROR_CODES) == {"INBOX_ITEM_INCOMPLETE",
                                    "INBOX_DOUBLE_DECIDE",
                                    "INBOX_AUTO_EXEC_ATTEMPT",
                                    "INBOX_CHOICE_REQUIRED"}

    def test_ast_zero_network_zero_subprocess(self):
        banned = {"urllib", "requests", "socket", "http", "subprocess"}
        src = (REPO / "scripts" / "decision_inbox.py").read_text(
            encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module.split(".")[0]]
            for mod in mods:
                assert mod not in banned


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
