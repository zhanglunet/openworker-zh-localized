# -*- coding: utf-8 -*-
"""PRD-239/T4 + PRD-240/T4 自测（trend #1198 / #1203）。

运行：uv run --no-project --with pytest python -m pytest tests/test_prd239_t4_pack_load.py tests/test_prd240_t4_consistency.py -q

239/T4：按包加载（现有使用方式不断链——目录形态加载不依赖登记资产）、
检索路径可用（子串 OR/短词拒绝/确定性）。
240/T4：三层对齐检查（E-DANGLING-REF/E-CIRCULAR-REF/E-ORPHAN-SOURCE、
不一致条目可检出并列出清单、对齐通过）。零网络；全合成。
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from pack_loader import SkillLoadError, load_skills_for_runtime, search_skills  # noqa: E402
from consistency_check import check_consistency  # noqa: E402


def _packs(tmp: Path):
    """合成 role-packs 目录（hr/jd + sales/brief 两技能）。"""
    for pack, skill, desc in (
        ("hr", "zh-hr-jd-draft", "帮我写个 JD（占位触发）"),
        ("sales", "zh-sales-lead-brief", "做个客户速览（占位触发）"),
    ):
        d = tmp / "role-packs" / pack / "skills" / skill
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(
            f"---\nname: {skill}\ndescription: {desc}\n---\n正文（占位）",
            encoding="utf-8")
    return tmp / "role-packs"


class TestPackLoad:
    def test_load_via_directory_form_no_registry_dependency(self, tmp_path):
        """现有使用方式不断链：只认目录形态（SKILL.md），不依赖登记册资产。"""
        root = _packs(tmp_path)
        entries = load_skills_for_runtime(root)
        assert {e["name"] for e in entries} == {"zh-hr-jd-draft",
                                                "zh-sales-lead-brief"}
        assert all(Path(e["path"]).is_file() for e in entries)

    def test_missing_root_raises(self, tmp_path):
        with pytest.raises(SkillLoadError, match="不存在"):
            load_skills_for_runtime(tmp_path / "ghost")

    def test_search_hits_and_short_reject(self, tmp_path):
        root = _packs(tmp_path)
        entries = load_skills_for_runtime(root)
        hits = search_skills(entries, "JD")
        assert len(hits) == 1 and hits[0]["name"] == "zh-hr-jd-draft"
        with pytest.raises(SkillLoadError, match="至少"):
            search_skills(entries, "J")

    def test_search_deterministic(self, tmp_path):
        root = _packs(tmp_path)
        entries = load_skills_for_runtime(root)
        assert search_skills(entries, "速览") == search_skills(entries, "速览")


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


class 三方对齐Tests:
    def test_aligned_three_layers_no_errors(self):
        """T2 迁移产物回指链完整 → 对齐（E-ORPHAN-SOURCE 提示级不算错误）。"""
        report = check_consistency(_three_layers())
        assert report["summary"]["errors"] == 0
        assert report["summary"]["aligned"] is True

    def test_dangling_kb_ref_detected(self):
        """规则 kb_ref 悬空 → E-DANGLING-REF 检出。"""
        layers = _three_layers()
        layers["layers"]["rules"][0]["kb_refs"] = ["term-9999"]
        report = check_consistency(layers)
        assert any(i["code"] == "E-DANGLING-REF" for i in report["issues"])

    def test_circular_ref_detected(self):
        """知识条目 → 规则反向引用 → E-CIRCULAR-REF（§6.2 禁止）。"""
        layers = _three_layers()
        layers["layers"]["knowledge"][0]["rule_ref"] = "term-0000"
        report = check_consistency(layers)
        assert any(i["code"] == "E-CIRCULAR-REF" for i in report["issues"])

    def test_orphan_source_listed_as_warning(self):
        """未被回指的原文 → E-ORPHAN-SOURCE 提示级（warning 不算 error）。"""
        layers = _three_layers()
        layers["layers"]["sources"].append(
            {"entry_id": "term-9999", "origin_file": "ghost.txt",
             "line_number": 1, "raw_text": "孤儿原文（占位）"})
        report = check_consistency(layers)
        assert report["summary"]["warnings"] >= 1
        assert any(i["code"] == "E-ORPHAN-SOURCE" for i in report["issues"])

    def test_issue_list_machine_readable(self):
        """不一致条目可被检出并列出清单（验收）：issues 每条含 code/location/detail。"""
        layers = _three_layers()
        layers["layers"]["rules"][0]["kb_refs"] = ["term-9999"]
        report = check_consistency(layers)
        for issue in report["issues"]:
            assert {"code", "location", "detail"} <= set(issue)
        assert report["schema"] == "three-layer-consistency/v1"
