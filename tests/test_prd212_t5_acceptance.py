# -*- coding: utf-8 -*-
"""PRD-212/T5 自测（trend #1064）：验收试运行——多工具环境记录完整。

运行：.venv/bin/python -m pytest tests/test_prd212_t5_acceptance.py -q

覆盖（验收「多工具环境记录完整」）：
  四工具 fixture 环境（各装 1 合规 + 1 版本漂移）
  检查脚本全量跑 → 状态表记录完整（逐 skill × tool 有结论，漂移 FAIL 定位 CN-SYNC-05）
  触发词抽查 → probe CSV 记录完整（逐条判定）
  修复指引可达：漂移 blocking_items 能在指引里找到编号章节
零网络。
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import cn_skill_sync_check as sync  # noqa: E402
import trigger_probe as tp  # noqa: E402

VERSION = "1.0.0"
GOOD = "zh-good"
DRIFT = "zh-drift"
TRIGGERS = ["示例触发", "演示触发", "测试触发"]


def _skill_md(name, desc, version=VERSION):
    return (f"---\nname: {name}\ndescription: {desc}\n"
            f"version: {version}\n---\n\n正文（虚构）。\n")


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_world(tmp: Path):
    """四工具 fixture：各装 zh-good@1.0.0 与 zh-drift@0.9.0（版本漂移）。"""
    skills = [
        {"skill_id": GOOD, "skill_name": GOOD,
         "description": "合规示例技能：当用户说「示例触发」时使用。",
         "version": VERSION, "trigger_word": "示例触发"},
        {"skill_id": DRIFT, "skill_name": DRIFT,
         "description": "漂移示例技能：当用户说「漂移触发」时使用。",
         "version": "0.9.0", "trigger_word": "漂移触发"},
    ]
    manifest_skills = []
    for s in skills:
        body = _skill_md(s["skill_id"], s["description"])
        ref = "附件（虚构）。\n"
        manifest_skills.append({
            "skill_id": s["skill_id"], "skill_name": s["skill_id"],
            "expected_version": VERSION,
            "files": [
                {"path": "SKILL.md", "sha256": _sha(body)},
                {"path": "references/a.md", "sha256": _sha(ref)},
            ],
            "history": [],
            "triggers": {"standard": TRIGGERS[:1] if s["skill_id"] == GOOD
                         else ["漂移触发"]},
        })
        for tool_rel in sync.TOOL_ROOTS.values():
            d = tmp / tool_rel / s["skill_id"]
            d.mkdir(parents=True, exist_ok=True)
            (d / "SKILL.md").write_text(
                _skill_md(s["skill_id"], s["description"], s["version"]),
                encoding="utf-8")
            refdir = d / "references"
            refdir.mkdir(exist_ok=True)
            (refdir / "a.md").write_text(ref, encoding="utf-8")
    manifest = {"batch": "t5", "skills": manifest_skills}
    mpath = tmp / "manifest.json"
    mpath.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return mpath, manifest


class MultiToolAcceptanceTests(unittest.TestCase):
    def test_full_environment_record(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            mpath, manifest = build_world(tmp)
            all_skills = sync.load_manifest(mpath)["skills"]
            rows = []
            for tool, rel in sync.TOOL_ROOTS.items():
                root = tmp / rel
                for entry in all_skills:
                    rows.append(sync.check_skill_tool(entry, tool, root))
            self.assertEqual(len(rows), 8)
            self.assertTrue(all(r["conclusion"] in ("PASS", "FAIL", "WARN", "SKIP")
                                for r in rows))
            by = {(r["skill_id"], r["tool"]): r for r in rows}
            self.assertTrue(all(by[(GOOD, t)]["conclusion"] == "PASS"
                                for t in sync.TOOL_ROOTS))
            for t in sync.TOOL_ROOTS:
                drift_row = by[(DRIFT, t)]
                self.assertEqual(drift_row["conclusion"], "FAIL")
                self.assertIn("CN-SYNC-05", drift_row["blocking_items"])

    def test_probe_csv_complete(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            mpath, manifest = build_world(tmp)
            probes = tp.build_probe_suite(manifest)

            def invoke(utterance):
                for w in TRIGGERS[:1]:
                    if w in utterance:
                        return GOOD
                if "漂移触发" in utterance:
                    return DRIFT
                return None

            records = tp.run_probe_suite(probes, invoke, checked_by="t5",
                                         checked_at="2026-11-01T12:00:00+00:00")
            self.assertEqual(len(records), 21)  # (1标准+8口语)×2 skill + 3 reverse
            path = tp.write_probe_csv(records, tmp / "probe.csv")
            self.assertTrue(path.exists())
            report = tp.check_pass_criteria(
                [r for r in records if r["skill_id"] == GOOD])
            self.assertEqual(report["verdict"], "PASS")

    def test_remediation_guide_reachable_for_drift(self):
        guide = (REPO / "docs" / "guides" / "sync-remediation.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            mpath, manifest = build_world(tmp)
            all_skills = sync.load_manifest(mpath)["skills"]
            row = sync.check_skill_tool(all_skills[1], "claude-code",
                                        tmp / ".claude" / "skills")
            for item in row["blocking_items"]:
                self.assertIn(item, guide)


if __name__ == "__main__":
    unittest.main(verbosity=2)
