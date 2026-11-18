"""PRD-488/T2：openworker-zh-localized 中文技能包评估最小实现测试。

质量门 + 重叠检测的最小实现测试。断言值来自首份评估报告的真实跑分
（评估脚本按 skill-eval/inventory.json 的真实技能文本算出），不是拍脑袋的数。
"""

from __future__ import annotations

import sys
from pathlib import Path

MOD_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(MOD_DIR))

from skill_evaluation import (
    VERDICT_INSUFFICIENT,
    VERDICT_PASS,
    VERDICT_REMEDIATE,
    evaluate,
    gate_error_rate,
    load_inventory,
    render_report,
)

INVENTORY = Path(__file__).resolve().parents[1] / "skill-eval" / "inventory.json"


def test_inventory_loads() -> None:
    inv = load_inventory(INVENTORY)
    assert inv["prd"] == 488
    assert inv["repo"] == "openworker-zh-localized"
    assert len(inv["skills"]) == 12
    for skill in inv["skills"]:
        assert skill["id"] and skill["text"] and skill["source_path"]
        assert skill["metrics"]["sample_tasks"] == 0


def test_gate_verdicts_all_insufficient_evidence() -> None:
    report = evaluate(load_inventory(INVENTORY))
    assert report["skill_count"] == 12
    assert all(v["verdict"] == VERDICT_INSUFFICIENT for v in report["verdicts"])
    assert report["remediation_candidates"] == []


def test_overlap_real_numbers() -> None:
    report = evaluate(load_inventory(INVENTORY))
    assert report["pair_count"] == 66
    assert len(report["suspected"]) == 5
    if report["pairs"]:
        top = report["pairs"][0]
        assert top["similarity"] == 1.0
        assert (top["a"], top["b"]) == ('aws-posture', 'aws-posture@posture-worker')
    assert len(report["suspected"]) == 5


def test_gate_logic_boundaries() -> None:
    thresholds = {"min_sample_tasks": 20, "min_relative_error_drop": 0.20,
                  "max_new_error_types": 0, "overlap_similarity": 0.8}
    passing = {"sample_tasks": 20, "error_rate_with_skill": 0.08,
               "error_rate_without_skill": 0.10, "new_error_types": 0}
    assert gate_error_rate(passing, thresholds)[0] == VERDICT_PASS
    failing = {"sample_tasks": 20, "error_rate_with_skill": 0.09,
               "error_rate_without_skill": 0.10, "new_error_types": 0}
    assert gate_error_rate(failing, thresholds)[0] == VERDICT_REMEDIATE
    small_sample = {"sample_tasks": 5, "error_rate_with_skill": 0.08,
                    "error_rate_without_skill": 0.10, "new_error_types": 0}
    assert gate_error_rate(small_sample, thresholds)[0] == VERDICT_INSUFFICIENT
    no_runs = {"sample_tasks": 0, "error_rate_with_skill": None,
               "error_rate_without_skill": None, "new_error_types": None}
    assert gate_error_rate(no_runs, thresholds)[0] == VERDICT_INSUFFICIENT


def test_report_renders_with_real_numbers() -> None:
    report = evaluate(load_inventory(INVENTORY))
    text = render_report(report)
    assert "2026-11-17" in text
    assert VERDICT_INSUFFICIENT in text
    assert "证据不足不是失效" in text
    assert "1.000" in text
