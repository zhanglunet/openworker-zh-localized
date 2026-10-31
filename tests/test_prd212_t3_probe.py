# -*- coding: utf-8 -*-
"""PRD-212/T3 自测（trend #1062）：中文触发词可用性抽查。

运行：.venv/bin/python -m pytest tests/test_prd212_t3_probe.py -q

覆盖（T1 §4 + 验收「抽查记录完整」）：
  探测样本集：标准 3 + 口语 A/B/C/D 各 2（共 8）+ 反向 3；缺标准触发词拒绝
  run_probe_suite：注入式唤起逐条记 invoked/actual_skill（离线可跑）
  通过标准（§4.3）：标准 3/3 且口语 ≥6/8 且每类 ≥1 且反向 0 误触发 → PASS；
    任一层失败 → FAIL（三类失败形态各测一）
  probe CSV 落盘：§4.4 十一字段齐全、行数一致（记录完整可回溯）

虚构纪律：技能/触发词全虚构；零网络。
"""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from trigger_probe import (  # noqa: E402
    ProbeError,
    build_probe_suite,
    check_pass_criteria,
    run_probe_suite,
    write_probe_csv,
)

MANIFEST = {"skills": [{
    "skill_id": "zh-demo", "skill_name": "示例技能（虚构）",
    "expected_version": "1.0.0",
    "triggers": {"standard": ["示例简报", "晨会速览", "值班交接"]},
    "files": [], "history": [],
}]}


def all_pass_invoke(utterance):
    for word in ("示例简报", "晨会速览", "值班交接"):
        if word in utterance:
            return "zh-demo"
    if "示例简报" in utterance or "速览" in utterance or "交接" in utterance:
        return "zh-demo"
    return None  # 反向与无关请求不唤起


class ProbeSuiteTests(unittest.TestCase):
    def test_suite_shape(self):
        probes = build_probe_suite(MANIFEST)
        by_type = {}
        for p in probes:
            by_type[p["variant_type"]] = by_type.get(p["variant_type"], 0) + 1
        self.assertEqual(by_type["STANDARD"], 3)
        self.assertEqual(by_type["A"], 2)
        self.assertEqual(by_type["B"], 2)
        self.assertEqual(by_type["C"], 2)
        self.assertEqual(by_type["D"], 2)
        self.assertEqual(by_type["REVERSE"], 3)
        self.assertEqual(len(probes), 14)  # 11 正向 + 3 反向

    def test_missing_standard_triggers_rejected(self):
        bad = {"skills": [{"skill_id": "x", "triggers": {"standard": []}}]}
        with self.assertRaises(ProbeError):
            build_probe_suite(bad)

    def test_run_records_all_probes(self):
        probes = build_probe_suite(MANIFEST)
        records = run_probe_suite(probes, all_pass_invoke, checked_by="t",
                                  checked_at="2026-10-31T12:00:00+00:00")
        self.assertEqual(len(records), len(probes))
        self.assertTrue(all(r["invoked"] in ("Y", "N") for r in records))
        self.assertTrue(all(r["checked_by"] == "t" for r in records))


class CriteriaTests(unittest.TestCase):
    def records_with_invoke_fn(self, fn):
        return run_probe_suite(build_probe_suite(MANIFEST), fn, checked_by="t")

    def test_all_pass_verdict(self):
        report = check_pass_criteria(self.records_with_invoke_fn(all_pass_invoke))
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["standard"], "3/3")
        self.assertEqual(report["false_triggers"], 0)

    def test_standard_miss_fails(self):
        def fn(u):
            if u == "示例简报":  # 标准词漏唤起
                return None
            return all_pass_invoke(u)

        report = check_pass_criteria(self.records_with_invoke_fn(fn))
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(report["standard"], "2/3")

    def test_oral_below_threshold_fails(self):
        def fn(u):
            # 只认标准词（精确）与 B 类两条：口语命中 2 < 6 → FAIL
            if u in ("示例简报", "晨会速览", "值班交接"):
                return "zh-demo"
            if u == "来一份示例简报":
                return "zh-demo"
            return None

        report = check_pass_criteria(self.records_with_invoke_fn(fn))
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(report["oral"], "2/8")

    def test_false_trigger_fails(self):
        def fn(u):
            if "日程" in u:  # 反向样本被误唤起
                return "zh-demo"
            return all_pass_invoke(u)

        report = check_pass_criteria(self.records_with_invoke_fn(fn))
        self.assertEqual(report["verdict"], "FAIL")
        self.assertEqual(report["false_triggers"], 1)

    def test_csv_roundtrip_complete(self):
        records = self.records_with_invoke_fn(all_pass_invoke)
        with tempfile.TemporaryDirectory() as td:
            path = write_probe_csv(records, Path(td) / "probe.csv")
            with open(path, encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), len(records))
            self.assertEqual(set(rows[0].keys()),
                             {"probe_id", "skill_id", "tool", "variant_type",
                              "utterance", "expected_skill", "actual_skill",
                              "invoked", "evidence_note", "checked_at", "checked_by"})


if __name__ == "__main__":
    unittest.main()
