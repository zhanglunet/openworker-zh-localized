# -*- coding: utf-8 -*-
"""PRD-452/T3 测试（trend #2157 的 T3 环节）：翻译监督台闸门。
运行：uv run --with pytest python -m pytest tests/test_prd452_t3_translation_supervision_gate.py -q
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from translation_supervision_bench import (  # noqa: E402
    TranslationSupervisionBench)
from translation_supervision_gate import (  # noqa: E402
    GATE_REASONS, admit_via_gate, evaluate)

NOW = "2026-11-15T09:00:00Z"
T1 = "2026-11-15T10:00:00Z"


def ok_bench():
    b = TranslationSupervisionBench(source_seq="S-3（占位）",
                                    translator="agent-a（占位）",
                                    created_at=NOW, source_text="原文（占位）")
    b.submit_draft(version="v1", text="译稿 v1（占位）")
    b.annotate(author="甲（占位）", at=NOW, anchor="行2（占位）",
               atype="通过", text="ok（占位）", version="v1")
    b.resolve_annotation(seq=1, status="已采纳")
    b.approve(approver="乙（占位）", at=T1, version="v1")
    return b


class TestGate(unittest.TestCase):
    def test_clean_approve_allowed(self):
        out = admit_via_gate(ok_bench())
        self.assertEqual(out["passed"][0]["source_seq"], "S-3（占位）")
        self.assertEqual(out["passed"][0]["gate"], "GATE_ALLOWED")

    def test_no_decision(self):
        b = TranslationSupervisionBench(source_seq="S-3（占位）",
                                        translator="a（占位）", created_at=NOW,
                                        source_text="原文（占位）")
        b.submit_draft(version="v1", text="x（占位）")
        out = admit_via_gate(b)
        self.assertEqual(out["blocked"][0]["gate"], "GATE_NO_DECISION")

    def test_annotation_open(self):
        b = ok_bench()
        b.annotations[0]["status"] = "待处理"   # 手写回未处理
        out = admit_via_gate(b)
        self.assertEqual(out["blocked"][0]["gate"], "GATE_ANNOTATION_OPEN")

    def test_feedback_open(self):
        b = ok_bench()
        b.feedbacks.append({"status": "待处理"})
        out = admit_via_gate(b)
        self.assertEqual(out["blocked"][0]["gate"], "GATE_FEEDBACK_OPEN")

    def test_not_latest_version(self):
        b = ok_bench()
        b.versions.append({"version": "v2", "text": "x（占位）",
                           "term_choices": {}})
        out = admit_via_gate(b)
        self.assertEqual(out["blocked"][0]["gate"], "GATE_NOT_LATEST_VERSION")

    def test_gate_reasons_closed(self):
        self.assertEqual(len(GATE_REASONS), 5)


if __name__ == "__main__":
    unittest.main()
