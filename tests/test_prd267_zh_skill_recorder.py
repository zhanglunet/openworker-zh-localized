# -*- coding: utf-8 -*-
"""PRD-267/T2 自测（trend #1336）：中文实操录制——白名单/Z-1~Z-4 脱敏/回放/CLI。

运行：python3 -m pytest tests/test_prd267_zh_skill_recorder.py -q

覆盖（T1 §3.1/§3.2）：
  say_zh 口语解说字段在模型中（口语语料来源）
  值类禁录字段出现即失败；多余字段丢弃+告警
  Z-1 全半角手机号均阻断；Z-2 姓名称谓阻断；Z-3 用户名路径替换；Z-4 内部词替换
  样例回放：虚构中文任务全流程；最终自检；确定性；CLI 0/2

虚构纪律：任务/解说全虚构；密钥样例占位形态；不含真实主机名、账号。
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import zh_skill_recorder as zr  # noqa: E402


def base_step(**over):
    step = {"seq": 1, "action_zh": "打开示例设置页", "say_zh": "先点右上角那个齿轮",
            "tool": "示例工具", "intent_zh": "进入设置入口"}
    step.update(over)
    return step


class TestWhitelist(unittest.TestCase):
    def test_say_zh_in_model(self):
        cap = zr.new_capture("2026-10-28T10:00:00Z", "<USER>", "示例任务：配置示例通知")
        cap = zr.add_step(cap, base_step())
        self.assertEqual(cap["steps"][0]["say_zh"], "先点右上角那个齿轮")

    def test_value_fields_forbidden(self):
        cap = zr.new_capture("2026-10-28T10:00:00Z", "<USER>", "示例任务")
        for bad in ({"path": "/home/u/示例"}, {"account": "demo"}, {"value": "任意值"}):
            with self.assertRaises(zr.CaptureBlocked) as ctx:
                zr.add_step(cap, base_step(**bad))
            self.assertEqual(ctx.exception.rule, "FORBIDDEN")

    def test_extra_field_dropped(self):
        cap = zr.new_capture("2026-10-28T10:00:00Z", "<USER>", "示例任务")
        cap = zr.add_step(cap, base_step(browser_note="额外"))
        self.assertTrue(any("browser_note" in w for w in cap["_warnings"]))


class TestDesensitization(unittest.TestCase):
    def test_z1_halfwidth_phone_blocked(self):
        cap = zr.new_capture("2026-10-28T10:00:00Z", "<USER>", "示例任务")
        with self.assertRaises(zr.CaptureBlocked) as ctx:
            zr.add_step(cap, base_step(say_zh="打 13812345678 这个电话"))
        self.assertEqual(ctx.exception.rule, "Z-1")

    def test_z1_fullwidth_phone_blocked(self):
        cap = zr.new_capture("2026-10-28T10:00:00Z", "<USER>", "示例任务")
        fullwidth = "１３８１２３４５６７８"
        with self.assertRaises(zr.CaptureBlocked) as ctx:
            zr.add_step(cap, base_step(say_zh=f"号码是 {fullwidth}"))
        self.assertEqual(ctx.exception.rule, "Z-1")

    def test_z2_name_title_blocked(self):
        cap = zr.new_capture("2026-10-28T10:00:00Z", "<USER>", "示例任务")
        with self.assertRaises(zr.CaptureBlocked) as ctx:
            zr.add_step(cap, base_step(say_zh="发给王经理审批"))
        self.assertEqual(ctx.exception.rule, "Z-2")

    def test_z3_username_path_replaced(self):
        cap = zr.new_capture("2026-10-28T10:00:00Z", "<USER>", "示例任务")
        cap = zr.add_step(cap, base_step(action_zh="打开 /home/xiaoming/示例 文件夹"))
        self.assertIn("/home/<USER>", cap["steps"][0]["action_zh"])
        self.assertNotIn("xiaoming", json.dumps(cap, ensure_ascii=False))

    def test_z4_internal_replaced(self):
        cap = zr.new_capture("2026-10-28T10:00:00Z", "<USER>", "示例任务")
        cap = zr.add_step(cap, base_step(intent_zh="同步到内部系统"))
        self.assertIn("<INTERNAL>", cap["steps"][0]["intent_zh"])


class TestReplay(unittest.TestCase):
    def test_full_replay(self):
        cap = zr.new_capture("2026-10-28T10:00:00Z", "<USER>", "示例任务：配置示例通知")
        cap = zr.add_step(cap, base_step())
        cap = zr.add_step(cap, base_step(seq=2, action_zh="开启通知开关", say_zh="然后把这个开关打开",
                                          intent_zh="完成配置"))
        cap = zr.finish_capture(cap, "两步完成")
        blob = zr.dump_capture(cap)
        parsed = json.loads(blob)
        self.assertEqual(parsed["schema"], "zh-capture-v1")
        self.assertEqual(len(parsed["steps"]), 2)
        self.assertIn("先点右上角那个齿轮", blob)  # 口语语料保留（供触发词归纳）
        self.assertEqual(zr.dump_capture(cap), blob)

    def test_final_selfcheck_blocked(self):
        cap = zr.new_capture("2026-10-28T10:00:00Z", "<USER>", "示例任务")
        cap = zr.add_step(cap, base_step())
        cap["steps"][0]["say_zh"] = "发给李（经理）确认"
        with self.assertRaises(zr.CaptureBlocked) as ctx:
            zr.finish_capture(cap, "done")
        self.assertEqual(ctx.exception.rule, "Z-2")


class TestCli(unittest.TestCase):
    def _run(self, payload):
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "in.json"
            out = Path(tmp) / "out.json"
            inp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts" / "zh_skill_recorder.py"),
                 "record", str(inp), str(out)],
                capture_output=True, text=True)
            out_text = out.read_text(encoding="utf-8") if out.exists() else None
            return proc, out_text

    def test_cli_ok_exit0(self):
        proc, out = self._run({
            "captured_at": "2026-10-28T10:00:00Z", "user": "<USER>",
            "task_summary": "示例任务", "steps": [base_step()], "summary": "完成",
        })
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIsNotNone(out)

    def test_cli_blocked_exit2(self):
        proc, out = self._run({
            "captured_at": "2026-10-28T10:00:00Z", "user": "<USER>",
            "task_summary": "示例任务", "steps": [base_step(say_zh="找张工看一下")], "summary": "完成",
        })
        self.assertEqual(proc.returncode, 2)
        self.assertIn("Z-2", proc.stderr)
        self.assertIsNone(out)


if __name__ == "__main__":
    unittest.main()
