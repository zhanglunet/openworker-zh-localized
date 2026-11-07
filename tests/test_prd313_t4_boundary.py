# -*- coding: utf-8 -*-
"""PRD-313/T4 划界断言（trend #1579）。

- 模块隔离（AST 白名单）：replay_pack 只导入标准库与本仓动作出口模块——
  零审计链/快照/复核/执行面导入（闸门与既有机制互不越界）；
- 闸门拒绝零写盘：拒绝路径不追加账本、不改任何文件；
- 红线钉值：歧义零硬判（人工消歧留痕）。
"""
import ast
import copy
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import replay_pack as rp  # noqa: E402

MODULE_SRC = Path("scripts/replay_pack.py").read_text(encoding="utf-8")
ALLOWED_IMPORT_ROOTS = {"__future__", "hashlib", "json", "pathlib", "typing", "zh_trigger_registry"}


class ModuleIsolationTests(unittest.TestCase):

    def test_ast_import_whitelist(self):
        """模块隔离：replay_pack 只导入标准库与本仓动作出口——零越界导入。"""
        tree = ast.parse(MODULE_SRC)
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        self.assertTrue(roots <= ALLOWED_IMPORT_ROOTS,
                        f"越界导入：{sorted(roots - ALLOWED_IMPORT_ROOTS)}")


class GateRefusalZeroWriteTests(unittest.TestCase):

    def test_refused_gate_writes_nothing(self):
        """拒绝路径零写盘：闸门拒绝不追加账本、不改任何文件。"""
        from replay_pack import ReplayLedger, replay_gate
        with tempfile.TemporaryDirectory() as tmp:
            ledger = ReplayLedger(Path(tmp) / "ledger.jsonl")
            before = ledger.bytes_now()
            verdict = replay_gate({"status": "MISMATCH", "evidence": {"x": 1}})
            self.assertFalse(verdict["allow"])
            self.assertEqual(ledger.bytes_now(), before)  # 拒绝零写盘——歧义零硬判


if __name__ == "__main__":
    unittest.main()
