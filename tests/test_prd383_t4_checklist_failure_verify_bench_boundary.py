# -*- coding: utf-8 -*-
"""PRD-383/T4 测试（trend #1887 的 T4 环节）：checklist 失败验证台划界断言。

运行：uv run --with pytest python -m pytest tests/test_prd383_t4_checklist_failure_verify_bench_boundary.py -q
（仓库根执行）

覆盖（T1 §0/§3，验收「划界断言通过」）：
  ① 模块隔离双向：checklist_failure_verify_bench/gates 零导入
    decision_inbox（369 收件箱——下游零感知）/skill_checklist（机检引擎
    ——被消费零 import，经 recheck_fn 注入重跑）/zh_skill_ref+
    zh_trigger_registry（299/355 解析与候选）/zh_call_replay*（重放）+
    借鉴词零出现（codex/security-audit，仅代码标识符扫描 docstring 提及
    不算）；
  ② 零外部仓内耦合钉值：bench 静态导入全标准库（gates 只 import 同链
    checkers_fingerprint）；零 LLM 零网络零子进程零改写词面 AST（R2，
    TAMPERED 红线不变）；
  ③ R2 零新增失败 AST+行为：bench 零机检/引擎词面（run_checklist/
    CHECKLIST 不在标识符面）——复算只经注入 fn；同一输入 verify_failure
    两遍逐字节一致（确定性复现）；
  ④ R1 拦截行为钉值：UNVERIFIED 不进 verified 分组（不进人工拍板）；
  ⑤ R3 八件套封闭钉值：缺件 BENCH_INCOMPLETE+verdict 词表封闭+checkers
    指纹 sha16 同族钉值；
  ⑥ R4：FailureBenchLedger 公开方法面封闭+reverify BENCH_STALE；
  ⑦ §3 划界钉值：skill_checklist 面（run_checklist/summarize）与
    decision_inbox 面（ITEM_KINDS 词表）符号不变——判定归引擎、验证台
    零新增失败，互不越界。
零网络；全合成占位。
"""
import ast
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from checklist_failure_verify_bench import (  # noqa: E402
    BENCH_SCHEMA,
    ERROR_CODES,
    FailureBenchError,
    FailureBenchLedger,
    VERDICTS,
    checkers_fingerprint,
    verify_failure,
    verify_failures,
)
from decision_inbox import ITEM_KINDS  # noqa: E402
from skill_checklist import run_checklist, summarize  # noqa: E402

NOW = "2026-11-13T09:00:00Z"
REF_P1 = "zh_trigger_registry.build_registry"
FAILING_CHECKERS = {REF_P1: lambda: False}
FAILURE = {"failure_id": "f-001", "check_id": "P1", "kind": "machine_fail",
           "source_ref": "skill-checklist-report/v1#P1（占位）",
           "state": "fail"}

BENCH_MODULES = ["checklist_failure_verify_bench.py",
                 "checklist_failure_verify_bench_gates.py"]


def recheck_fn(checkers):
    report = run_checklist("skill-a（占位）", checkers)
    return [dict(r) for r in report["results"] if r["state"] == "fail"]


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
    def test_bench_never_imports_inbox_engine_resolver_or_replay(self):
        """验证台面零触碰收件箱/机检引擎/解析器/重放（机检经注入重跑零
        import；收件箱是下游零感知）。"""
        for mod in BENCH_MODULES:
            imported = _imports_of(SCRIPTS / mod)
            for banned in ("decision_inbox", "skill_checklist",
                           "zh_skill_ref", "zh_trigger_registry",
                           "zh_call_replay", "zh_call_replay_gates"):
                self.assertNotIn(banned, imported, f"{mod} 导入 {banned}")
            names = _code_names(SCRIPTS / mod)
            for symbol in ("InboxLedger", "run_checklist", "resolve",
                           "lookup"):
                self.assertNotIn(symbol, names, f"{mod} 引用 {symbol}")

    def test_inbox_never_imports_bench(self):
        """收件箱面零导入验证台（369 不感知本条——双向隔离）。"""
        imported = _imports_of(SCRIPTS / "decision_inbox.py")
        for mod in ("checklist_failure_verify_bench",
                    "checklist_failure_verify_bench_gates"):
            self.assertNotIn(mod, imported)

    def test_upstream_zero_symbols(self):
        """借鉴仓（codex-security Apache-2.0/security-audit-skill MIT 实测）
        零符号——只借控制面形态（仅代码标识符扫描）。"""
        for mod in BENCH_MODULES:
            names = {n.lower() for n in _code_names(SCRIPTS / mod)}
            for word in ("codex", "audit_skill"):
                self.assertNotIn(word, names, f"{mod} 出现 {word}")

    def test_zero_internal_coupling_and_redline_ast(self):
        """零外部仓内耦合钉值：bench 静态导入全标准库（gates 只 import 同链
        checkers_fingerprint）；零 LLM 零网络零子进程零改写词面。"""
        imported = _imports_of(SCRIPTS / "checklist_failure_verify_bench.py")
        self.assertLessEqual(imported - {"__future__", "copy", "hashlib",
                                         "json", "pathlib", "typing"},
                             set(), imported)
        gates_imported = _imports_of(
            SCRIPTS / "checklist_failure_verify_bench_gates.py")
        self.assertLessEqual(gates_imported - {"__future__", "typing",
                                               "checklist_failure_verify_bench"},
                             set())
        for mod in BENCH_MODULES:
            names = {n.lower() for n in _code_names(SCRIPTS / mod)}
            for word in ("write_checklist", "write_registry", "fill_answers"):
                self.assertNotIn(word, names, f"{mod} 出现改写词面 {word}")


class TestRedLinePins(unittest.TestCase):
    def test_r2_no_new_failure_ast_and_deterministic(self):
        """R2 AST+行为：bench 零机检/引擎词面（复算只经注入 fn）；同一输入
        verify_failure 两遍逐字节一致（确定性复现）。"""
        for mod in BENCH_MODULES:
            names = {n.lower() for n in _code_names(SCRIPTS / mod)}
            for word in ("run_checklist", "summarize"):
                self.assertNotIn(word, names, f"{mod} 出现 {word}")
        a = verify_failure(FAILURE, FAILING_CHECKERS, recheck_fn, at=NOW)
        b = verify_failure(FAILURE, FAILING_CHECKERS, recheck_fn, at=NOW)
        self.assertEqual(a, b)

    def test_r1_unverified_blocked_at_outlet(self):
        """R1 拦截钉值：UNVERIFIED 不进 verified 分组（不进人工拍板）。"""
        out = verify_failures([dict(FAILURE, check_id="P99（不存在项）")],
                              FAILING_CHECKERS, recheck_fn, at=NOW)
        self.assertEqual(out["verified"], [])
        self.assertEqual(out["unverified_count"], 1)

    def test_r3_eight_piece_closed_and_fp_family(self):
        """R3 钉值：账目缺件 BENCH_INCOMPLETE；verdict 词表封闭；checkers
        指纹 sha16 同族钉值（确定性）。"""
        led = FailureBenchLedger(None)
        with self.assertRaisesRegex(FailureBenchError, "BENCH_INCOMPLETE"):
            led.record({"schema": BENCH_SCHEMA}, at=NOW)
        self.assertEqual(set(VERDICTS), {"VERIFIED", "UNVERIFIED"})
        fp = checkers_fingerprint(FAILING_CHECKERS)
        self.assertTrue(fp.startswith("sha16:"))
        self.assertEqual(fp, checkers_fingerprint(FAILING_CHECKERS))

    def test_r4_ledger_surface_closed_and_stale(self):
        """R4：FailureBenchLedger 公开方法面封闭（零删除方法）+reverify
        checkers 变更 BENCH_STALE 拒绝复用。"""
        led = FailureBenchLedger(None)
        methods = {n for n in dir(led) if not n.startswith("_")}
        self.assertLessEqual(methods, {"record", "entries", "latest_for",
                                       "reverify"}, methods)
        led.record(verify_failure(FAILURE, FAILING_CHECKERS, recheck_fn,
                                  at=NOW), at=NOW)
        out = led.reverify("f-001", {REF_P1: lambda: True,
                                     "other.check（占位）": lambda: True},
                           recheck_fn, at=NOW)
        self.assertEqual(out["refused"], "BENCH_STALE")


class TestDemarcationPins(unittest.TestCase):
    def test_engine_and_inbox_surfaces_unchanged(self):
        """§3 划界钉值：skill_checklist 面（run_checklist+summarize）与
        decision_inbox 面（ITEM_KINDS 词表）符号不变——判定归引擎、验证台
        零新增失败，互不越界。"""
        import skill_checklist as sc
        import decision_inbox as di
        self.assertTrue(callable(sc.run_checklist))
        self.assertTrue(callable(sc.summarize))
        self.assertEqual(set(ITEM_KINDS),
                         {"manual_review", "answer_confirm",
                          "zh_disambiguation"})
        self.assertFalse(hasattr(sc, "verify_failure"),
                         "引擎面不应出现验证台符号")
        self.assertFalse(hasattr(di, "reverify"),
                         "收件箱面不应出现复验符号")


if __name__ == "__main__":
    unittest.main()
