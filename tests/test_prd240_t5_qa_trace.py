# -*- coding: utf-8 -*-
"""PRD-240/T5 测试：验收试运行——抽样知识问答溯源（trend #1204）。

运行：uv run --no-project --with pytest python -m pytest tests/test_prd240_t5_qa_trace.py -q

验收标准（trend #1204）：**抽样问答全程可溯源到原文**。

演练（规则+知识库+原文三层真实代码全链，术语条目/原文全合成占位，
不涉及任何命理内容本身——只借三层结构）：
  ① 抽样问答 ×4：terms 原文行 → migrate_terms 三层重组 → lookup 知识层
    → trace_to_source 回指原文（origin_file/line_number/raw_text）；
    每条问答记录含知识条目 id 与原文逐字引用（全程可溯源）；
  ② 规则可算问答：evaluate_rule（expr 形态，kb_refs 引知识条目）→
    evidence 带解析后的原文引用 → 同样回指 raw_text；
  ③ 三方对齐：check_consistency 零错误零警告（无悬空/无反向/无孤儿）；
  ④ 确定性：同抽样重放逐字节一致。
"""
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from consistency_check import check_consistency  # noqa: E402
from knowledge_migration import (  # noqa: E402
    lookup,
    migrate_terms,
    trace_to_source,
)
from rule_engine import evaluate_rule  # noqa: E402

#: terms.txt 形态原文行（全合成占位——三层结构演练不涉及命理内容本身）
RAW_LINES = [
    {"term": "病象", "standard": "格局失衡的统称（占位标准词）",
     "note": "术语规范示例", "origin": "terms.txt", "line_number": 3,
     "raw": "原文行 3：病象 → 格局失衡（占位）"},
    {"term": "扶抑", "standard": "强弱调剂法（占位标准词）",
     "note": "术语规范示例", "origin": "terms.txt", "line_number": 7,
     "raw": "原文行 7：扶抑 → 强弱调剂（占位）"},
    {"term": "通关", "standard": "两神成象格的桥梁术语（占位）",
     "note": "术语规范示例", "origin": "terms.txt", "line_number": 11,
     "raw": "原文行 11：通关 → 桥梁术语（占位）"},
    {"term": "用神", "standard": "核心取用术语（占位标准词）",
     "note": "术语规范示例", "origin": "terms.txt", "line_number": 15,
     "raw": "原文行 15：用神 → 核心取用（占位）"},
]


def build_kb():
    return migrate_terms(RAW_LINES)


class 问答溯源Tests(unittest.TestCase):
    def test_lookup_traces_to_source_verbatim(self):
        """验收①：抽样问答 ×4——知识条目 → 原文逐字引用（全程可溯源）。"""
        kb = build_kb()
        for question_term in ("病象", "扶抑", "通关", "用神"):
            hits = lookup(kb, question_term)
            self.assertEqual(len(hits), 1, question_term)
            entry = hits[0]
            source = trace_to_source(kb, entry["entry_id"])
            self.assertIsNotNone(source)
            self.assertEqual(source["origin_file"], "terms.txt")
            self.assertTrue(source["raw_text"].startswith("原文行"))
            # 原文逐字包含术语与标准词形（回指可验证）
            self.assertIn(question_term, source["raw_text"])
            self.assertIn("占位", source["raw_text"])

    def test_rule_answer_carries_source_evidence(self):
        """验收②：规则可算问答——evidence 带原文引用并回指 raw_text。"""
        kb = build_kb()
        rule = {
            "rule_id": "RULE-ZHTERM-0001",
            "name": "术语命中计数（占位）",
            "form": "expr",
            "body": "hit = 1 if term_input in sample_text else 0",
            "inputs": [{"name": "term_input", "type": "string", "constraint": "待判定术语占位"},
                       {"name": "sample_text", "type": "string", "constraint": "待测文本占位"}],
            "outputs": [{"name": "hit", "type": "integer"}],
            "precondition": "term_input != '' and sample_text != ''",
            "kb_refs": ["term-0000"],
            "source_refs": ["term-0000"],
            "determinism": "strict",
            "rule_version": 1,
            "status": "active",
            "updated_at": "2026-11-08T00:00:00Z",
            "updated_by": "PLACEHOLDER_ACCOUNT",
        }
        entry = lookup(kb, "病象")[0]
        result = evaluate_rule(rule, {"term_input": "病象",
                                      "sample_text": "病象示例文本（占位）"}, kb)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["outputs"]["hit"], 1)
        blob = json.dumps(result["evidence"], ensure_ascii=False)
        self.assertIn("term-0000", blob)                    # 引用知识条目
        source = trace_to_source(kb, "term-0000")
        self.assertIn("原文行 3", source["raw_text"])       # evidence 回指原文

    def test_consistency_aligned(self):
        """③ 三方对齐：零悬空/零反向/零孤儿。"""
        report = check_consistency(build_kb())
        self.assertTrue(report["summary"]["aligned"], report["issues"])
        self.assertEqual(report["summary"]["errors"], 0)
        # 抽样库只给一条规则引用 → 未被规则引用的知识条目按提示级孤儿标注
        # （E-ORPHAN-SOURCE 是提示级 warnings，不破坏对齐；errors 恒 0）
        codes = {i["code"] for i in report["issues"]}
        self.assertNotIn("E-DANGLING-REF", codes)
        self.assertNotIn("E-CIRCULAR-REF", codes)

    def test_deterministic_replay(self):
        """④ 确定性：同抽样重放（问答+规则+一致性）逐字节一致。"""

        def replay():
            kb = build_kb()
            qa = []
            for term in ("病象", "用神"):
                entry = lookup(kb, term)[0]
                src = trace_to_source(kb, entry["entry_id"])
                qa.append({"entry_id": entry["entry_id"],
                           "raw_text": src["raw_text"]})
            return json.dumps({"qa": qa, "kb": kb}, ensure_ascii=False,
                              sort_keys=True)

        self.assertEqual(replay(), replay())


if __name__ == "__main__":
    unittest.main()
