# -*- coding: utf-8 -*-
"""PRD-239/T5 测试：验收试运行——中文口语指令抽样（trend #1199）。

运行：uv run --no-project --with pytest python -m pytest tests/test_prd239_t5_utterance_sample.py -q
（或 python3 -m unittest tests.test_prd239_t5_utterance_sample -v）

验收标准（trend #1199）：**抽样口语指令命中率达标，误命中可解释**。

抽样（真实登记册 22 条种子 × 真实 role-packs 六技能，全合成占位口语）：
  ① 命中样本×8（P0 产物词整句/句式嵌长句/跨包覆盖三包）→ 全部命中预期
    技能（命中率 8/8 达标）；
  ② 误命中可解释：裸场景词「合同」→ ambiguous + reason 带候选技能与
    「待澄清，不由登记册硬判」（不静默硬判）；无关口语 → miss 不硬凑；
  ③ 口语命中 ↔ 按包加载衔接：命中的每个技能都能在 role-packs 真实目录
    由 load_skills_for_runtime 加载到运行时菜单（登记↔目录零断链）；
  ④ 确定性：同抽样重跑逐项一致。
零网络；发行侧登记资产 + 目录形态加载（诚实边界：登记册非运行时引擎）。
"""
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from pack_loader import load_skills_for_runtime  # noqa: E402
from zh_trigger_registry import build_registry, coverage, lookup  # noqa: E402

#: 口语指令抽样表（§5.3/§5.4 口径；占位口语）
SAMPLE = [
    # (utterance, expected_status, expected_skill)
    ("做个客户速览", "hit", "zh-sales-lead-brief"),                      # P0 产物词整句
    ("帮我整理一下这家客户的情况", "hit", "zh-sales-lead-brief"),        # 句式嵌长句
    ("把和他们的历史沟通整理成档案，下周要用", "hit", "zh-sales-lead-brief"),
    ("帮我起草一条跟进消息给对方", "hit", "zh-sales-followup-draft"),
    ("看看这份合同有什么风险", "hit", "zh-contract-risk-list"),
    ("标出对我不利的地方", "hit", "zh-contract-risk-list"),
    ("这份合同还缺什么材料", "hit", "zh-legal-doc-checklist"),
    ("帮我核对签约要带的文件", "hit", "zh-legal-doc-checklist"),
    # 误命中/歧义样本（可解释性）
    ("合同", "ambiguous", None),                                         # 裸场景词：同级跨技能
    ("帮我订一张去北京的机票", "miss", None),                            # 无关口语不硬凑
]


class 口语抽样Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = build_registry()
        cls.results = [(u, lookup(cls.registry, u)) for u, _s, _k in SAMPLE]

    def test_registry_and_coverage_ready(self):
        """前置：登记册构建成功、三包覆盖 ok。"""
        cov = coverage(self.registry)
        self.assertTrue(cov["ok"], cov)
        self.assertEqual(cov["missing_packs"], [])

    def test_hit_rate_target_met(self):
        """验收①：命中样本 8/8 全中预期技能（命中率达标）。"""
        designed_hits = [s for s in SAMPLE if s[1] == "hit"]
        self.assertEqual(len(designed_hits), 8)
        for utterance, expect, skill in SAMPLE:
            if expect != "hit":
                continue
            result = lookup(self.registry, utterance)
            self.assertEqual(result["status"], "hit", (utterance, result))
            self.assertEqual(result["skill"], skill, utterance)
            self.assertTrue(result["candidates"])               # 命中带候选可溯

    def test_misfires_explainable(self):
        """验收②误命中可解释：裸场景词 ambiguous 带候选与待澄清 reason；
        无关口语 miss 不硬凑。"""
        for utterance, expect, _skill in SAMPLE:
            if expect == "hit":
                continue
            result = lookup(self.registry, utterance)
            self.assertEqual(result["status"], expect, (utterance, result))
            if expect == "ambiguous":
                self.assertTrue(result.get("reason"))
                self.assertIn("待澄清", result["reason"])
                self.assertGreaterEqual(len(result["candidates"]), 2)
                skills = {c["skill"] for c in result["candidates"]}
                self.assertGreaterEqual(len(skills), 2)         # 跨技能歧义显形
            if expect == "miss":
                self.assertEqual(result["candidates"], [])
                self.assertIsNone(result["skill"])

    def test_hits_loadable_from_role_packs(self):
        """③ 衔接：命中技能全部能由 role-packs 目录加载到运行时菜单。"""
        entries = load_skills_for_runtime(REPO / "role-packs")
        by_name = {e["name"]: e for e in entries}
        for utterance, expect, skill in SAMPLE:
            if expect != "hit":
                continue
            self.assertIn(skill, by_name, f"{skill} 不在运行时菜单（登记↔目录断链）")
            self.assertTrue(by_name[skill]["description"])
        # 六技能全量可加载（登记册 skills ⊆ 运行时菜单）
        registry_skills = {e["skill"] for e in self.registry["entries"]
                           if e["status"] == "启用"}
        self.assertTrue(registry_skills <= set(by_name))

    def test_deterministic(self):
        """④ 确定性：同抽样重跑，逐项 status/skill/reason 一致。"""
        first = [(lookup(self.registry, u)["status"],
                  lookup(self.registry, u).get("skill"),
                  lookup(self.registry, u).get("reason")) for u, _s, _k in SAMPLE]
        second = [(lookup(self.registry, u)["status"],
                   lookup(self.registry, u).get("skill"),
                   lookup(self.registry, u).get("reason")) for u, _s, _k in SAMPLE]
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
