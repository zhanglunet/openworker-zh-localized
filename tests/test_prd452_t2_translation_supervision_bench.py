# -*- coding: utf-8 -*-
"""PRD-452/T2 测试（trend #2156 的 T2 环节）：翻译监督台。
运行：uv run --with pytest python -m pytest tests/test_prd452_t2_translation_supervision_bench.py -q
覆盖（T1 §3/§4/§5）：版本链/批注打包发回/回炉批注对照（未处理挂新版）/
关口未点头不进收件箱/点头是落账记录/JSONL 落库/词表封闭/AST 零网络。
"""
import ast
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from translation_supervision_bench import (  # noqa: E402
    ANNOTATION_TYPES, BENCH_SCHEMA, SupervisionError,
    TranslationSupervisionBench, TranslationSupervisionLedger,
)

NOW = "2026-11-15T09:00:00Z"


def mk():
    b = TranslationSupervisionBench(source_seq="S-3（占位）",
                                    translator="agent-a（占位）",
                                    created_at=NOW, source_text="原文（占位）")
    b.submit_draft(version="v1", text="译稿 v1（占位）",
                   term_choices={"术语A（占位）": "译法1（占位）"})
    return b


class TestProgressVersions(unittest.TestCase):
    def test_submit_then_pending_review(self):
        s = mk()
        self.assertEqual(s.status, "待人审")
        self.assertEqual(s.versions[0]["version"], "v1")

    def test_duplicate_version_conflict(self):
        s = mk()
        with self.assertRaisesRegex(SupervisionError, "SUPERVISION_STATE_CONFLICT"):
            s.submit_draft(version="v1", text="x（占位）")


class TestAnnotationFeedback(unittest.TestCase):
    def test_annotate_pack_send_back(self):
        s = mk()
        s.annotate(author="甲（占位）", at=NOW, anchor="行2（占位）",
                   atype="换术语", text="术语不对（占位）", version="v1")
        s.annotate(author="甲（占位）", at=NOW, anchor="行3（占位）",
                   atype="重译", text="整句不顺（占位）", version="v1")
        fb = s.send_back(author="甲（占位）", at=NOW, annotation_seqs=[1, 2],
                         order="重译整段", note="n（占位）")
        self.assertEqual(fb["annotations"], [1, 2])
        self.assertEqual(s.status, "已发回")

    def test_send_back_requires_annotation(self):
        s = mk()
        with self.assertRaisesRegex(SupervisionError, "SUPERVISION_INCOMPLETE"):
            s.send_back(author="甲（占位）", at=NOW, annotation_seqs=[],
                        order="换术语")

    def test_return_carries_unhandled_annotations(self):
        s = mk()
        s.annotate(author="甲（占位）", at=NOW, anchor="行2（占位）",
                   atype="换术语", text="术语不对（占位）", version="v1")
        s.annotate(author="甲（占位）", at=NOW, anchor="行3（占位）",
                   atype="疑问", text="这句歧义（占位）", version="v1")
        s.send_back(author="甲（占位）", at=NOW, annotation_seqs=[1],
                    order="换术语")
        s.return_draft(version="v2", text="译稿 v2（占位）",
                       handled_annotation_seqs=[1])
        carried = [a for a in s.annotations if a["carried_to"] == "v2"]
        self.assertEqual(len(carried), 1)          # 未处理的继续挂在新版
        self.assertEqual(s.annotations[0]["status"], "已处理")

    def test_return_without_pending_feedback_refused(self):
        s = mk()
        with self.assertRaisesRegex(SupervisionError, "SUPERVISION_STATE_CONFLICT"):
            s.return_draft(version="v2", text="x（占位）",
                           handled_annotation_seqs=[])


class TestGateAndLedger(unittest.TestCase):
    def test_unapproved_never_in_inbox(self):
        s = mk()
        out = s.outlet()
        self.assertEqual(out["passed"], [])
        self.assertEqual(out["blocked"][0]["status"], "待人审")

    def test_approve_is_a_ledger_record(self):
        s = mk()
        s.annotate(author="甲（占位）", at=NOW, anchor="行2（占位）",
                   atype="通过", text="ok（占位）", version="v1")
        s.resolve_annotation(seq=1, status="已采纳")
        d = s.approve(approver="乙（占位）", at=NOW, version="v1")
        self.assertEqual((d["approver"], d["version"], d["verdict"]),
                         ("乙（占位）", "v1", "点头"))
        out = s.outlet()
        self.assertEqual(out["passed"][0]["version"], "v1")

    def test_approve_requires_unhandled_resolved(self):
        s = mk()
        s.annotate(author="甲（占位）", at=NOW, anchor="行2（占位）",
                   atype="疑问", text="x（占位）", version="v1")
        with self.assertRaisesRegex(SupervisionError, "SUPERVISION_STATE_CONFLICT"):
            s.approve(approver="乙（占位）", at=NOW, version="v1")

    def test_ledger_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sup" / "log.jsonl"
            led = TranslationSupervisionLedger(path)
            led.record(kind="progress", source_seq="S-3（占位）", at=NOW,
                       payload={"status": "出稿中"})
            led.record(kind="annotation", source_seq="S-3（占位）", at=NOW,
                       payload={"text": "x（占位）"})
            self.assertEqual(len(led.entries()), 2)
            self.assertEqual(json.loads(Path(path).read_text(
                encoding="utf-8").strip().splitlines()[0])["source_seq"],
                "S-3（占位）")


class TestRedline(unittest.TestCase):
    def test_ast_zero_network(self):
        banned = {"urllib", "requests", "socket", "http", "subprocess"}
        src = (Path(__file__).resolve().parents[1] / "scripts"
               / "translation_supervision_bench.py").read_text(encoding="utf-8")
        imported = set()
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertFalse(imported & banned, imported & banned)

    def test_vocab_closed(self):
        self.assertEqual(set(ANNOTATION_TYPES),
                         {"换术语", "重译", "疑问", "通过"})
        self.assertEqual(BENCH_SCHEMA, "translation-supervision-bench/v1")


if __name__ == "__main__":
    unittest.main()
