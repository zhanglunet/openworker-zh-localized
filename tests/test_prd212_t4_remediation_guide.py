# -*- coding: utf-8 -*-
"""PRD-212/T4 自测（trend #1063）：漂移修复指引（可照做）。

运行：.venv/bin/python -m pytest tests/test_prd212_t4_remediation_guide.py -q

机检口径（验收「指引可照做」）：
  指引覆盖 CN-SYNC-01~12 全部编号（每条有修复步骤小节）；
  诊断命令引用真实脚本路径（scripts/cn_skill_sync_check.py 存在且可 import）；
  修复命令与 T2 判定枚举口径一致（MISSING/VERSION_DRIFT/CONTENT_DRIFT/OLD_DIR/
    ORPHAN_FILES 等状态名逐一对得上）；
  术语一致性预检（CI quality-gate 口径）零失败。
零网络。
"""
import importlib.util
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GUIDE = REPO / "docs" / "guides" / "sync-remediation.md"
SCRIPT = REPO / "scripts" / "cn_skill_sync_check.py"

ALL_IDS = [f"CN-SYNC-{i:02d}" for i in range(1, 13)]
STATES = ["MISSING", "VERSION_DRIFT", "CONTENT_DRIFT", "OLD_DIR", "ORPHAN_FILES",
          "UNREADABLE", "SKIP"]


class RemediationGuideTests(unittest.TestCase):
    def test_guide_covers_all_sync_ids(self):
        text = GUIDE.read_text(encoding="utf-8")
        missing = [i for i in ALL_IDS if i not in text]
        self.assertEqual(missing, [], f"指引缺编号：{missing}")

    def test_diagnosis_command_references_real_script(self):
        text = GUIDE.read_text(encoding="utf-8")
        self.assertIn("scripts/cn_skill_sync_check.py", text)
        self.assertTrue(SCRIPT.exists())
        spec = importlib.util.spec_from_file_location("sync", str(SCRIPT))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # 脚本可加载（诊断入口真实可用）
        self.assertTrue(hasattr(mod, "check_skill_tool"))

    def test_state_names_match_t2_enum(self):
        text = GUIDE.read_text(encoding="utf-8")
        for state in STATES:
            self.assertIn(state, text, f"指引未覆盖状态 {state}（与 T2 判定枚举对不上）")

    def test_term_consistency_clean(self):
        spec = importlib.util.spec_from_file_location("qg", str(REPO / "scripts" / "quality-gate.py"))
        qg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(qg)
        fails = qg.check_terms({str(GUIDE.relative_to(REPO)): GUIDE.read_text(encoding="utf-8")},
                               qg.TERMS)
        self.assertEqual(fails, [])


if __name__ == "__main__":
    unittest.main()
