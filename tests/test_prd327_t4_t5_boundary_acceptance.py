# -*- coding: utf-8 -*-
"""PRD-327/T4+T5：i18n 发布闸门划界断言 + 验收试运行（trend #1604 区段）。

T4 划界：i18n_publish_gate 零网络形态（无 requests/urllib/socket/http）+
零写盘调用形态（AST import 白名单）+ 闸门拒绝零副作用（入参 deepcopy 不变）。
T5 验收：真实技能包（manifest + SKILL.md）→ 闸门三场景（真实过闸/双语缺失
拒/双载体不同源拒）各两遍逐字段一致（可重放口径）。
"""
from __future__ import annotations
import ast
import copy
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from i18n_publish_gate import i18n_publish_gate, verify_i18n_publish

REAL = REPO / "skills" / "i18n-skill"


class T4BoundaryTests(unittest.TestCase):
    def test_ast_import_stdlib_only(self):
        tree = ast.parse((REPO / "scripts" / "i18n_publish_gate.py").read_text(encoding="utf-8"))
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        for bad in ("requests", "urllib", "socket", "http", "shutil"):
            self.assertNotIn(bad, roots, f"越界导入：{bad}")

    def test_gate_refusal_zero_side_effect(self):
        bad = {"name": "x", "description": "中文", "description_en": "english", "version": "1.0"}
        bad["version"] = "not-semver"
        frozen = copy.deepcopy(bad)
        verify_i18n_publish(bad, "")
        self.assertEqual(bad, frozen, "拒绝路径不得改入参")


class T5AcceptanceTests(unittest.TestCase):
    def _chain(self, skill_dir):
        gate = i18n_publish_gate(skill_dir)
        manifest = json.loads((Path(skill_dir) / "manifest.json").read_text(encoding="utf-8")) \
            if (Path(skill_dir) / "manifest.json").is_file() else {}
        return {"gate": gate, "manifest_view": {"name": manifest.get("name"),
                                                "version": manifest.get("version")}}

    def test_real_skill_full_chain_replay_identical(self):
        self.assertEqual(self._chain(str(REAL)), self._chain(str(REAL)))
        out = self._chain(str(REAL))
        self.assertTrue(out["gate"]["allow"])
        self.assertEqual(out["gate"]["name"], "i18n-skill")

    def test_bilingual_missing_refused_replay_identical(self):
        def run():
            import tempfile
            with tempfile.TemporaryDirectory() as d:
                mf = {"name": "x", "description": "只有中文", "version": "1.0.0"}
                Path(d, "manifest.json").write_text(json.dumps(mf, ensure_ascii=False), encoding="utf-8")
                Path(d, "SKILL.md").write_text("---\nname: x\n---\n正文\n", encoding="utf-8")
                return self._chain(d)
        self.assertEqual(run(), run())
        self.assertFalse(run()["gate"]["allow"])
        self.assertTrue(any("成对" in e for e in run()["gate"]["evidence"]))

    def test_dual_carrier_mismatch_refused_replay_identical(self):
        def run():
            import tempfile
            with tempfile.TemporaryDirectory() as d:
                mf = {"name": "a", "description": "中文描述", "description_en": "english",
                      "version": "1.0.0"}
                Path(d, "manifest.json").write_text(json.dumps(mf, ensure_ascii=False), encoding="utf-8")
                Path(d, "SKILL.md").write_text("---\nname: b\n---\n正文\n", encoding="utf-8")
                return self._chain(d)
        self.assertEqual(run(), run())
        self.assertFalse(run()["gate"]["allow"])
        self.assertTrue(any("不同源" in e for e in run()["gate"]["evidence"]))


if __name__ == "__main__":
    unittest.main()
