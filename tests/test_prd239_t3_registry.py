# -*- coding: utf-8 -*-
"""PRD-239/T3 自测（trend #1197）：中文触发词登记册——口语收录与冲突处理。

运行：uv run --with pytest python -m pytest tests/test_prd239_t3_registry.py -q

覆盖（T1 §5，验收「登记册可用，口语触发可命中对应包」）：19 条种子全量入册
（§5.2 必填字段）、包覆盖（三场景包各 ≥1 条启用）、口语命中（整句精确/包含/
口语形差归一：全角标点与空白）、§5.4 裁决顺序（P0 产物名压 P1 句式、同级跨
技能 → ambiguous 待澄清可解释）、收录冲突处理（同触发词跨技能拒绝并列出冲突
对象、场景词同包多技能显式登记冲突标注）、停用留痕不删行、确定性。零网络。
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from zh_trigger_registry import (  # noqa: E402
    RegistrationError,
    build_registry,
    coverage,
    disable,
    lookup,
    normalize,
)


@pytest.fixture(scope="module")
def registry():
    return build_registry()


class TestRegistration:
    def test_19_seeds_plus_2_conflict_demos(self, registry):
        """§5.3 的 19 条种子逐句入册；另含 P0 产物名示范与 2 条场景词冲突示范。"""
        assert registry["total"] == 22
        assert registry["schema"] == "zh-trigger-registry/v1"
        seeds = ["帮我整理一下这家客户", "做个客户速览", "梳理一下决策链",
                 "把和他们的历史沟通整理成档案", "写一封跟进邮件",
                 "帮我起草一条跟进消息", "跟进上次沟通写点什么",
                 "看看这份合同有什么风险", "帮我过一遍条款", "标出对我不利的地方",
                 "这份合同还缺什么材料", "帮我核对签约要带的文件",
                 "有哪些时间节点要盯", "帮我写个 JD", "起草一份岗位说明",
                 "这个职位要招人了怎么写", "帮我准备面试问题", "出一份面试题纲",
                 "这场面试怎么评估"]
        phrases = {normalize(e["phrase"]) for e in registry["entries"]}
        for seed in seeds:
            assert normalize(seed) in phrases, f"种子缺失：{seed}"

    def test_entry_fields_complete(self, registry):
        for entry in registry["entries"]:
            for field in ("entry_id", "phrase", "type", "skill", "pack",
                          "priority", "conflict", "source", "status"):
                assert entry.get(field), f"{entry['entry_id']} 缺 {field}"
            assert entry["priority"] in ("P0", "P1", "P2", "P3")

    def test_pack_coverage_all_three(self, registry):
        """验收前提：三场景包各 ≥1 条启用触发词（登记册可用）。"""
        cov = coverage(registry)
        assert cov["ok"] is True
        assert set(cov["counts"]) == {"workplace", "legal-contract", "sales-marketing"}

    def test_duplicate_phrase_cross_skill_rejected(self):
        """收录冲突处理：同触发词登记到不同技能且未标注冲突 → 拒绝并列出冲突双方。"""
        from zh_trigger_registry import _entry as entry, check_conflicts
        good = build_registry()["entries"]
        check_conflicts(good)  # 现有登记册自身合法
        pair = [entry("TRG-X-001", "同一句话", "句式", "skill-a", "hr", "P1"),
                entry("TRG-X-002", "同一句话", "句式", "skill-b", "legal", "P1")]
        with pytest.raises(RegistrationError) as exc:
            check_conflicts(good + pair)
        assert "skill-a" in str(exc.value) and "skill-b" in str(exc.value)
        assert "人工消歧" in str(exc.value)
        # 已显式标注冲突与处理方式 → 放行
        annotated = [entry("TRG-X-003", "另一句", "场景词", "s-a", "hr", "P3",
                           conflict="跨包", conflict_targets=["TRG-X-004"],
                           resolution="待澄清"),
                     entry("TRG-X-004", "另一句", "场景词", "s-b", "legal", "P3",
                           conflict="跨包", conflict_targets=["TRG-X-003"],
                           resolution="待澄清")]
        check_conflicts(good + annotated)

    def test_conflict_entry_requires_targets_and_resolution(self):
        """冲突标注非「无」时，冲突对象与处理方式必填（§5.2 条件必填）。"""
        from zh_trigger_registry import _entry as entry
        with pytest.raises(RegistrationError, match="必填"):
            entry("TRG-X-003", "合同", "场景词", "s-a", "legal", "P3",
                  conflict="同包多技能")


class TestLookup:
    def test_exact_colloquial_hit(self, registry):
        """验收核心：口语触发可命中对应包——「帮我写个 JD」→ workplace/JD 草拟。"""
        result = lookup(registry, "帮我写个 JD")
        assert result["status"] == "hit"
        assert result["skill"] == "zh-hr-jd-draft"
        assert result["candidates"][0]["pack"] == "workplace"

    def test_product_word_priority_beats_sentence(self, registry):
        """P0 产物名命中压 P1 句式（§5.4 裁决顺序）。"""
        result = lookup(registry, "帮我做个客户速览")
        assert result["status"] == "hit"
        assert result["candidates"][0]["priority"] == "P0"
        assert result["skill"] == "zh-sales-lead-brief"

    def test_normalization_shape_tolerance(self, registry):
        """口语形差归一：全角标点/空白不影响命中。"""
        one = lookup(registry, "帮我写个JD")
        two = lookup(registry, "帮我写个 JD。")
        three = lookup(registry, "帮我写个 ＪＤ ？？")
        assert one["status"] == "hit" and two["status"] == "hit" and three["status"] == "hit"
        assert one["skill"] == three["skill"]

    def test_same_level_cross_skill_ambiguous(self, registry):
        """同级跨技能 → ambiguous 待澄清（误命中可解释：候选与原因可见）。"""
        result = lookup(registry, "合同")  # 场景词 P3 两条（同包两技能）
        assert result["status"] == "ambiguous"
        assert result["skill"] is None
        assert "待澄清" in result["reason"]
        assert len(result["candidates"]) == 2

    def test_miss_reported(self, registry):
        result = lookup(registry, "帮我订个机票")
        assert result["status"] == "miss"

    def test_priority_order_in_candidates(self, registry):
        """候选按 P0→P3 排序（可解释性）。"""
        result = lookup(registry, "帮我过一遍条款 做一份合同风险清单")
        priorities = [c["priority"] for c in result["candidates"]]
        assert priorities == sorted(priorities, key=lambda p: ("P0", "P1", "P2", "P3").index(p))


class TestDisableDeterminism:
    def test_disable_keeps_row_with_reason(self, registry):
        """停用不删行、原因必填；停用后不参与命中。"""
        work = json.loads(json.dumps(registry, ensure_ascii=False))
        entry = disable(work, "TRG-HR-001", "与新版 JD 技能合并（占位原因）")
        assert entry["status"] == "停用"
        assert "停用原因" in entry["note"]
        assert lookup(work, "帮我写个 JD")["status"] in ("miss", "ambiguous")
        with pytest.raises(RegistrationError, match="原因"):
            disable(work, "TRG-HR-002", "")

    def test_deterministic(self, registry):
        one = json.dumps(lookup(registry, "帮我准备面试问题"),
                         ensure_ascii=False, sort_keys=True)
        two = json.dumps(lookup(registry, "帮我准备面试问题"),
                         ensure_ascii=False, sort_keys=True)
        assert one == two

    def test_normalize_stable(self):
        assert normalize("帮我，写个 JD！") == normalize("帮我写个jd")
