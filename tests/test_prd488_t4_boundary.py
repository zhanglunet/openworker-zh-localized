# -*- coding: utf-8 -*-
"""PRD-488/T4 测试（trend #2363 的 T4 环节）：技能评估划界断言。
运行：uv run --with pytest python -m pytest tests/test_prd488_t4_boundary.py -q
按 PRD 任务拆分 T4 行：评估与独立验收测试/验证台/评审流水线/监督回路的边界
断言——评估不越界审产物、不审过程：
  - 评估双模块（T2 评估 + T3 闸门）对邻居模块（评审流水线/协同会话/监督台/
    下游载体）零导入（AST）；
  - 借鉴仓（NVIDIA/SkillEvaluator Apache-2.0、Claude-BugHunter MIT、
    stitch-skills Apache-2.0）零符号（仅代码标识符扫描）；
  - 下游载体词零标识符（评估只在技能层面，产物/过程通道零触碰）；
  - 红线钉值：疑似重叠拦下不自动合并/未知技能显形拒绝/闸门账本 append-only
    （深拷贝隔离）/闸门只读报告不重跑评估/无发布路径；
  - 词表封闭 + AST 零网络零子进程。
只断言，不改任何生产代码。零网络；全合成占位。
"""
import ast
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

MOD_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(MOD_DIR))
MODULE_DIR = MOD_DIR
MODULES = ["skill_evaluation.py", "skill_evaluation_gate.py"]
NEIGHBOR_STEMS = ["checklist_collab_session", "translation_review_pipeline", "checklist_supervision_bench"]
CARRIER_WORDS = ["checklist_collab_session", "translation_review_pipeline", "checklist_supervision_bench", "engine"]

from skill_evaluation import evaluate  # noqa: E402
from skill_evaluation_gate import (  # noqa: E402
    BLOCK_REASON_CODES, GATE_AUDIT_KINDS, GateError,
    SkillEvaluationLedger, check_gate)

NOW = "2026-11-17T10:00:00Z"
BY = "reviewer（占位）"



PASS_METRICS = {"sample_tasks": 25, "error_rate_with_skill": 0.10,
                "error_rate_without_skill": 0.40, "new_error_types": 0}


def make_report(specs):
    skills = [{"id": sid, "text": sid + " 占位文本", "metrics": m}
              for sid, m in specs]
    report = evaluate({"prd": 488, "repo": "openworker-zh-localized",
                       "generated_at": "2026-11-17", "version": 1,
                       "design_ref": "docs/plans（占位）",
                       "gate": "error-rate",
                       "thresholds": {"min_sample_tasks": 20,
                                      "min_relative_error_drop": 0.2,
                                      "max_new_error_types": 0,
                                      "overlap_similarity": 0.8},
                       "skills": skills})
    return report


def codes(verdict):
    return [r["code"] for r in verdict["reasons"]]


class TestGatePins(unittest.TestCase):
    def test_redline_overlap_blocked_even_if_passing(self):
        """红线：疑似重叠拦下不自动合并。"""
        report = make_report([("skill-a", PASS_METRICS)])
        report["suspected"] = [{"a": "skill-a", "b": "other",
                                "similarity": 0.9, "suspected": True}]
        d = check_gate(report, "skill-a")
        self.assertFalse(d["allowed"])
        self.assertIn("SUSPECTED_OVERLAP", codes(d))

    def test_redline_unknown_skill_explicit(self):
        with self.assertRaisesRegex(GateError, "UNKNOWN_SKILL"):
            check_gate(make_report([("skill-a", PASS_METRICS)]), "ghost")

    def test_redline_ledger_append_only_deep_copy(self):
        led = SkillEvaluationLedger(None)
        led.record({"prd": 488}, {"kind": "gate_passed", "skill_id": "s",
                                    "by": BY, "at": NOW})
        snapshot = led.entries()
        snapshot[0]["kind"] = "改（占位）"
        self.assertEqual(led.entries()[0]["kind"], "gate_passed")

    def test_redline_gate_reads_not_reruns(self):
        report = make_report([("skill-a", PASS_METRICS)])
        before = copy.deepcopy(report)
        check_gate(report, "skill-a")
        self.assertEqual(json.dumps(report, sort_keys=True),
                         json.dumps(before, sort_keys=True))

    def test_vocab_closed(self):
        self.assertEqual(set(BLOCK_REASON_CODES),
                         {"BAD_REPORT", "UNKNOWN_SKILL", "REMEDIATE",
                          "INSUFFICIENT_EVIDENCE", "SUSPECTED_OVERLAP"})
        self.assertEqual(set(GATE_AUDIT_KINDS),
                         {"gate_passed", "gate_blocked", "remediation"})

class TestBoundary(unittest.TestCase):
    def test_eval_modules_zero_neighbor_imports(self):
        """评估双模块对邻居（评审流水线/协同会话/监督台/下游载体）零导入。"""
        for mod in MODULES:
            src = (MODULE_DIR / mod).read_text(encoding="utf-8")
            imported = set()
            for node in ast.walk(ast.parse(src)):
                if isinstance(node, ast.Import):
                    imported.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            for stem in NEIGHBOR_STEMS:
                self.assertNotIn(stem, imported, f"{mod} 导入邻居 {stem}")

    def test_downstream_carrier_zero_identifiers(self):
        """下游载体词零标识符（产物通道/过程通道不在评估模块里）。"""
        for mod in MODULES:
            src = (MODULE_DIR / mod).read_text(encoding="utf-8")
            tree = ast.parse(src)
            names = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    names.add(node.name.lower())
                elif isinstance(node, ast.arg):
                    names.add(node.arg.lower())
                elif isinstance(node, ast.Name):
                    names.add(node.id.lower())
                elif isinstance(node, ast.Attribute):
                    names.add(node.attr.lower())
            for word in CARRIER_WORDS:
                self.assertNotIn(word, names,
                                 f"{mod} 标识符出现下游载体词 {word}")

    def test_borrowed_zero_symbols(self):
        """借鉴仓零符号（SkillEvaluator/BugHunter/stitch-skills，仅标识符）。"""
        for mod in MODULES:
            src = (MODULE_DIR / mod).read_text(encoding="utf-8")
            tree = ast.parse(src)
            names = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    names.add(node.name.lower())
                elif isinstance(node, ast.Name):
                    names.add(node.id.lower())
                elif isinstance(node, ast.Attribute):
                    names.add(node.attr.lower())
            for word in ("skillevaluator", "bughunter", "stitch_skills"):
                self.assertNotIn(word, names,
                                 f"{mod} 标识符出现借鉴词 {word}")

    def test_no_publish_path(self):
        """评估不碰发布/删除：评估双模块无发布路径符号。"""
        for mod in MODULES:
            src = (MODULE_DIR / mod).read_text(encoding="utf-8")
            tree = ast.parse(src)
            names = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    names.add(node.name.lower())
                elif isinstance(node, ast.Name):
                    names.add(node.id.lower())
            for word in ("publish", "delete_skill", "remove_skill",
                         "merge_skill"):
                self.assertNotIn(word, names, f"{mod} 出现 {word}")

    def test_ast_zero_network(self):
        """AST 零网络零子进程（评估双模块）。"""
        banned = {"urllib", "requests", "socket", "http", "subprocess"}
        for mod in MODULES:
            src = (MODULE_DIR / mod).read_text(encoding="utf-8")
            imported = set()
            for node in ast.walk(ast.parse(src)):
                if isinstance(node, ast.Import):
                    imported.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            self.assertFalse(imported & banned,
                             f"{mod} 导入 {imported & banned}")


if __name__ == "__main__":
    unittest.main()
