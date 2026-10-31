# -*- coding: utf-8 -*-
"""PRD-267/T3 自测（trend #1337）：中文技能草稿 + 口语化触发词。

运行：python3 -m pytest tests/test_prd267_t3_draft.py -q

覆盖（T1 §3.3 / issue #1337 验收「草稿可触发演示」）：
  frontmatter 结构齐全（name/description/triggers/required_review/review/source）
  colloquial >=3 且逐条可溯源到 say_zh 原句；截取 8-24 字
  say_zh 不足时 action_zh 补足；语料不足拒绝（不编造口语）
  触发词冲突检查：重叠率 >0.5 双向判冲突；无重叠通过
  触发演示：canonical 与 colloquial 均可命中；无关话术不命中
  确定性：同输入两次产出逐字节一致
虚构纪律：任务/解说全虚构；不含真实主机名、账号、密钥。
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import zh_skill_draft as zsd  # noqa: E402
import zh_skill_recorder as zr  # noqa: E402


def build_capture(say_list, action_list=None):
    """走 T2 真实录制管线构造 capture（草稿只消费脱敏后的合法产物）。"""
    action_list = action_list or say_list
    cap = zr.new_capture("2026-10-28T10:00:00Z", "<USER>", "示例任务：配置示例通知")
    seqs = range(1, max(len(say_list), len(action_list)) + 1)
    for i, (say, action) in zip(seqs, _zip_pad(say_list, action_list)):
        cap = zr.add_step(cap, {"seq": i, "action_zh": action, "say_zh": say,
                                 "tool": "示例工具", "intent_zh": f"第{i}步意图"})
    return zr.finish_capture(cap, "三步完成示例")


def _zip_pad(a, b):
    la, lb = list(a), list(b)
    n = max(len(la), len(lb))
    return [(la[i] if i < len(la) else "", lb[i] if i < len(lb) else "") for i in range(n)]


SAYS = ["先点右上角那个齿轮图标", "然后把这个通知开关直接打开", "最后别忘了按下面保存按钮"]


class TestFrontmatter(unittest.TestCase):
    def setUp(self):
        self.draft = zsd.draft_from_capture(build_capture(SAYS),
                                            name="示例通知配置", description="一句话：配置示例通知")

    def test_structure_complete(self):
        fm = self.draft["frontmatter"]
        self.assertEqual(fm["name"], "示例通知配置")
        self.assertEqual(fm["description"], "一句话：配置示例通知")
        self.assertEqual(set(fm["triggers"]), {"canonical", "colloquial"})
        self.assertEqual(len(fm["triggers"]["canonical"]), 1)  # canonical 恰 1 条
        self.assertEqual(fm["source"], "recorded")
        self.assertEqual(fm["review"], {"state": "draft", "reviewer": "", "decided_at": ""})

    def test_required_review_true(self):
        self.assertIs(self.draft["frontmatter"]["required_review"], True)
        self.assertEqual(self.draft["frontmatter"]["review"]["state"], "draft")

    def test_colloquial_at_least_three_from_say_zh(self):
        colloquial = self.draft["frontmatter"]["triggers"]["colloquial"]
        self.assertGreaterEqual(len(colloquial), 3)
        blob = "".join(SAYS)  # 逐条溯源：均截取自 say_zh 原句
        for phrase in colloquial:
            self.assertIn(phrase, blob)
        self.assertTrue(all(p in blob for p in colloquial[:3]))  # 前 3 条优先 say_zh

    def test_excerpt_bounds_8_to_24(self):
        for phrase in self.draft["frontmatter"]["triggers"]["colloquial"]:
            self.assertTrue(8 <= len(phrase) <= 24, phrase)

    def test_canonical_from_task_words(self):
        self.assertEqual(self.draft["frontmatter"]["triggers"]["canonical"],
                         ["配置示例通知"])  # 去"示例任务："前缀归纳


class TestFillAndRefuse(unittest.TestCase):
    def test_fill_from_action_zh(self):
        """say_zh 只有 1 条可截时，从 action_zh 补足到 3 条。"""
        cap = build_capture(say_list=["这个开关一打开就行了", "", ""],
                            action_list=["打开示例通知设置页面", "开启示例通知开关", "保存示例通知配置"])
        colloquial = zsd.draft_from_capture(
            cap, name="示例技能", description="示例描述")["frontmatter"]["triggers"]["colloquial"]
        self.assertGreaterEqual(len(colloquial), 3)
        self.assertIn("打开示例通知设置页面", colloquial)  # action_zh 补足可溯源
        self.assertIn("开启示例通知开关", colloquial)

    def test_insufficient_corpus_refused(self):
        """语料不足 3 条：拒绝产出，不编造口语（T1 红线 4）。"""
        cap = build_capture(say_list=["就这一句话解说"], action_list=["短步骤"])
        with self.assertRaises(zsd.DraftRejected):
            zsd.draft_from_capture(cap, name="示例技能", description="示例描述")

    def test_bad_schema_refused(self):
        with self.assertRaises(zsd.DraftRejected):
            zsd.draft_from_capture({"schema": "other"}, name="x", description="y")


class TestConflict(unittest.TestCase):
    def setUp(self):
        self.a = {"canonical": ["配置示例通知"],
                  "colloquial": ["先点右上角那个齿轮图标", "然后把这个通知开关直接打开",
                                  "最后别忘了按下面保存按钮"]}
        self.same = {"canonical": ["配置示例通知"],
                     "colloquial": ["先点右上角那个齿轮图标", "然后把这个通知开关直接打开",
                                     "最后别忘了按下面保存按钮"]}
        self.other = {"canonical": ["导出示例报表"],
                      "colloquial": ["打开报表页面", "选好日期范围", "点导出按钮"]}

    def test_conflict_symmetric(self):
        self.assertTrue(zsd.trigger_conflict(self.a, self.same))
        self.assertTrue(zsd.trigger_conflict(self.same, self.a))  # 双向一致

    def test_no_conflict_passes(self):
        self.assertFalse(zsd.trigger_conflict(self.a, self.other))
        self.assertFalse(zsd.trigger_conflict(self.other, self.a))

    def test_partial_overlap_below_threshold(self):
        half = {"canonical": ["完全不同的话"],
                "colloquial": ["先点右上角那个齿轮图标", "选好日期范围", "打开报表页面"]}
        # 交集 1 / 并集 6 ≈ 0.17 < 0.5
        self.assertFalse(zsd.trigger_conflict(self.a, half))
        self.assertFalse(zsd.trigger_conflict(half, self.a))

    def test_empty_no_conflict(self):
        self.assertFalse(zsd.trigger_conflict({}, self.a))
        self.assertFalse(zsd.trigger_conflict({}, {}))


class TestTriggerDemo(unittest.TestCase):
    def setUp(self):
        self.draft = zsd.draft_from_capture(build_capture(SAYS),
                                            name="示例通知配置", description="配置示例通知")

    def test_canonical_hits(self):
        self.assertTrue(zsd.trigger_match(self.draft, "帮我做一下配置示例通知这件事"))

    def test_colloquial_hits(self):
        self.assertTrue(zsd.trigger_match(self.draft, "先点右上角那个齿轮图标在哪"))

    def test_unrelated_misses(self):
        self.assertFalse(zsd.trigger_match(self.draft, "帮我写一首关于秋天的诗"))


class TestDeterminism(unittest.TestCase):
    def test_deterministic_output(self):
        cap = build_capture(SAYS)
        d1 = zsd.draft_from_capture(cap, name="示例技能", description="示例描述")
        d2 = zsd.draft_from_capture(cap, name="示例技能", description="示例描述")
        self.assertEqual(d1, d2)
        self.assertEqual(zsd.render_markdown(d1), zsd.render_markdown(d2))

    def test_render_markdown_skill_md_shape(self):
        text = zsd.render_markdown(zsd.draft_from_capture(
            build_capture(SAYS), name="示例技能", description="示例描述"))
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("required_review: true", text)
        self.assertIn("source: \"recorded\"", text)
        self.assertIn("先点右上角那个齿轮图标", text)  # 口语语料保留在正文


if __name__ == "__main__":
    unittest.main()
