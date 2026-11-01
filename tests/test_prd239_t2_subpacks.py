# -*- coding: utf-8 -*-
"""PRD-239/T2 自测：中文技能包按场景分包。"""
import sys
import unittest
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from zh_skill_subpack import build_registry  # noqa: E402


class Test(unittest.TestCase):
    def test_registry_has_three_scenes(self):
        r = build_registry(str(REPO / "role-packs"))
        self.assertEqual(set(r["subpacks"].keys()), {"workplace", "legal-contract", "sales-marketing"})

    def test_all_skills_have_subpack(self):
        r = build_registry(str(REPO / "role-packs"))
        self.assertGreater(len(r["skills"]), 0)
        for name, info in r["skills"].items():
            self.assertTrue(info["subpack"], f"{name} 缺分包")
            self.assertTrue(info["subpack_one_line"], f"{name} 缺定位")

    def test_json_serializable(self):
        import json
        r = build_registry(str(REPO / "role-packs"))
        json.dumps(r, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
