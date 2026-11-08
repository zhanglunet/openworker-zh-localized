# -*- coding: utf-8 -*-
"""PRD-327/T3 国际化技能包发布闸门测试（trend #1604 区段）。"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from i18n_publish_gate import i18n_publish_gate, verify_i18n_publish

REPO = Path(__file__).resolve().parents[1]
REAL = REPO / "skills" / "i18n-skill"


class GateTests(unittest.TestCase):
    def test_real_skill_passes(self):
        out = i18n_publish_gate(str(REAL))
        self.assertTrue(out["allow"], str(out))
        self.assertEqual(out["name"], "i18n-skill")

    def test_missing_en_description_refused(self):
        bad = json.loads((REAL / "manifest.json").read_text(encoding="utf-8"))
        del bad["description_en"]
        out = verify_i18n_publish(bad, (REAL / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual(out["status"], "REFUSED")
        self.assertTrue(any("成对" in e for e in out["evidence"]))

    def test_cjk_in_en_refused(self):
        bad = json.loads((REAL / "manifest.json").read_text(encoding="utf-8"))
        bad["description_en"] = "英文里夹中文"
        out = verify_i18n_publish(bad, "")
        self.assertTrue(any("description_en" in e for e in out["evidence"]))

    def test_bad_version_refused(self):
        bad = json.loads((REAL / "manifest.json").read_text(encoding="utf-8"))
        bad["version"] = "v1"
        out = verify_i18n_publish(bad, "")
        self.assertTrue(any("version" in e for e in out["evidence"]))

    def test_frontmatter_manifest_mismatch_refused(self):
        bad = json.loads((REAL / "manifest.json").read_text(encoding="utf-8"))
        bad["name"] = "other-name"
        out = verify_i18n_publish(bad, (REAL / "SKILL.md").read_text(encoding="utf-8"))
        self.assertTrue(any("不同源" in e for e in out["evidence"]))

    def test_missing_files_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            out = i18n_publish_gate(d)
            self.assertFalse(out["allow"])
            self.assertEqual(out["code"], "I18N_PUBLISH_REFUSED")

    def test_gate_pure_deterministic(self):
        self.assertEqual(i18n_publish_gate(str(REAL)), i18n_publish_gate(str(REAL)))


if __name__ == "__main__":
    unittest.main()
