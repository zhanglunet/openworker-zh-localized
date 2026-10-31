# -*- coding: utf-8 -*-
"""PRD-267/T4 自测（trend #1338）：人 review 入库门——未 review 不可入库。

运行：python3 -m pytest tests/test_prd267_t4_intake.py -q

覆盖（T1 §3.4 / issue #1338 验收「未 review 不可入库，有测试」）：
  三条件门：review 签字（state=approved + reviewer/decided_at 非空）
  / 触发词冲突复检（重叠率 >0.5 拒，双向对称）/ Z 复扫（Z-1/Z-2 全半角覆盖再跑一遍）
  draft 态拒；approved 缺签字拒；冲突拒；三条件全过收（version 0.1.0）；
  原因可读（每个拒绝都带"为什么+怎么办"级中文说明）。
虚构纪律：审核人/时间戳/任务全虚构；不含真实主机名、账号、密钥。
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import zh_intake_gate as gate  # noqa: E402
import zh_skill_recorder as zr  # noqa: E402
from zh_skill_draft import draft_from_capture  # noqa: E402

SAYS = ["先点右上角那个齿轮图标", "然后把这个通知开关直接打开", "最后别忘了按下面保存按钮"]
APPROVED = {"state": "approved", "reviewer": "示例审核人", "decided_at": "2026-10-28T12:00:00Z"}


def build_capture(task="示例任务：配置示例通知"):
    cap = zr.new_capture("2026-10-28T10:00:00Z", "<USER>", task)
    for i, say in enumerate(SAYS, 1):
        cap = zr.add_step(cap, {"seq": i, "action_zh": f"示例动作{i}", "say_zh": say,
                                 "tool": "示例工具", "intent_zh": f"第{i}步意图"})
    return zr.finish_capture(cap, "三步完成示例")


def build_draft(name="示例通知配置", task="示例任务：配置示例通知"):
    return draft_from_capture(build_capture(task), name, "一句话：配置示例通知")


def approve(draft):
    """人 review 通过：签字后返回（模拟本地 diff review 的产物）。"""
    draft["frontmatter"]["review"] = dict(APPROVED)
    return draft


class TestGate(unittest.TestCase):
    def test_draft_state_rejected(self):
        """draft 态（未经 review）闸门硬拒——PRD 红线。"""
        result = gate.intake(build_draft(), [])
        self.assertFalse(result["admitted"])
        self.assertIn("approved", result["reason"])

    def test_approved_without_signature_rejected(self):
        """approved 但缺 reviewer / decided_at 签字仍拒。"""
        d = build_draft()
        d["frontmatter"]["review"] = {"state": "approved", "reviewer": "", "decided_at": "2026-10-28T12:00:00Z"}
        self.assertFalse(gate.intake(d, [])["admitted"])
        d["frontmatter"]["review"] = {"state": "approved", "reviewer": "示例审核人", "decided_at": ""}
        self.assertFalse(gate.intake(d, [])["admitted"])

    def test_trigger_conflict_rejected(self):
        """触发词与既有技能重叠率 >0.5 拒（防误唤起），双向对称。"""
        approved_a = approve(build_draft(name="技能甲"))
        draft_b = approve(build_draft(name="技能乙"))   # 同一 capture 归纳——触发词完全重叠
        result = gate.intake(draft_b, [approved_a["frontmatter"]["triggers"]])
        self.assertFalse(result["admitted"])
        self.assertIn("冲突", result["reason"])
        # 对称：先注册乙，未签字的甲同样撞车（撞在签字门，但冲突复检对已签者对称成立）
        draft_a = build_draft(name="技能甲")
        self.assertFalse(gate.intake(draft_a, [draft_b["frontmatter"]["triggers"]])["admitted"])
        # 已签字的甲与已入库的乙：触发词相同 → 冲突门拦（对称第二向）
        result2 = gate.intake(approve(build_draft(name="技能甲")),
                              [draft_b["frontmatter"]["triggers"]])
        self.assertFalse(result2["admitted"])
        self.assertIn("冲突", result2["reason"])

    def test_all_three_conditions_admitted(self):
        """review 签字齐全 + 无既有冲突 + Z 复扫干净 → admitted，version 从 0.1.0 起。"""
        result = gate.intake(approve(build_draft()), [])
        self.assertTrue(result["admitted"])
        self.assertEqual(result["version"], "0.1.0")
        # 既有技能触发词完全不同（不同任务、不同语料）也不冲突
        other_says = ["先打开示例文件夹窗口", "选中那个示例报表文件", "最后点导出按钮就可以了"]
        cap = zr.new_capture("2026-10-28T11:00:00Z", "<USER>", "示例任务：导出示例报表")
        for i, say in enumerate(other_says, 1):
            cap = zr.add_step(cap, {"seq": i, "action_zh": f"示例动作{i}", "say_zh": say,
                                     "tool": "示例工具", "intent_zh": f"第{i}步意图"})
        other = draft_from_capture(zr.finish_capture(cap, "导出完成示例"),
                                   "示例报表导出", "一句话：导出示例报表")
        result2 = gate.intake(approve(build_draft()), [other["frontmatter"]["triggers"]])
        self.assertTrue(result2["admitted"])

    def test_reasons_readable(self):
        """每个拒绝原因可读：说明卡在哪条 + 该怎么办。"""
        cases = [
            (gate.intake(build_draft(), []), "review"),
            (gate.intake(approve(build_draft()),
                         [build_draft()["frontmatter"]["triggers"]]), "冲突"),
            (gate.intake({**approve(build_draft()),
                          "body_markdown": "联系 １３９１２３４５６７８"}, []), "复扫"),
        ]
        for result, marker in cases:
            self.assertIn(marker, result["reason"])
            self.assertGreater(len(result["reason"]), 8)  # 不是干巴巴的 code

    def test_z_rescan_catches_tampered_body(self):
        """(c) Z 复扫：入库前正文夹带个人信息（全角手机号）仍被拦——草稿生成后篡改兜底。"""
        d = approve(build_draft())
        d["body_markdown"] += "\n联系电话 １３９１２３４５６７８（虚构示例）"
        result = gate.intake(d, [])
        self.assertFalse(result["admitted"])
        self.assertIn("复扫", result["reason"])
        self.assertIn("Z-1", result["reason"])

    def test_required_review_false_rejected(self):
        """required_review 非 true 的产物不配走门——配置即拒（门只服务 reviewed 草稿）。"""
        d = approve(build_draft())
        d["frontmatter"]["required_review"] = False
        self.assertFalse(gate.intake(d, [])["admitted"])

    def test_rescan_covers_frontmatter_too(self):
        """Z 复扫覆盖 frontmatter：description 夹带姓名称谓组合同样拦。"""
        d = approve(build_draft())
        d["frontmatter"]["description"] = "配置示例通知（找张经理那种）"
        result = gate.intake(d, [])
        self.assertFalse(result["admitted"])
        self.assertIn("Z-2", result["reason"])

    def test_deterministic_verdict(self):
        """同输入两次判定一致（确定性门）。"""
        d1, d2 = approve(build_draft()), approve(build_draft())
        self.assertEqual(gate.intake(d1, []), gate.intake(d2, []))


if __name__ == "__main__":
    unittest.main()
