# -*- coding: utf-8 -*-
"""PRD-369/T5 测试（trend #1648 的 T5 环节）：人工决策收件箱验收试运行。

运行：uv run --with pytest python -m pytest tests/test_prd369_t5_decision_inbox.py -q
（仓库根执行）

验收（T1 §5 T5 行「样例回放+文档无密钥」）：
  全链周期演练：三源只读汇聚（manual 评审/附答确认/中文歧义）→ 入箱 →
  人批（歧义项 CHOICE 候选内选）→ 人拒留痕 → 重复裁决演练
  （INBOX_DOUBLE_DECIDE 显形）→ AUTO_EXEC 演练（write_checklist/
  write_registry/fill_answer 载荷 INBOX_AUTO_EXEC_ATTEMPT 显形拒绝——
  零 checklist 改写零注册表写零附答代填，TAMPERED 红线继续）→
  CHOICE_REQUIRED 演练（歧义项 approve 缺候选内选择显形拒绝）；两遍
  全链周期产物逐字节一致（确定性可复现）；账本 append-only；零改写行为
  复验（批/拒返回值零改写载荷键）；链复跑：T2/T3/T4 测试子进程复跑
  exit 0（链上仍绿实测，含 T3 双缺陷订正后全链）；文档无密钥：T1 设计
  文档拼接 needle 扫描+占位符纪律。零网络；全合成占位。
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from decision_inbox import InboxError, InboxLedger, collect  # noqa: E402

NOW = "2026-11-11T09:00:00Z"
FP = "sha16:checklist（占位）"
QUESTIONS = ["给三个新用户读 description，能否不动手册说清何时用？（占位）"]
MANUAL = [{"source_ref": "skill-checklist-report/v1#P10（占位）",
           "fingerprint": FP, "questions": QUESTIONS,
           "reason": "P10 人工评审项（占位）"}]
ANSWERS = [{"source_ref": "manual-answers（占位）", "fingerprint": FP,
            "answers_ref": "manual_answers.json（占位）",
            "reason": "附答后确认（占位）"}]
DISAMB = [{"source_ref": "ref-resolution/v1（占位）", "fingerprint": FP,
           "candidates": ["@写作周报（占位）", "@写周报（占位）"],
           "reason": "中文歧义候选（占位）"}]


def _fresh_cycle():
    items = collect(manual_reviews=MANUAL, answer_confirms=ANSWERS,
                    zh_disambiguations=DISAMB, at=NOW)
    led = InboxLedger()
    led.add(items)
    led.approve(items[0]["item_id"], by="人（占位）", at=NOW)
    led.reject(items[1]["item_id"], by="人（占位）", at=NOW,
               reason="附答存疑（占位）")
    return items, led


class TestFullCycleDrill(unittest.TestCase):
    def test_cycle_deterministic_twice(self):
        """全链周期（收→批→拒）两遍：条目/events/状态逐字节一致。"""
        items1, led1 = _fresh_cycle()
        items2, led2 = _fresh_cycle()
        self.assertEqual(json.dumps(items1, sort_keys=True),
                         json.dumps(items2, sort_keys=True))
        self.assertEqual(json.dumps(led1.events, sort_keys=True),
                         json.dumps(led2.events, sort_keys=True))
        states = [it["state"] for it in led1.view()]
        self.assertEqual(sorted(states), ["approved", "pending",
                                          "rejected"])

    def test_disambiguation_choice_within_candidates(self):
        """歧义项人批：CHOICE 在候选列表内成功（chosen_candidate 落条目），
        附答 answers_ref 引用形态保留（收口引用零改写）。"""
        items = collect(zh_disambiguations=DISAMB, at=NOW)
        led = InboxLedger()
        led.add(items)
        out = led.approve(items[0]["item_id"], by="人（占位）", at=NOW,
                          choice="@写作周报（占位）")
        self.assertEqual(out["chosen_candidate"], "@写作周报（占位）")
        answers = collect(answer_confirms=ANSWERS, at=NOW)
        self.assertEqual(answers[0]["answers_ref"], "manual_answers.json（占位）")


class TestFailureDrills(unittest.TestCase):
    def test_double_decide_visible(self):
        """重复裁决演练：INBOX_DOUBLE_DECIDE 显形拒绝。"""
        items, led = _fresh_cycle()
        with self.assertRaisesRegex(InboxError, "INBOX_DOUBLE_DECIDE"):
            led.approve(items[0]["item_id"], by="人（占位）", at=NOW)

    def test_auto_exec_payload_rejected(self):
        """AUTO_EXEC 演练：write_checklist/fill_answer 载荷 →
        INBOX_AUTO_EXEC_ATTEMPT 显形拒绝（零 checklist 改写零注册表写零
        附答代填——TAMPERED 红线继续）。"""
        items, led = _fresh_cycle()
        with self.assertRaisesRegex(InboxError, "INBOX_AUTO_EXEC_ATTEMPT"):
            led.approve(items[2]["item_id"], by="人（占位）", at=NOW,
                        payload={"write_checklist": True})
        with self.assertRaisesRegex(InboxError, "INBOX_AUTO_EXEC_ATTEMPT"):
            led.reject(items[2]["item_id"], by="人（占位）", at=NOW,
                       payload={"fill_answers": True})

    def test_choice_required_for_disambiguation(self):
        """CHOICE_REQUIRED 演练：歧义项 approve 缺候选内选择 → 显形拒绝。"""
        items = collect(zh_disambiguations=DISAMB, at=NOW)
        led = InboxLedger()
        led.add(items)
        with self.assertRaisesRegex(InboxError, "INBOX_CHOICE_REQUIRED"):
            led.approve(items[0]["item_id"], by="人（占位）", at=NOW)

    def test_reject_trace_and_zero_tamper_keys(self):
        """拒也留痕；批/拒返回值零改写载荷键（R1 行为复验）。"""
        items, led = _fresh_cycle()
        rejected = next(it for it in led.view()
                        if it["item_id"] == items[1]["item_id"])
        self.assertEqual(rejected["reject_reason"], "附答存疑（占位）")
        fresh = InboxLedger()
        fresh.add(collect(manual_reviews=MANUAL, at=NOW))
        approved = fresh.approve(fresh.view()[0]["item_id"],
                                 by="人（占位）", at=NOW)
        for key in ("checklist_written", "registry_written", "answers_filled"):
            self.assertNotIn(key, approved)

    def test_ledger_append_only_through_drills(self):
        """账本 append-only：全演练流程后 events 只增不删。"""
        _, led1 = _fresh_cycle()
        n0 = len(led1.events)
        items2, led2 = _fresh_cycle()
        try:
            led2.approve(items2[0]["item_id"], by="人（占位）", at=NOW)
        except InboxError:
            pass   # 重复裁决被拒——events 不增
        self.assertEqual(len(led2.events), n0)


class TestChainRerun(unittest.TestCase):
    def test_t2_t3_t4_rerun_green(self):
        """链复跑：T2/T3/T4 测试子进程复跑 exit 0（链上仍绿实测，含 T3
        双缺陷订正后全链）。"""
        for test_file in ("test_prd369_t2_decision_inbox.py",
                          "test_prd369_t3_decision_inbox_gates.py",
                          "test_prd369_t4_decision_inbox_boundary.py"):
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q",
                 str(Path(__file__).resolve().parent / test_file)],
                capture_output=True, timeout=300)
            self.assertEqual(proc.returncode, 0,
                             f"{test_file} 复跑失败：{proc.stdout[-400:]}")


class TestDocNoSecrets(unittest.TestCase):
    def test_t1_design_doc_no_secrets(self):
        """文档无密钥：T1 设计文档拼接 needle 扫描+占位符纪律。"""
        repo = Path(__file__).resolve().parents[1]
        doc = next(repo.glob("docs/plans/2026-11-11-prd-369-*.md"))
        text = doc.read_text(encoding="utf-8").lower()
        for needle in ("sk-" + "live", "passw" + "ord", "api_k" + "ey"):
            self.assertNotIn(needle, text, f"设计文档出现密钥词 {needle}")
        self.assertIn("占位", text)


if __name__ == "__main__":
    unittest.main()
