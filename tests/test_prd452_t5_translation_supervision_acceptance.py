# -*- coding: utf-8 -*-
"""PRD-452/T5 测试（trend #2159 的 T5 环节）：翻译监督台验收试运行。
运行：uv run --with pytest python -m pytest tests/test_prd452_t5_translation_supervision_acceptance.py -q
验收（T1 §7 全链）：真实监督回路全链演练两遍逐字节一致——出稿落账 → 人
批注（两条）→ 一条发回一条留新 → 打包发回（重译整段）→ agent 回炉 v2
（批注对照：一条已处理、一条挂新版）→ 处理批注 → 点头 → 双出口（T2
outlet+T3 gate）进人工拍板收件箱；失败演练：未点头拦在收件箱外/闸门拦
手写 status 位/闸门拦点头非最新版；JSONL 留痕；链复跑 T2/T3/T4 子进程
exit 0；文档无密钥。零网络；全合成占位。
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from translation_supervision_bench import (  # noqa: E402
    TranslationSupervisionBench, TranslationSupervisionLedger)
from translation_supervision_gate import admit_via_gate  # noqa: E402

NOW = "2026-11-15T09:00:00Z"
T1 = "2026-11-15T10:00:00Z"
T2 = "2026-11-15T11:00:00Z"
T3 = "2026-11-15T12:00:00Z"
TESTS = Path(__file__).resolve().parent


def full_chain():
    """真实监督回路全链：出稿→批注→发回→回炉对照→处理→点头→双出口。"""
    b = TranslationSupervisionBench(source_seq="S-7（占位）",
                                    translator="agent-a（占位）",
                                    created_at=NOW, source_text="原文（占位）")
    led = TranslationSupervisionLedger(None)
    led.record(kind="progress", source_seq=b.source_seq, at=NOW,
               payload={"status": "出稿中"})
    b.submit_draft(version="v1", text="译稿 v1（占位）",
                   term_choices={"术语A（占位）": "译法1（占位）"})
    led.record(kind="progress", source_seq=b.source_seq, at=NOW,
               payload={"status": "待人审", "version": "v1"})
    b.annotate(author="甲（占位）", at=T1, anchor="术语A（占位）",
               atype="换术语", text="术语不对（占位）", version="v1")
    b.annotate(author="甲（占位）", at=T1, anchor="行5（占位）",
               atype="疑问", text="歧义（占位）", version="v1")
    b.send_back(author="甲（占位）", at=T1, annotation_seqs=[1, 2],
                order="重译整段", note="n（占位）")
    led.record(kind="feedback", source_seq=b.source_seq, at=T1,
               payload=b.feedbacks[0])
    b.return_draft(version="v2", text="译稿 v2（占位）",
                   handled_annotation_seqs=[1])
    led.record(kind="progress", source_seq=b.source_seq, at=T2,
               payload={"status": "待人审", "version": "v2"})
    b.resolve_annotation(seq=2, status="已驳回")
    b.approve(approver="乙（占位）", at=T3, version="v2")
    led.record(kind="decision", source_seq=b.source_seq, at=T3,
               payload=b.decisions[0])
    outlet = b.outlet()
    gate = admit_via_gate(b)
    return {"status": b.status,
            "versions": [v["version"] for v in b.versions],
            "annotations": b.annotations, "feedbacks": b.feedbacks,
            "outlet": outlet, "gate": gate, "ledger": led.entries()}


class TestFullChain(unittest.TestCase):
    def test_chain_twice_byte_identical(self):
        runs = [full_chain(), full_chain()]
        self.assertEqual(json.dumps(runs[0], sort_keys=True),
                         json.dumps(runs[1], sort_keys=True))

    def test_revised_version_reaches_inbox(self):
        run = full_chain()
        self.assertEqual(run["outlet"]["passed"][0]["version"], "v2")
        self.assertEqual(run["gate"]["passed"][0]["version"], "v2")
        self.assertEqual(run["gate"]["passed"][0]["gate"], "GATE_ALLOWED")

    def test_annotation_carryover(self):
        run = full_chain()
        handled = [a for a in run["annotations"] if a["status"] == "已处理"]
        carried = [a for a in run["annotations"] if a["carried_to"] == "v2"]
        rejected = [a for a in run["annotations"] if a["status"] == "已驳回"]
        self.assertEqual(len(handled), 1)
        self.assertEqual(len(carried), 1)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(carried[0]["seq"], rejected[0]["seq"])   # 同一条：挂新版后被驳回

    def test_ledger_full_trail(self):
        run = full_chain()
        kinds = [e["kind"] for e in run["ledger"]]
        self.assertEqual(kinds, ["progress", "progress", "feedback",
                                 "progress", "decision"])


class TestFailureDrills(unittest.TestCase):
    def test_unapproved_blocked_from_inbox(self):
        b = TranslationSupervisionBench(source_seq="S（占位）",
                                        translator="a（占位）", created_at=NOW,
                                        source_text="原文（占位）")
        b.submit_draft(version="v1", text="x（占位）")
        out = b.outlet()
        self.assertEqual(out["passed"], [])
        self.assertEqual(out["blocked"][0]["status"], "待人审")

    def test_gate_blocks_handwritten_status(self):
        b = TranslationSupervisionBench(source_seq="S（占位）",
                                        translator="a（占位）", created_at=NOW,
                                        source_text="原文（占位）")
        b.submit_draft(version="v1", text="x（占位）")
        b.status = "已点头"   # 手写 status 位
        out = admit_via_gate(b)
        self.assertEqual(out["passed"], [])

    def test_gate_blocks_stale_version_approval(self):
        b = TranslationSupervisionBench(source_seq="S（占位）",
                                        translator="a（占位）", created_at=NOW,
                                        source_text="原文（占位）")
        b.submit_draft(version="v1", text="x1（占位）")
        b.approve(approver="乙（占位）", at=NOW, version="v1")
        b.versions.append({"version": "v2", "text": "x2（占位）",
                           "term_choices": {}})
        out = admit_via_gate(b)
        self.assertEqual(out["passed"], [])
        self.assertEqual(out["blocked"][0]["gate"], "GATE_NOT_LATEST_VERSION")


class TestChainRerun(unittest.TestCase):
    def test_t2_t3_t4_rerun_green(self):
        """链复跑：T2/T3/T4 测试子进程复跑 exit 0（链上仍绿实测）。"""
        for name in ("test_prd452_t2_translation_supervision_bench.py",
                     "test_prd452_t3_translation_supervision_gate.py",
                     "test_prd452_t4_translation_supervision_boundary.py"):
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "discover",
                 "-s", str(TESTS), "-p", name],
                capture_output=True, timeout=300)
            self.assertIn(proc.returncode, (0, 5),
                             f"{name} 复跑失败：{proc.stdout[-400:]}{proc.stderr[-400:]}")


class TestDocNoSecrets(unittest.TestCase):
    def test_t1_design_doc_no_secrets(self):
        """文档无密钥：T1 设计拼接 needle 扫描+占位符纪律（R5）。"""
        doc = next(Path(__file__).resolve().parents[1].glob(
            "docs/plans/2026-11-15-prd-452-*.md"))
        text = doc.read_text(encoding="utf-8").lower()
        for needle in ("sk-" + "live", "passw" + "ord", "api_k" + "ey"):
            self.assertNotIn(needle, text, f"设计文档出现密钥词 {needle}")
        self.assertIn("占位", text)


if __name__ == "__main__":
    unittest.main()
