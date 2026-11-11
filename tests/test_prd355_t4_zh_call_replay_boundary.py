# -*- coding: utf-8 -*-
"""PRD-355/T4 测试（trend #1634 的 T4 环节）：中文调用重放划界断言。

运行：uv run --with pytest python -m pytest tests/test_prd355_t4_zh_call_replay_boundary.py -q
（仓库根执行）

覆盖（T1 §0/§2，验收「划界断言通过」）：
  ① 模块隔离双向：zh_call_replay/gates 零导入 skillpack_snapshot
    （PRD-285 升级可逆）/zh_trigger_registry（解析层经 lookup_fn 注入零
    import）/eng_checklist（PRD-341 机检）+ 借鉴词零出现（AiSOC/OpenBot
    MIT 只借形态）；skillpack_snapshot 零导入 zh_call_replay*；
  ② 唯一耦合钉值：zh_call_replay 静态导入全标准库——解析层经 lookup_fn
    注入；零网络零子进程零 skill 执行词面 AST（R2）；
  ③ R1 行为钉值：决策缺 utterance/status 或 normalized 长度不齐或空
    calls → refused=PACK_INCOMPLETE；
  ④ R2 零执行行为钉值：lookup_fn 收到深拷贝（registry 零污染）+重放
    返回值零执行载荷键；
  ⑤ R3 零静默钉值：mismatch 键面封闭 {schema,refused,verdict,evidence,
    rerun_count}——零静默换新解析载荷键；
  ⑥ R4：ReplayLedger 方法面封闭（零删除方法）；
  ⑦ §2 划界钉值：skillpack_snapshot 快照面（skillpack-snapshot-v1 +
    事件词表）符号不变——PRD-285 管升级可逆，本条管中文调用可重放，
    互不越界。
零网络；全合成占位。
"""
import ast
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from skillpack_snapshot import (  # noqa: E402
    ACTOR_ROLES,
    CHANGE_TYPES,
    SNAPSHOT_SCHEMA,
)
from zh_call_replay import ReplayLedger, make_pack, replay  # noqa: E402
from zh_trigger_registry import build_registry, lookup  # noqa: E402

REGISTRY = build_registry()
UTTERANCES = ["帮我写周报（占位）"]
NORMALIZED = ["帮我写周报（占位）"]
LOOKUP = lookup(REGISTRY, UTTERANCES[0])
CALLS = [{"utterance": UTTERANCES[0], "resolved_skill": LOOKUP.get("skill"),
          "status": LOOKUP["status"], "candidates": LOOKUP.get("candidates", [])}]

REPLAY_MODULES = ["zh_call_replay.py", "zh_call_replay_gates.py"]


def lookup_fn(utt, reg):
    return dict(LOOKUP)


def _imports_of(path: Path) -> set:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    return imported


class TestModuleIsolation(unittest.TestCase):
    def test_replay_never_imports_snapshot_registry_or_checklist(self):
        """重放面零触碰升级快照/解析器/机检（中文调用可重放不感知升级可逆
        与生产化成熟度）。"""
        for mod in REPLAY_MODULES:
            imported = _imports_of(SCRIPTS / mod)
            for banned in ("skillpack_snapshot", "zh_trigger_registry",
                           "eng_checklist", "trigger_probe"):
                self.assertNotIn(banned, imported, f"{mod} 导入 {banned}")
            blob = ast.dump(ast.parse(
                (SCRIPTS / mod).read_text(encoding="utf-8")))
            for symbol in ("SNAPSHOT_SCHEMA", "spot_check", "run_checklist"):
                self.assertNotIn(symbol, blob, f"{mod} 引用 {symbol}")

    def test_snapshot_never_imports_replay(self):
        """快照面零导入重放（PRD-285 不感知本条——双向隔离）。"""
        imported = _imports_of(SCRIPTS / "skillpack_snapshot.py")
        for mod in ("zh_call_replay", "zh_call_replay_gates"):
            self.assertNotIn(mod, imported)

    def test_no_aisoc_openbot_symbols(self):
        """借鉴仓（AiSOC/OpenBot，MIT 实测）零符号——只借形态。"""
        for mod in REPLAY_MODULES:
            blob = ast.dump(ast.parse(
                (SCRIPTS / mod).read_text("utf-8"))).lower()
            for word in ("aisoc", "openbot"):
                self.assertNotIn(word, blob, f"{mod} 出现 {word}")

    def test_only_coupling_is_injected_lookup_fn(self):
        """§2 钉值：zh_call_replay 静态导入全标准库——解析层经 lookup_fn
        注入（零 import 耦合）。"""
        imported = _imports_of(SCRIPTS / "zh_call_replay.py")
        self.assertLessEqual(imported,
                             {"__future__", "copy", "hashlib", "json",
                              "typing"})
        src = (SCRIPTS / "zh_call_replay.py").read_text("utf-8")
        self.assertIn("lookup_fn", src)


class TestRedLinePins(unittest.TestCase):
    def test_r1_pack_incomplete_refusal_pinned(self):
        """R1 行为钉值：决策缺 utterance/status、normalized 长度不齐或空
        calls → refused=PACK_INCOMPLETE。"""
        out = make_pack([{"resolved_skill": "x"}], REGISTRY, NORMALIZED,
                        rules_version="v1")
        self.assertEqual(out["refused"], "PACK_INCOMPLETE")
        out2 = make_pack(CALLS, REGISTRY, [], rules_version="v1")
        self.assertEqual(out2["refused"], "PACK_INCOMPLETE")
        out3 = make_pack([], REGISTRY, NORMALIZED, rules_version="v1")
        self.assertEqual(out3["refused"], "PACK_INCOMPLETE")

    def test_r2_zero_execution_ast_and_deepcopy(self):
        """R2 AST+行为：零网络零子进程零 skill 执行词面；lookup_fn 收到
        深拷贝 registry 零污染；重放返回值零执行载荷键。"""
        banned = {"urllib", "requests", "socket", "http", "subprocess",
                  "skillpack_snapshot"}
        for mod in REPLAY_MODULES:
            imported = _imports_of(SCRIPTS / mod)
            self.assertFalse(imported & banned,
                             f"{mod} 导入 {imported & banned}")
            src = (SCRIPTS / mod).read_text(encoding="utf-8").lower()
            for word in ("run_skill", "execute_skill", "upgrade("):
                self.assertNotIn(word, src, f"{mod} 出现 {word}")
        pack = make_pack(CALLS, REGISTRY, NORMALIZED, rules_version="v1")
        seen = {}

        def mutating_fn(utt, reg):
            seen["utt"] = utt
            reg["packs"] = []   # 就地改写仅副本
            return dict(LOOKUP)

        out = replay(pack, UTTERANCES, REGISTRY, NORMALIZED, mutating_fn,
                     rules_version="v1")
        self.assertEqual(seen["utt"], UTTERANCES[0])
        self.assertTrue(len(REGISTRY.get("packs", REGISTRY)) >= 1,
                        "调用方 registry 零污染")
        for key in ("executed", "ran"):
            self.assertNotIn(key, out)

    def test_r3_mismatch_returns_closed_keys_no_new_resolution(self):
        """R3 零静默钉值：mismatch 键面封闭——零静默换新解析载荷键。"""
        pack = make_pack(CALLS, REGISTRY, NORMALIZED, rules_version="v1")
        out = replay(pack, UTTERANCES, REGISTRY, NORMALIZED,
                     lambda u, r: dict(LOOKUP, skill="改写（占位）"),
                     rules_version="v1")
        self.assertEqual(out["verdict"], "REPLAY_MISMATCH")
        self.assertEqual(out["evidence"]["first_divergence_index"], 0)
        self.assertEqual(set(out), {"schema", "refused", "verdict",
                                    "evidence", "rerun_count"})

    def test_r4_ledger_method_surface_closed(self):
        """R4：ReplayLedger 方法面封闭——零删除方法。"""
        led = ReplayLedger()
        methods = {n for n in dir(led) if not n.startswith("_")}
        self.assertLessEqual(methods, {"record", "entries"}, methods)
        pack = make_pack(CALLS, REGISTRY, NORMALIZED, rules_version="v1")
        led.record(pack, {"verdict": "REPLAY_OK", "evidence": None},
                   at="2026-11-11T09:00:00Z")
        self.assertEqual(len(led.entries), 1)


class TestDemarcationPins(unittest.TestCase):
    def test_skillpack_snapshot_surface_unchanged(self):
        """§2 划界钉值：skillpack_snapshot 快照面（skillpack-snapshot-v1 +
        事件词表）符号不变——PRD-285 管升级可逆，本条管中文调用可重放，
        互不越界。"""
        import skillpack_snapshot as ss
        self.assertEqual(SNAPSHOT_SCHEMA, "skillpack-snapshot-v1")
        for name in ("CHANGE_TYPES", "ACTOR_ROLES", "SPOT_CHECK_DEFAULT_N"):
            self.assertTrue(hasattr(ss, name), name)
        self.assertFalse(hasattr(ss, "replay"), "快照面不应出现重放符号")


if __name__ == "__main__":
    unittest.main()
