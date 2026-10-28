# -*- coding: utf-8 -*-
"""PRD-267/T5 验收试运行（trend #1339）：虚构中文任务→技能。

运行：python3 -m pytest tests/test_prd267_acceptance.py -q

验收标准（issue #1339 / T1 §5 T5）：
  本地处理（零网络断言）；无密钥（扫描 0 命中）；触发词可用
  （trigger_match 命中 canonical 与 colloquial、无关话术不命中）；
  虚构中文任务回放时间线（say_zh 在场）；Z-1 全角手机号阻断；
  草稿 triggers canonical+colloquial>=3；未 review 入库拒；三条件过收。

虚构纪律：任务/话术/审核人全虚构；不含真实主机名、账号、密钥。
"""
import ast
import json
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import zh_intake_gate as gate  # noqa: E402
import zh_skill_recorder as zr  # noqa: E402
import zh_skill_draft as zd  # noqa: E402

DEVLOG = REPO / "docs" / "devlog" / "2026-10-28-prd-267-t5-acceptance.md"

# 虚构中文任务时间线（示例周报归档；话术全为演示口语）
TASK = "示例任务：把示例周报按周归档"
TIMELINE = [
    {"seq": 1, "action_zh": "打开归档页", "say_zh": "先打开示例归档页面右上角的入库按钮",
     "tool": "示例浏览器", "intent_zh": "进入归档入口"},
    {"seq": 2, "action_zh": "勾选周报", "say_zh": "然后选上这个月的三份示例周报",
     "tool": "示例浏览器", "intent_zh": "选定归档对象"},
    {"seq": 3, "action_zh": "确认入库", "say_zh": "最后按归档就能入库了别忘了核对清单",
     "tool": "示例浏览器", "intent_zh": "完成归档"},
]
APPROVED = {"state": "approved", "reviewer": "示例审核人", "decided_at": "2026-10-28T12:00:00Z"}


def record_capture(task=TASK, timeline=TIMELINE):
    """T2 录制：虚构中文任务 → zh-capture-v1 时间线。"""
    cap = zr.new_capture("2026-10-28T10:00:00Z", "<USER>", task)
    for step in timeline:
        cap = zr.add_step(cap, dict(step))
    return zr.finish_capture(cap, "三步归档完成（虚构演示）")


def build_draft(task=TASK, timeline=TIMELINE, name="示例周报归档"):
    return zd.draft_from_capture(record_capture(task, timeline), name, "一句话：把示例周报按周归档")


class TestFictionalTaskTimelineReplay(unittest.TestCase):
    """验收：虚构中文任务回放时间线（say_zh 在场）。"""

    def test_timeline_recorded_and_replayed_in_order(self):
        cap = record_capture()
        self.assertEqual(cap["schema"], "zh-capture-v1")
        steps = sorted(cap["steps"], key=lambda s: s["seq"])
        self.assertEqual([s["seq"] for s in steps], [1, 2, 3])
        # say_zh 在场：每步都带原句口语，且与时间线逐字一致（回放不丢不改）
        for step, src in zip(steps, TIMELINE):
            self.assertTrue(step.get("say_zh"), "每步必须有 say_zh 口语字段")
            self.assertEqual(step["say_zh"], src["say_zh"])
        # 录制产物（落盘形态）say_zh 在场
        blob = zr.dump_capture(cap)
        for src in TIMELINE:
            self.assertIn(src["say_zh"], blob)

    def test_draft_to_render_full_pipeline_deterministic(self):
        draft = build_draft()
        a, b = zd.render_markdown(draft), zd.render_markdown(draft)
        self.assertEqual(a, b)  # 确定性
        self.assertIn("先打开示例归档页面右上角的入库按钮", a)  # say_zh 在场于成稿


class TestZ1FullWidthPhoneBlocked(unittest.TestCase):
    """验收：Z-1 全角手机号阻断（全半角归一覆盖）。"""

    def test_full_width_phone_blocked_at_capture(self):
        with self.assertRaises(zr.CaptureBlocked) as ctx:
            zr.new_capture("2026-10-28T10:00:00Z", "<USER>",
                           "示例任务：回拨示例用户１３９１２３４５６７８")
        self.assertEqual(ctx.exception.rule, "Z-1")
        # 半角同形同样阻断（归一后同源）
        with self.assertRaises(zr.CaptureBlocked) as ctx2:
            zr.new_capture("2026-10-28T10:00:00Z", "<USER>", "示例任务：回拨 13912345678")
        self.assertEqual(ctx2.exception.rule, "Z-1")

    def test_step_say_zh_z1_also_blocked(self):
        cap = zr.new_capture("2026-10-28T10:00:00Z", "<USER>", TASK)
        with self.assertRaises(zr.CaptureBlocked):
            zr.add_step(cap, {"seq": 1, "action_zh": "示例动作", "tool": "示例工具",
                              "intent_zh": "示例意图", "say_zh": "打示例电话１５９００００００００"})


class TestTriggersShape(unittest.TestCase):
    """验收：草稿 triggers canonical+colloquial>=3。"""

    def test_canonical_exactly_one_and_colloquial_at_least_three(self):
        draft = build_draft()
        triggers = draft["frontmatter"]["triggers"]
        self.assertEqual(len(triggers["canonical"]), 1)
        self.assertGreaterEqual(len(triggers["colloquial"]), 3)
        self.assertEqual(triggers["canonical"][0], "把示例周报按周归档")
        # required_review 红线在场
        self.assertTrue(draft["frontmatter"]["required_review"])
        self.assertEqual(draft["frontmatter"]["review"]["state"], "draft")
        # colloquial 取自真实 say_zh 语料（不编造）
        for phrase in triggers["colloquial"]:
            self.assertTrue(any(phrase in s["say_zh"] for s in TIMELINE),
                            f"口语触发词须来自 say_zh 原句: {phrase}")


class TestTriggerMatchDemo(unittest.TestCase):
    """验收：触发演示——命中 canonical 与一条 colloquial；无关话术不命中。"""

    def test_canonical_colloquial_hit_and_unrelated_miss(self):
        draft = build_draft()
        canonical = draft["frontmatter"]["triggers"]["canonical"][0]
        colloquial = draft["frontmatter"]["triggers"]["colloquial"]
        self.assertTrue(zd.trigger_match(draft, f"帮我{canonical}"))            # canonical 命中
        self.assertTrue(zd.trigger_match(draft, f"{colloquial[0]}就行"))        # colloquial 命中
        self.assertFalse(zd.trigger_match(draft, "今天中午吃什么好"))            # 无关话术不命中
        self.assertFalse(zd.trigger_match(draft, "帮我订个示例会议室"))           # 无关话术不命中


class TestIntakeGate(unittest.TestCase):
    """验收：未 review 入库拒；三条件过收。"""

    def test_draft_state_rejected(self):
        draft = build_draft()
        result = gate.intake(draft, existing_triggers_list=[])
        self.assertFalse(result["admitted"])
        self.assertIn("approved", result["reason"])

    def test_missing_signature_rejected(self):
        draft = build_draft()
        draft["frontmatter"]["review"] = {"state": "approved", "reviewer": "", "decided_at": ""}
        result = gate.intake(draft, [])
        self.assertFalse(result["admitted"])

    def test_trigger_conflict_rejected(self):
        draft = build_draft()
        draft["frontmatter"]["review"] = dict(APPROVED)
        twin = build_draft()["frontmatter"]["triggers"]  # 同任务再产一份 → 触发词高度重叠
        result = gate.intake(draft, existing_triggers_list=[twin])
        self.assertFalse(result["admitted"])
        self.assertIn("冲突", result["reason"])

    def test_three_conditions_pass_admitted(self):
        draft = build_draft()
        draft["frontmatter"]["review"] = dict(APPROVED)
        other = {"canonical": ["完全无关的任务词"], "colloquial": ["另一件不相关的小事流程"]}
        result = gate.intake(draft, existing_triggers_list=[other])
        self.assertTrue(result["admitted"], result)
        self.assertEqual(result["version"], "0.1.0")
        # 入库后成稿 review 态为 approved（人 review 红线闭环）
        self.assertEqual(draft["frontmatter"]["review"]["state"], "approved")


class TestLocalOnlyAndNoSecrets(unittest.TestCase):
    """验收：本地零网络断言；密钥扫描。"""

    def test_modules_import_no_network_local_only(self):
        allowed = {"json", "re", "sys", "unicodedata", "pathlib", "typing", "__future__",
                   "zh_skill_draft", "zh_skill_recorder"}  # 本地模块间引用
        banned = {"socket", "urllib", "http", "requests", "httpx", "ssl", "ftplib",
                  "smtplib", "subprocess", "asyncio"}
        for mod in ("zh_skill_recorder.py", "zh_skill_draft.py", "zh_intake_gate.py"):
            src = (REPO / "scripts" / mod).read_text(encoding="utf-8")
            imported = set()
            for node in ast.walk(ast.parse(src)):
                if isinstance(node, ast.Import):
                    imported.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            self.assertFalse(imported & banned, f"{mod} 检出网络/进程模块: {imported & banned}")
            self.assertTrue(imported <= allowed, f"{mod} 出现白名单外依赖: {imported - allowed}")

    def test_no_secrets_in_modules_tests_devlog(self):
        secret_re = re.compile(
            r"sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|Bearer\s+[A-Za-z0-9._-]{16,}"
            r"|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----")
        lan_re = re.compile(r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b")
        targets = [REPO / "scripts" / n for n in
                   ("zh_skill_recorder.py", "zh_skill_draft.py", "zh_intake_gate.py")]
        targets += [Path(__file__), DEVLOG]
        for path in targets:
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(secret_re.search(text), f"{path.name} 检出密钥形态")
            self.assertIsNone(lan_re.search(text), f"{path.name} 检出内网主机名形态")
            # 成稿形态同样零密钥（草稿渲染产物扫描）
        rendered = zd.render_markdown(build_draft())
        self.assertIsNone(secret_re.search(rendered))
        self.assertIsNone(lan_re.search(rendered))


if __name__ == "__main__":
    unittest.main()
