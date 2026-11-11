# -*- coding: utf-8 -*-
"""PRD-369/T4 测试（trend #1648 的 T4 环节）：人工决策收件箱划界断言。

运行：uv run --with pytest python -m pytest tests/test_prd369_t4_decision_inbox_boundary.py -q
（仓库根执行）

覆盖（T1 §0/§2，验收「划界断言通过」）：
  ① 模块隔离双向：decision_inbox/decision_inbox_gates 零导入
    skill_checklist（PRD-341 三态判定引擎——机检继续各判各的零 import）/
    zh_skill_ref+zh_trigger_registry（PRD-299/355 解析与候选）/
    zh_call_replay*（重放隔离）+ 借鉴词零出现（plannotator/t3code 只借
    控制面形态）；skill_checklist 零导入 decision_inbox*（仅代码标识符
    扫描，docstring 提及不算）；
  ② 零网络零子进程零 checklist/注册表写词面 AST（R1，PRD-341 TAMPERED
    红线继续）；
  ③ R1 零自动执行 AST+行为：approve 携带 closed 词表载荷
    （write_checklist/write_registry/fill_answer）→
    INBOX_AUTO_EXEC_ATTEMPT 显形拒绝；裁决返回值零 checklist 改写/注册表
    写/附答代填载荷键；
  ④ R2 只读汇聚行为钉值：collect 注入式三源齐收（manual_review/
    answer_confirm/zh_disambiguation 词表封闭），零内核调用面；
  ⑤ R3 每项带证据钉值：manual 项缺 questions → INBOX_ITEM_INCOMPLETE
    显形拒绝入箱+附答 answers_ref 引用形态钉值（收口引用零改写）；
  ⑥ R4：InboxLedger 方法面封闭（零删除方法）+reject 留痕钉值+歧义项
    choice 必带（CHOICE_REQUIRED 同族）；
  ⑦ §2 划界钉值：skill_checklist 面（run_checklist 三态引擎）与
    zh_skill_ref 面（ref-resolution/v1 + 三码词表）符号不变——判定归
    引擎、收件箱零自动，互不越界。
零网络；全合成占位。
"""
import ast
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from decision_inbox import (  # noqa: E402
    InboxError,
    InboxLedger,
    ITEM_KINDS,
    collect,
)
from skill_checklist import run_checklist, summarize  # noqa: E402
from zh_skill_ref import ERROR_CODES as REF_ERROR_CODES  # noqa: E402
from zh_skill_ref import REF_SCHEMA  # noqa: E402

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

INBOX_MODULES = ["decision_inbox.py", "decision_inbox_gates.py"]


def _imports_of(path: Path) -> set:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    return imported


def _code_names(path: Path) -> set:
    """仅代码标识符（ast.Name/Attribute）——docstring 提及不算引用。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


class TestModuleIsolation(unittest.TestCase):
    def test_inbox_never_imports_checklist_resolver_or_replay(self):
        """收件箱面零触碰判定引擎/解析器/重放（只读消费=注入式；机检继续
        各判各的）。"""
        for mod in INBOX_MODULES:
            imported = _imports_of(SCRIPTS / mod)
            for banned in ("skill_checklist", "zh_skill_ref",
                           "zh_trigger_registry", "zh_call_replay",
                           "zh_call_replay_gates"):
                self.assertNotIn(banned, imported, f"{mod} 导入 {banned}")
            names = _code_names(SCRIPTS / mod)
            for symbol in ("run_checklist", "resolve", "lookup"):
                self.assertNotIn(symbol, names, f"{mod} 引用 {symbol}")

    def test_checklist_never_imports_inbox(self):
        """判定引擎面零导入收件箱（PRD-341 不感知本条——双向隔离）。"""
        imported = _imports_of(SCRIPTS / "skill_checklist.py")
        for mod in ("decision_inbox", "decision_inbox_gates"):
            self.assertNotIn(mod, imported)

    def test_no_plannotator_t3code_symbols(self):
        """借鉴仓（plannotator Apache-2.0/t3code MIT 实测）零符号——只借
        控制面形态。"""
        for mod in INBOX_MODULES:
            blob = ast.dump(ast.parse(
                (SCRIPTS / mod).read_text("utf-8"))).lower()
            for word in ("plannotator", "t3code"):
                self.assertNotIn(word, blob, f"{mod} 出现 {word}")


class TestRedLinePins(unittest.TestCase):
    def test_r1_zero_tamper_ast_and_payload_rejected(self):
        """R1 AST+行为（PRD-341 TAMPERED 红线继续）：收件箱两模块零网络零
        子进程；checklist/注册表写词面零出现；approve 携带 closed 词表
        载荷（write_checklist/write_registry）→ INBOX_AUTO_EXEC_ATTEMPT
        显形拒绝；裁决返回值零 checklist 改写/注册表写/附答代填键。"""
        banned = {"urllib", "requests", "socket", "http", "subprocess"}
        for mod in INBOX_MODULES:
            imported = _imports_of(SCRIPTS / mod)
            self.assertFalse(imported & banned,
                             f"{mod} 导入 {imported & banned}")
            names = {n.lower() for n in _code_names(SCRIPTS / mod)}
            for word in ("write_checklist_now", "fill_answers"):
                self.assertNotIn(word, names, f"{mod} 出现 {word}")
        items = collect(manual_reviews=MANUAL, answer_confirms=ANSWERS,
                        zh_disambiguations=DISAMB, at=NOW)
        led = InboxLedger()
        led.add(items)
        iid = items[0]["item_id"]
        with self.assertRaisesRegex(InboxError, "INBOX_AUTO_EXEC_ATTEMPT"):
            led.approve(iid, by="人（占位）", at=NOW,
                        payload={"write_checklist": True})
        out = led.approve(iid, by="人（占位）", at=NOW, choice="approved")
        for key in ("checklist_written", "registry_written", "answers_filled"):
            self.assertNotIn(key, out)

    def test_r2_collect_injected_three_sources(self):
        """R2 只读汇聚行为钉值：collect 注入式三源齐收（词表封闭），零
        内核调用面。"""
        items = collect(manual_reviews=MANUAL, answer_confirms=ANSWERS,
                        zh_disambiguations=DISAMB, at=NOW)
        self.assertEqual([it["kind"] for it in items],
                         ["manual_review", "answer_confirm",
                          "zh_disambiguation"])
        self.assertEqual(set(ITEM_KINDS),
                         {"manual_review", "answer_confirm",
                          "zh_disambiguation"})

    def test_r3_incomplete_refused_and_answers_ref_pinned(self):
        """R3 行为钉值：INBOX_ITEM_INCOMPLETE 为防御分支——公开 API 三源均
        带默认文案（与 369/T2 同款 monkeypatch 词表触发，如实声明）；附答
        answers_ref 引用形态钉值（收口引用零改写）。"""
        import decision_inbox
        orig = decision_inbox.ITEM_KINDS
        decision_inbox.ITEM_KINDS = ("not_a_kind（占位）",)   # 临时收窄词表
        try:
            with self.assertRaisesRegex(InboxError,
                                        "INBOX_ITEM_INCOMPLETE"):
                collect(manual_reviews=MANUAL, fingerprint=FP, at=NOW)
        finally:
            decision_inbox.ITEM_KINDS = orig
        items = collect(answer_confirms=ANSWERS, at=NOW)
        self.assertEqual(items[0]["answers_ref"], "manual_answers.json（占位）")

    def test_r4_ledger_surface_closed_reject_trace_choice_required(self):
        """R4：InboxLedger 方法面封闭（零删除方法）+reject 留痕钉值+歧义
        项 choice 必带（CHOICE_REQUIRED 同族）。"""
        led = InboxLedger()
        methods = {n for n in dir(led) if not n.startswith("_")}
        self.assertLessEqual(methods, {"add", "approve", "reject", "view",
                                       "events"}, methods)
        items = collect(manual_reviews=MANUAL, at=NOW)
        led.add(items)
        iid = items[0]["item_id"]
        out = led.reject(iid, by="人（占位）", at=NOW, reason="不批（占位）")
        self.assertEqual(out["reject_reason"], "不批（占位）")
        self.assertEqual(len(led.events), 2)   # add + rejected（只增）
        dis_items = collect(zh_disambiguations=DISAMB, at=NOW)
        led2 = InboxLedger()
        led2.add(dis_items)
        with self.assertRaisesRegex(InboxError, "INBOX_CHOICE_REQUIRED"):
            led2.approve(dis_items[0]["item_id"], by="人（占位）", at=NOW)


class TestDemarcationPins(unittest.TestCase):
    def test_engine_and_resolver_surfaces_unchanged(self):
        """§2 划界钉值：skill_checklist 面（run_checklist+summarize 三态
        引擎）与 zh_skill_ref 面（ref-resolution/v1+三码词表）符号不变
        ——判定归引擎、解析归解析器、收件箱零自动，互不越界。"""
        import skill_checklist as sc
        import zh_skill_ref as zsr
        self.assertTrue(callable(sc.run_checklist))
        self.assertTrue(callable(sc.summarize))
        self.assertEqual(REF_SCHEMA, "ref-resolution/v1")
        self.assertEqual(set(REF_ERROR_CODES),
                         {"REF_AMBIGUOUS", "REF_NOT_FOUND",
                          "REF_SYNTAX_ERROR"})
        self.assertFalse(hasattr(sc, "collect_inbox"),
                         "引擎面不应出现收件箱符号")


if __name__ == "__main__":
    unittest.main()
