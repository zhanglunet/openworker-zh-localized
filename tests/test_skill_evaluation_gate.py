"""PRD-488/T3 测试（trend #2362 的 T3 环节）：中文技能评估监督回路闸门。
uv run --with pytest python -m pytest tests/test_skill_evaluation_gate.py -q
覆盖（T1 §五 + §七红线）：只放行评估"通过"的技能/整改拦下并追加整改条目/
证据不足拦下但不进整改清单/疑似重叠拦下待人确认/未知技能先记账再拒绝/
放行与拦截审计留痕/加固出口批量过闸/整改清单 append-only/词表封闭/
AST 零网络/无发布路径/闸门自身不授予通过。
零网络；全合成占位（真实清单只读断言用 skill-eval/inventory.json）。
"""

import ast
import sys
import tempfile
import unittest
from pathlib import Path

MOD_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(MOD_DIR))
MODULE_DIR = MOD_DIR

from skill_evaluation import (  # noqa: E402
    VERDICT_INSUFFICIENT,
    VERDICT_PASS,
    VERDICT_REMEDIATE,
    evaluate,
    load_inventory,
)
from skill_evaluation_gate import (  # noqa: E402
    BLOCK_REASON_CODES,
    GATE_AUDIT_KINDS,
    GATE_SCHEMA,
    GateError,
    SkillEvaluationLedger,
    admit_to_downstream,
    check_gate,
    enforce_gate,
    format_remediation_line,
    gate_outlet,
)

NOW = "2026-11-17T09:00:00Z"
BY = "reviewer（占位）"
THRESHOLDS = {"min_sample_tasks": 20, "min_relative_error_drop": 0.20,
              "max_new_error_types": 0, "overlap_similarity": 0.8}
INVENTORY = Path(__file__).resolve().parents[1] / "skill-eval" / "inventory.json"


def make_report(specs):
    """按给定的 (技能 id, 评分数) 合成一份 T2 报告；评分数是 metrics dict。

    文本默认各不相同（不触发疑似重叠）；传 text 可指定文本。
    """
    topics = ["术语表维护", "译稿润色说明", "审校步骤梳理", "双语对照盘点",
              "翻译记忆报表", "报表解读说明", "文风合规审查", "差异摘要推送",
              "模板生成说明", "评审角度核对"]
    skills = []
    for i, spec in enumerate(specs):
        skill_id, metrics = spec[0], spec[1]
        text = spec[2] if len(spec) > 2 else f"{skill_id} {topics[i % len(topics)]} 占位"
        skills.append({"id": skill_id, "text": text, "metrics": metrics})
    inventory = {"prd": 488, "repo": "openworker-zh-localized", "generated_at": "2026-11-17",
                 "design_ref": "design（占位）", "version": 1,
                 "thresholds": THRESHOLDS, "gate": "error-rate",
                 "skills": skills}
    return evaluate(inventory)


def passing_metrics():
    return {"sample_tasks": 20, "error_rate_with_skill": 0.08,
            "error_rate_without_skill": 0.10, "new_error_types": 0}


def failing_metrics():
    return {"sample_tasks": 20, "error_rate_with_skill": 0.09,
            "error_rate_without_skill": 0.10, "new_error_types": 0}


def no_runs_metrics():
    return {"sample_tasks": 0, "error_rate_with_skill": None,
            "error_rate_without_skill": None, "new_error_types": None}


def codes(verdict):
    return [r["code"] for r in verdict["reasons"]]


class TestCheckGate(unittest.TestCase):
    def test_passing_skill_admitted(self):
        report = make_report([("skill-a", passing_metrics())])
        v = check_gate(report, "skill-a")
        self.assertTrue(v["allowed"])
        self.assertEqual(v["reasons"], [])

    def test_remediate_skill_blocked(self):
        report = make_report([("skill-a", failing_metrics())])
        v = check_gate(report, "skill-a")
        self.assertFalse(v["allowed"])
        self.assertIn("REMEDIATE", codes(v))
        self.assertEqual(report["remediation_candidates"][0]["id"], "skill-a")

    def test_insufficient_evidence_blocked(self):
        report = make_report([("skill-a", no_runs_metrics())])
        v = check_gate(report, "skill-a")
        self.assertFalse(v["allowed"])
        self.assertIn("INSUFFICIENT_EVIDENCE", codes(v))
        self.assertEqual(report["remediation_candidates"], [])

    def test_real_inventory_all_insufficient_blocked(self):
        # 今天的实情：首份评估 12 个技能全是"证据不足"，闸门把它们全拦下——
        # 不是闸门太严，是真实对照跑分还没补，跑分出来重评通过后才能放行。
        report = evaluate(load_inventory(INVENTORY))
        self.assertEqual(report["skill_count"], 12)
        self.assertTrue(all(v["verdict"] == VERDICT_INSUFFICIENT
                            for v in report["verdicts"]))
        for verdict in report["verdicts"]:
            v = check_gate(report, verdict["id"])
            self.assertFalse(v["allowed"])
            self.assertIn("INSUFFICIENT_EVIDENCE", codes(v))

    def test_suspected_overlap_blocked_even_if_passing(self):
        # 两个技能文本完全相同 → 相似度 1.0，疑似重叠；质量门过了也拦下待人确认。
        same_text = "占位 相同 文本内容"
        report = make_report([("skill-a", passing_metrics(), same_text),
                              ("skill-b", passing_metrics(), same_text)])
        self.assertEqual(len(report["suspected"]), 1)
        for skill_id in ("skill-a", "skill-b"):
            v = check_gate(report, skill_id)
            self.assertFalse(v["allowed"])
            self.assertIn("SUSPECTED_OVERLAP", codes(v))

    def test_other_skill_verdict_does_not_count(self):
        # 只给 skill-b 判了通过，skill-a 仍须拦下：结论按技能认，不串技能。
        report = make_report([("skill-a", no_runs_metrics()),
                              ("skill-b", passing_metrics())])
        v = check_gate(report, "skill-a")
        self.assertFalse(v["allowed"])
        self.assertIn("INSUFFICIENT_EVIDENCE", codes(v))

    def test_unknown_skill_raises(self):
        report = make_report([("skill-a", passing_metrics())])
        with self.assertRaises(GateError) as cm:
            check_gate(report, "skill-z")
        self.assertIn("UNKNOWN_SKILL", str(cm.exception))

    def test_malformed_report_blocked_not_raised(self):
        passing = make_report([("skill-a", passing_metrics())])
        bad_reports = [None, "x", {}, {"prd": 999, "repo": "openworker-zh-localized",
                                        "verdicts": passing["verdicts"]},
                       {"prd": 488, "repo": "other",
                        "verdicts": passing["verdicts"]},
                       {"prd": 488, "repo": "openworker-zh-localized"}]
        for bad in bad_reports:
            v = check_gate(bad, "skill-a")
            self.assertFalse(v["allowed"])
            self.assertIn("BAD_REPORT", codes(v))

    def test_unknown_verdict_value_blocked(self):
        report = make_report([("skill-a", passing_metrics())])
        report["verdicts"][0]["verdict"] = "已下线（词表外占位）"
        v = check_gate(report, "skill-a")
        self.assertFalse(v["allowed"])
        self.assertIn("BAD_REPORT", codes(v))

    def test_missing_suspected_list_blocked(self):
        # Codex P2：报告缺 suspected 列表时，重叠结果未知，不得按"无重叠"放行。
        base = make_report([("skill-a", passing_metrics())])
        missing = dict(base)
        del missing["suspected"]
        variants = [missing]
        for broken in (None, "not-a-list", {"a": "skill-a"}):
            report = dict(base)
            report["suspected"] = broken
            variants.append(report)
        for report in variants:
            v = check_gate(report, "skill-a")
            self.assertFalse(v["allowed"])
            self.assertIn("BAD_REPORT", codes(v))


class TestEnforceAndAdmit(unittest.TestCase):
    def test_enforce_passes_approved(self):
        report = make_report([("skill-a", passing_metrics())])
        self.assertTrue(enforce_gate(report, "skill-a")["allowed"])

    def test_enforce_raises_gate_blocked(self):
        report = make_report([("skill-a", failing_metrics())])
        with self.assertRaises(GateError) as cm:
            enforce_gate(report, "skill-a")
        self.assertIn("GATE_BLOCKED", str(cm.exception))

    def test_admit_passes_and_audits(self):
        report = make_report([("skill-a", passing_metrics())])
        with tempfile.TemporaryDirectory() as d:
            led = SkillEvaluationLedger(Path(d) / "gate.jsonl")
            out = admit_to_downstream(report, "skill-a", ledger=led,
                                      by=BY, at=NOW)
            self.assertEqual(out["admitted"]["skill_id"], "skill-a")
            self.assertEqual(out["admitted"]["verdict"], VERDICT_PASS)
            self.assertTrue(out["verdict"]["allowed"])
            entries = led.entries()
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["kind"], "gate_passed")

    def test_admit_remediate_blocked_audits_and_appends_remediation(self):
        report = make_report([("skill-a", failing_metrics())])
        with tempfile.TemporaryDirectory() as d:
            led = SkillEvaluationLedger(Path(d) / "gate.jsonl")
            with self.assertRaises(GateError) as cm:
                admit_to_downstream(report, "skill-a", ledger=led,
                                    by=BY, at=NOW)
            self.assertIn("GATE_BLOCKED", str(cm.exception))
            entries = led.entries()
            self.assertEqual([e["kind"] for e in entries],
                             ["gate_blocked", "remediation"])
            self.assertIn("REMEDIATE", entries[0]["reasons"])
            remediation = entries[1]
            self.assertEqual(remediation["skill_id"], "skill-a")
            self.assertEqual(remediation["verdict"], VERDICT_REMEDIATE)
            self.assertEqual(remediation["due"], "待定")
            self.assertIsNone(remediation["retest"])
            line = format_remediation_line(remediation)
            self.assertIn("技能 skill-a", line)
            self.assertIn("整改期限 待定", line)
            self.assertIn("复测结果 待复测", line)

    def test_admit_insufficient_blocked_audits_without_remediation(self):
        # 证据不足拦下，但不进整改清单：证据不足不是失效，只等补测。
        report = make_report([("skill-a", no_runs_metrics())])
        with tempfile.TemporaryDirectory() as d:
            led = SkillEvaluationLedger(Path(d) / "gate.jsonl")
            with self.assertRaises(GateError):
                admit_to_downstream(report, "skill-a", ledger=led,
                                    by=BY, at=NOW)
            kinds = [e["kind"] for e in led.entries()]
            self.assertEqual(kinds, ["gate_blocked"])

    def test_admit_unknown_skill_audits_then_raises(self):
        # 未知技能也要先记一条 gate_blocked 再拒绝，绕关尝试留痕。
        report = make_report([("skill-a", passing_metrics())])
        with tempfile.TemporaryDirectory() as d:
            led = SkillEvaluationLedger(Path(d) / "gate.jsonl")
            with self.assertRaises(GateError) as cm:
                admit_to_downstream(report, "skill-z", ledger=led,
                                    by=BY, at=NOW)
            self.assertIn("GATE_BLOCKED", str(cm.exception))
            entry = led.latest_for("skill-z")
            self.assertEqual(entry["kind"], "gate_blocked")
            self.assertIn("UNKNOWN_SKILL", entry["reasons"])

    def test_admit_without_ledger_still_gates(self):
        report = make_report([("skill-a", passing_metrics())])
        out = admit_to_downstream(report, "skill-a", by=BY, at=NOW)
        self.assertTrue(out["verdict"]["allowed"])
        with self.assertRaises(GateError):
            admit_to_downstream(make_report([("skill-a", failing_metrics())]),
                                "skill-a", by=BY, at=NOW)


class TestGateOutlet(unittest.TestCase):
    def test_mixed_batch(self):
        report = make_report([("skill-a", passing_metrics()),
                              ("skill-b", failing_metrics()),
                              ("skill-c", no_runs_metrics())])
        out = gate_outlet(report, ["skill-a", "skill-b", "skill-c",
                                   "skill-z", None],
                          by=BY, at=NOW)
        self.assertEqual(len(out["passed"]), 1)
        self.assertEqual(out["passed"][0]["skill_id"], "skill-a")
        self.assertEqual(out["blocked_count"], 4)
        self.assertEqual([b["skill_id"] for b in out["blocked"]],
                         ["skill-b", "skill-c", "skill-z", None])
        self.assertTrue(any(r["code"] == "UNKNOWN_SKILL"
                            for r in out["blocked"][2]["reasons"]))
        self.assertEqual(out["schema"], GATE_SCHEMA)

    def test_outlet_audits_both_outcomes(self):
        report = make_report([("skill-a", passing_metrics()),
                              ("skill-b", failing_metrics())])
        with tempfile.TemporaryDirectory() as d:
            led = SkillEvaluationLedger(Path(d) / "gate.jsonl")
            gate_outlet(report, ["skill-a", "skill-b"],
                        ledger=led, by=BY, at=NOW)
            kinds = [e["kind"] for e in led.entries()]
            self.assertEqual(kinds,
                             ["gate_passed", "gate_blocked", "remediation"])

    def test_outlet_empty_input(self):
        report = make_report([("skill-a", passing_metrics())])
        out = gate_outlet(report, [], by=BY, at=NOW)
        self.assertEqual(out["passed"], [])
        self.assertEqual(out["blocked_count"], 0)


class TestRemediationLedger(unittest.TestCase):
    def test_append_only(self):
        report = make_report([("skill-a", failing_metrics())])
        with tempfile.TemporaryDirectory() as d:
            led = SkillEvaluationLedger(Path(d) / "gate.jsonl")
            with self.assertRaises(GateError):
                admit_to_downstream(report, "skill-a", ledger=led,
                                    by=BY, at=NOW)
            first = led.entries()
            with self.assertRaises(GateError):
                admit_to_downstream(report, "skill-a", ledger=led,
                                    by=BY, at=NOW)
            second = led.entries()
            # 只追加：第一次的条目原样保留，第二次只多出两条（审计+整改）。
            self.assertEqual(len(first), 2)
            self.assertEqual(len(second), 4)
            self.assertEqual(second[:2], first)
            # entries() 返回拷贝：改返回结果不污染账本。
            second[0]["kind"] = "tampered（占位）"
            self.assertEqual(led.entries()[0]["kind"], "gate_blocked")

    def test_nested_audit_fields_are_deep_copies(self):
        # Codex P2：entries()/latest_for() 返回深拷贝，改嵌套的 reasons/targets
        # 也不污染账本。
        report = make_report([("skill-a", no_runs_metrics())])
        with tempfile.TemporaryDirectory() as d:
            led = SkillEvaluationLedger(Path(d) / "gate.jsonl")
            with self.assertRaises(GateError):
                admit_to_downstream(report, "skill-a", ledger=led,
                                    by=BY, at=NOW)
            led.entries()[0]["reasons"].clear()
            led.entries()[0]["targets"].clear()
            self.assertEqual(led.entries()[0]["reasons"],
                             ["INSUFFICIENT_EVIDENCE"])
            self.assertEqual(led.entries()[0]["targets"], ["skill-a"])
            led.latest_for("skill-a")["reasons"].append("tampered（占位）")
            self.assertEqual(led.latest_for("skill-a")["reasons"],
                             ["INSUFFICIENT_EVIDENCE"])

    def test_missing_required_fields_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            led = SkillEvaluationLedger(Path(d) / "gate.jsonl")
            with self.assertRaises(GateError):
                led.record({"prd": 488, "date": "2026-11-17",
                            "inventory_version": 1},
                           {"kind": "gate_blocked", "by": BY, "at": NOW})
            self.assertEqual(led.entries(), [])

    def test_latest_for(self):
        report = make_report([("skill-a", passing_metrics()),
                              ("skill-b", failing_metrics())])
        with tempfile.TemporaryDirectory() as d:
            led = SkillEvaluationLedger(Path(d) / "gate.jsonl")
            admit_to_downstream(report, "skill-a", ledger=led,
                                by=BY, at=NOW)
            with self.assertRaises(GateError):
                admit_to_downstream(report, "skill-b", ledger=led,
                                    by=BY, at=NOW)
            self.assertEqual(led.latest_for("skill-b")["kind"], "remediation")
            self.assertIsNone(led.latest_for("skill-z"))


class TestVocabularyNetworkAndRedLines(unittest.TestCase):
    def test_vocabularies_closed(self):
        self.assertEqual(set(BLOCK_REASON_CODES),
                         {"BAD_REPORT", "UNKNOWN_SKILL", "REMEDIATE",
                          "INSUFFICIENT_EVIDENCE", "SUSPECTED_OVERLAP"})
        self.assertEqual(set(GATE_AUDIT_KINDS),
                         {"gate_passed", "gate_blocked", "remediation"})

    def test_zero_network_ast(self):
        src = (MODULE_DIR / "skill_evaluation_gate.py").read_text(
            encoding="utf-8")
        tree = ast.parse(src)
        banned = {"socket", "urllib", "requests", "http", "subprocess",
                  "smtplib", "ftplib"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn(a.name.split(".")[0], banned)
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertNotIn(node.module.split(".")[0], banned)

    def test_no_publish_path(self):
        # 发布仍人工确认：闸门模块不含任何发布路径。
        src = (MODULE_DIR / "skill_evaluation_gate.py").read_text(
            encoding="utf-8")
        for token in ("publish", "release(", "deploy", "upload("):
            self.assertNotIn(token, src)

    def test_gate_cannot_grant_pass(self):
        # 闸门只读评估报告的结论，绝不能自己给技能判"通过"或重跑评估。
        src = (MODULE_DIR / "skill_evaluation_gate.py").read_text(
            encoding="utf-8")
        self.assertNotIn("] = VERDICT_PASS", src)
        self.assertNotIn('"verdict": VERDICT_PASS', src)
        self.assertNotIn("evaluate(", src)


if __name__ == "__main__":
    unittest.main()
