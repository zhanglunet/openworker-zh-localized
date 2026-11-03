# -*- coding: utf-8 -*-
"""PRD-240/T4 自测（trend #1203）：一致性校验——规则/知识/原文三方对齐检查。

运行：uv run --no-project --with pytest python -m pytest tests/test_prd240_t4_consistency.py -q

覆盖（T1 §6.3/§6.4，验收「不一致条目可被检出并列出清单」）：
E-DANGLING-REF 悬空引用（规则 kb_refs/知识回指原文）、E-CIRCULAR-REF 反向
引用、E-ORPHAN-SOURCE 孤儿原文提示级、issues 机读清单（code/location/detail）、
对齐通过。零网络；全合成。
"""
import json
import sys
import unittest
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from consistency_check import check_consistency  # noqa: E402


def _three_layers():
    return {
        "schema": "knowledge-migration/v1",
        "layers": {
            "rules": [{"entry_id": "term-0000", "type": "term",
                       "pattern": "违约金上限", "replacement": "≤本金30%",
                       "check": "terminology", "kb_refs": ["term-0000"]}],
            "knowledge": [{"entry_id": "term-0000", "term": "违约金上限",
                           "standard": "≤本金30%", "category": "terminology",
                           "origin_file": "terms.txt"}],
            "sources": [{"entry_id": "term-0000", "origin_file": "terms.txt",
                         "line_number": 12, "raw_text": "12|违约金上限|≤30%"}],
        },
        "total": 1,
    }


class 三方对齐Tests(unittest.TestCase):
    def test_aligned_no_errors(self):
        report = check_consistency(_three_layers())
        assert report["summary"]["errors"] == 0
        assert report["summary"]["aligned"] is True

    def test_dangling_kb_ref_detected(self):
        layers = _three_layers()
        layers["layers"]["rules"][0]["kb_refs"] = ["term-9999"]
        report = check_consistency(layers)
        assert any(i["code"] == "E-DANGLING-REF" for i in report["issues"])
        assert report["summary"]["errors"] >= 1

    def test_reverse_ref_detected(self):
        layers = _three_layers()
        layers["layers"]["knowledge"][0]["rule_ref"] = "term-0000"
        report = check_consistency(layers)
        assert any(i["code"] == "E-CIRCULAR-REF" for i in report["issues"])

    def test_orphan_source_warning(self):
        layers = _three_layers()
        layers["layers"]["sources"].append(
            {"entry_id": "src-orphan", "origin_file": "ghost.txt",
             "line_number": 1, "raw_text": "孤儿（占位）"})
        report = check_consistency(layers)
        assert any(i["code"] == "E-ORPHAN-SOURCE" for i in report["issues"])
        assert report["summary"]["warnings"] >= 1

    def test_issue_list_machine_readable(self):
        layers = _three_layers()
        layers["layers"]["rules"][0]["kb_refs"] = ["term-9999"]
        report = check_consistency(layers)
        for issue in report["issues"]:
            assert {"code", "location", "detail"} <= set(issue)
        assert report["schema"] == "three-layer-consistency/v1"

    def test_deterministic(self):
        layers = _three_layers()
        layers["layers"]["rules"][0]["kb_refs"] = ["term-9999"]
        one = json.dumps(check_consistency(layers), ensure_ascii=False,
                         sort_keys=True)
        two = json.dumps(check_consistency(layers), ensure_ascii=False,
                         sort_keys=True)
        assert one == two


if __name__ == "__main__":
    unittest.main()
