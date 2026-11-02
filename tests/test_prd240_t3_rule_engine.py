# -*- coding: utf-8 -*-
"""PRD-240/T3 自测（trend #1202）：规则层计算接口——可算规则的表达与执行。

运行：uv run --no-project --with pytest python -m pytest tests/test_prd240_t3_rule_engine.py -q

覆盖（T1 §5/§5.1/§6，验收「抽样规则可算出结果并回指原文依据」）：
  validate_rule 全字段（id 格式/词表/封闭类型/kb_refs 非空不悬空/strict）；
  expr 求值（算术+条件+白名单函数）、table 判定表（命中/无行→not_applicable）、
  formula；precondition 不满足统一 not_applicable（§5.1-3）；script 拒绝执行；
  非 active 拒绝；类型封闭校验（缺/多/类型不符）；回指原文依据（evidence.sources
  经 T2 trace_to_source 解析到 raw_text）；确定性；未放行语法拒绝。
零网络；示例规则/数值全为占位。
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from knowledge_migration import migrate_terms  # noqa: E402
from rule_engine import (  # noqa: E402
    RuleError,
    evaluate_rule,
    validate_rule,
)


def _kb():
    """三层合成知识库（T2 migrate_terms 形态）：规则引用的条目 + 原文层。"""
    return migrate_terms([
        {"term": "违约金上限", "standard": "不超过主合同本金 30%（占位）",
         "note": "合同违约条款口径", "origin": "terms.txt", "line_number": 12,
         "raw": "12|违约金上限|不超过主合同本金 30%"},
        {"term": "逾期利率", "standard": "日万分之五（占位）",
         "note": "", "origin": "terms.txt", "line_number": 13,
         "raw": "13|逾期利率|日万分之五"},
    ])


def _expr_rule(**overrides):
    rule = {
        "rule_id": "RULE-CONTRACT-0001",
        "name": "违约金超额判定（占位）",
        "form": "expr",
        "body": "excess = max(0, penalty_rate - cap_rate)",
        "inputs": [{"name": "penalty_rate", "type": "integer", "constraint": "万分比占位"},
                   {"name": "cap_rate", "type": "integer", "constraint": ""}],
        "outputs": [{"name": "excess", "type": "integer"}],
        "precondition": "penalty_rate >= 0 and cap_rate >= 0",
        "kb_refs": ["term-0000"],
        "source_refs": ["term-0000"],
        "determinism": "strict",
        "rule_version": 1,
        "status": "active",
        "updated_at": "2026-11-08T00:00:00Z",
        "updated_by": "PLACEHOLDER_ACCOUNT",
    }
    rule.update(overrides)
    return rule


def _ids(kb):
    kb_ids = {k["entry_id"] for k in kb["layers"]["knowledge"]}
    src_ids = {s["entry_id"] for s in kb["layers"]["sources"]}
    return kb_ids, src_ids


class TestValidation:
    def test_valid_rule_passes(self):
        kb = _kb()
        errors = validate_rule(_expr_rule(), *_ids(kb))
        assert errors == []

    def test_bad_rule_id_format(self):
        kb = _kb()
        errors = validate_rule(_expr_rule(rule_id="rule-1"), *_ids(kb))
        assert any("rule_id" in e for e in errors)

    def test_dangling_kb_ref_rejected(self):
        kb = _kb()
        rule = _expr_rule(kb_refs=["term-9999"])
        errors = validate_rule(rule, *_ids(kb))
        assert any("悬空" in e for e in errors)

    def test_empty_kb_refs_rejected(self):
        kb = _kb()
        errors = validate_rule(_expr_rule(kb_refs=[]), *_ids(kb))
        assert any("非空" in e for e in errors)

    def test_non_strict_determinism_rejected(self):
        kb = _kb()
        errors = validate_rule(_expr_rule(determinism="best_effort"), *_ids(kb))
        assert any("strict" in e for e in errors)


class TestEvaluation:
    def test_expr_evaluation_ok(self):
        """验收核心：抽样规则可算出结果。"""
        result = evaluate_rule(_expr_rule(), {"penalty_rate": 50, "cap_rate": 30}, _kb())
        assert result["status"] == "ok"
        assert result["outputs"] == {"excess": 20}

    def test_expr_with_conditional_and_min(self):
        rule = _expr_rule(body="grade = 'high' if penalty_rate >= 80 else ('mid' if min(penalty_rate, 79) >= 40 else 'low')",
                          outputs=[{"name": "grade", "type": "string"}],
                          inputs=[{"name": "penalty_rate", "type": "integer", "constraint": ""}],
                          precondition="")
        result = evaluate_rule(rule, {"penalty_rate": 85}, _kb())
        assert result["outputs"] == {"grade": "high"}
        assert evaluate_rule(rule, {"penalty_rate": 10}, _kb())["outputs"] == {"grade": "low"}

    def test_precondition_false_not_applicable(self):
        """§5.1-3：precondition 不满足 → 统一 not_applicable（不随机失败）。"""
        result = evaluate_rule(_expr_rule(), {"penalty_rate": -5, "cap_rate": 30}, _kb())
        assert result["status"] == "not_applicable"
        assert result["outputs"] == {}
        assert "not_applicable" in result["evidence"]["note"]

    def test_table_hit_and_miss(self):
        rule = _expr_rule(
            form="table",
            body=json.dumps({"match_on": "term_kind",
                             "rows": [{"when": "late", "then": {"action": "计逾期利息（占位）"}},
                                      {"when": "breach", "then": {"action": "计违约金（占位）"}}]},
                            ensure_ascii=False),
            inputs=[{"name": "term_kind", "type": "enum", "constraint": ["late", "breach", "other"]}],
            outputs=[{"name": "action", "type": "string"}],
            precondition="")
        hit = evaluate_rule(rule, {"term_kind": "late"}, _kb())
        assert hit["outputs"] == {"action": "计逾期利息（占位）"}
        miss = evaluate_rule(rule, {"term_kind": "other"}, _kb())
        assert miss["status"] == "not_applicable"

    def test_formula_arithmetic(self):
        rule = _expr_rule(form="formula", body="half = cap_rate / 2",
                          outputs=[{"name": "half", "type": "integer"}])
        result = evaluate_rule(rule, {"penalty_rate": 0, "cap_rate": 30}, _kb())
        assert result["outputs"] == {"half": 15}

    def test_script_rejected_with_reason(self):
        """form=script 须沙箱评审（§5.1），本接口不放行并给明确原因。"""
        with pytest.raises(RuleError, match="沙箱评审"):
            evaluate_rule(_expr_rule(form="script", body="import os"), {}, _kb())

    def test_non_active_rejected(self):
        with pytest.raises(RuleError, match="active"):
            evaluate_rule(_expr_rule(status="draft"), {"penalty_rate": 1, "cap_rate": 0}, _kb())

    def test_input_type_closed(self):
        """类型封闭（§5.1-2）：缺/多/类型不符全拒。"""
        with pytest.raises(RuleError, match="缺声明输入"):
            evaluate_rule(_expr_rule(), {"penalty_rate": 1}, _kb())
        with pytest.raises(RuleError, match="多余输入"):
            evaluate_rule(_expr_rule(), {"penalty_rate": 1, "cap_rate": 1, "extra": 2}, _kb())
        with pytest.raises(RuleError, match="integer"):
            evaluate_rule(_expr_rule(), {"penalty_rate": "50", "cap_rate": 30}, _kb())

    def test_undeclared_output_rejected(self):
        with pytest.raises(RuleError, match="未在 outputs"):
            evaluate_rule(_expr_rule(body="ghost = penalty_rate - cap_rate"),
                          {"penalty_rate": 1, "cap_rate": 0}, _kb())

    def test_unsafe_syntax_rejected(self):
        with pytest.raises(RuleError, match="未放行"):
            evaluate_rule(_expr_rule(body="excess = __import__('os').getpid()"),
                          {"penalty_rate": 1, "cap_rate": 0}, _kb())


class TestTraceback:
    def test_evidence_resolves_to_raw_text(self):
        """验收核心：可算结果回指原文依据（evidence.sources 到 raw_text）。"""
        kb = _kb()
        result = evaluate_rule(_expr_rule(), {"penalty_rate": 50, "cap_rate": 30}, kb)
        sources = result["evidence"]["sources"]
        assert sources and sources[0]["raw_text"] == "12|违约金上限|不超过主合同本金 30%"
        assert sources[0]["origin_file"] == "terms.txt"
        assert result["evidence"]["kb_refs"] == ["term-0000"]

    def test_dangling_ref_rejected_on_evaluate(self):
        with pytest.raises(RuleError, match="悬空"):
            evaluate_rule(_expr_rule(kb_refs=["term-9999"]),
                          {"penalty_rate": 1, "cap_rate": 0}, _kb())

    def test_deterministic(self):
        one = json.dumps(evaluate_rule(_expr_rule(), {"penalty_rate": 50, "cap_rate": 30}, _kb()),
                         ensure_ascii=False, sort_keys=True)
        two = json.dumps(evaluate_rule(_expr_rule(), {"penalty_rate": 50, "cap_rate": 30}, _kb()),
                         ensure_ascii=False, sort_keys=True)
        assert one == two
