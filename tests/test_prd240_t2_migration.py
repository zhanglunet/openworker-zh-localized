# -*- coding: utf-8 -*-
"""PRD-240/T2 自测：存量中文知识条目迁移。"""
import sys, unittest
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from knowledge_migration import lookup, migrate_terms, trace_to_source  # noqa: E402

RAW = [{"term": "流程", "standard": "工作流", "note": "术语锁定", "origin": "terms.txt", "line_number": 1},
       {"term": "代理", "standard": "智能体", "note": "术语锁定", "origin": "terms.txt", "line_number": 2}]


class Test(unittest.TestCase):
    def test_three_layers(self):
        r = migrate_terms(RAW)
        self.assertEqual(len(r["layers"]["rules"]), 2)
        self.assertEqual(len(r["layers"]["knowledge"]), 2)
        self.assertEqual(len(r["layers"]["sources"]), 2)
        self.assertEqual(r["total"], 2)

    def test_lookup(self):
        r = migrate_terms(RAW)
        self.assertEqual(len(lookup(r, "工作流")), 1)
        self.assertEqual(lookup(r, "不存在")[1:] if lookup(r, "不存在") else [], [])

    def test_trace_to_source(self):
        r = migrate_terms(RAW)
        s = trace_to_source(r, "term-0000")
        self.assertEqual(s["line_number"], 1)
        self.assertIsNone(trace_to_source(r, "term-9999"))

    def test_json_serializable(self):
        import json
        json.dumps(migrate_terms(RAW), ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
