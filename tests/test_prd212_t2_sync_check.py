# -*- coding: utf-8 -*-
"""PRD-212/T2 自测（trend #1061）：中文技能包跨工具同步检查脚本最小实现。

运行：.venv/bin/python -m pytest tests/test_prd212_t2_sync_check.py -q

覆盖（T2 验收"状态识别准确"，≥8 例）：
  manifest 加载校验（缺 skills / files 条目缺指纹 → ManifestError）
  generate-manifest：SHA-256 指纹确定、frontmatter version 缺失回退 0.1.0、触发词提取
  CN-SYNC-01：目录缺失 → MISSING/SKIP 且短路（后续项不产生额外 FAIL）
  CN-SYNC-02：SKILL.md 缺失（P0）/ name 与目录名不一致（P1）→ FAIL
  CN-SYNC-03：附属资源缺失 → PARTIAL + FAIL
  CN-SYNC-04/05：版本 UNKNOWN → UNREADABLE；版本号漂移 → VERSION_DRIFT
  CN-SYNC-06：同版本改内容 → CONTENT_DRIFT（优先呈现）
  CN-SYNC-07/08：旧版别名目录 / 孤儿文件 → WARN（residue 标注）
  聚合规则（T1 §5.2）：FAIL > WARN > PASS；NOT_TESTED 不阻断
  版本标识优先级：frontmatter version 优先于 VERSION 文件
  全链零网络、零写操作（检查过程不改工具目录）
"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_SCRIPT = REPO / "scripts" / "cn_skill_sync_check.py"
_spec = importlib.util.spec_from_file_location("cn_skill_sync_check", _SCRIPT)
sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync)

VERSION = "1.2.3"


def write_skill(root, skill_id="zh-demo", version=VERSION, files=None,
                name=None, frontmatter_version=True):
    """在 root/.claude/skills/<skill_id>/ 造一个已装技能（虚构中文示例）。"""
    d = root / ".claude" / "skills" / skill_id
    d.mkdir(parents=True, exist_ok=True)
    fm = [
        "---",
        "name: %s" % (name or skill_id),
        "description: 虚构示例技能，当用户说「示例触发」时使用。",
    ]
    if frontmatter_version and version is not None:
        fm.append("version: %s" % version)
    fm.append("---")
    (d / "SKILL.md").write_text("\n".join(fm) + "\n\n正文（虚构示例）。\n", encoding="utf-8")
    for rel, content in (files or {"references/a.md": "附件A（虚构）。\n"}).items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return d


def make_manifest(skills_root, tmp_path, batch="t-batch"):
    data = sync.generate_manifest(skills_root, batch)
    path = tmp_path / "manifests" / ("%s.json" % batch)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


class ManifestTests(unittest.TestCase):
    def test_generate_manifest_fingerprint_and_version_fallback(self):
        import hashlib
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = root / "pack" / "zh-role" / "skills" / "zh-demo"  # role-packs 布局
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(
                "---\nname: zh-demo\ndescription: 虚构示例技能，当用户说「示例触发」时使用。\n---\n\n正文。\n",
                encoding="utf-8")
            (d / "references").mkdir()
            (d / "references" / "a.md").write_text("附件A（虚构）。\n", encoding="utf-8")
            data = sync.generate_manifest(root / "pack", "b1")
            entry = data["skills"][0]
            self.assertEqual(entry["expected_version"], "0.1.0")  # 无版本标识 → 回退
            self.assertEqual(entry["triggers"]["standard"], ["示例触发"])  # 「」触发词提取
            for f in entry["files"]:
                real = d / f["path"]
                self.assertEqual(f["sha256"], hashlib.sha256(real.read_bytes()).hexdigest())

    def test_load_manifest_rejects_bad_schema(self):
        with self.assertRaises(sync.ManifestError):
            sync.load_manifest_dict({"skills": []})
        with self.assertRaises(sync.ManifestError):
            sync.load_manifest_dict({"skills": [{"skill_id": "x", "expected_version": "1.0.0",
                                                 "files": [{"path": "a"}]}]})


class CheckTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.entry = {
            "skill_id": "zh-demo",
            "skill_name": "示例技能",
            "expected_version": VERSION,
            "files": [
                {"path": "SKILL.md", "sha256": self._sha("SKILL.md")},
                {"path": "references/a.md", "sha256": self._sha("references/a.md")},
            ],
            "history": [],
            "triggers": {"standard": []},
        }

    def _sha(self, rel):
        import hashlib
        return hashlib.sha256(
            (write_skill(self.home) / rel).read_bytes()).hexdigest()

    def _check(self):
        return sync.check_skill_tool(self.entry, "claude-code",
                                     self.home / ".claude" / "skills")

    def test_all_pass(self):
        row = self._check()
        self.assertEqual(row["install_status"], "INSTALLED")
        self.assertEqual(row["installed_version"], VERSION)
        self.assertEqual(row["version_drift"], "NONE")
        self.assertEqual(row["conclusion"], "PASS")
        self.assertEqual(row["trigger_result"], "NOT_TESTED")  # T3 范围，不阻断

    def test_missing_dir_short_circuit(self):
        import shutil
        shutil.rmtree(self.home / ".claude" / "skills" / "zh-demo")
        row = self._check()
        self.assertEqual(row["install_status"], "MISSING")
        self.assertEqual(row["conclusion"], "SKIP")
        self.assertEqual(row["version_drift"], "SKIP")
        self.assertEqual(row["blocking_items"], ["CN-SYNC-01"])

    def test_skill_md_missing_is_p0(self):
        (self.home / ".claude" / "skills" / "zh-demo" / "SKILL.md").unlink()
        row = self._check()
        self.assertEqual(row["conclusion"], "FAIL")
        self.assertIn("CN-SYNC-02", row["blocking_items"])

    def test_name_mismatch_is_p1(self):
        write_skill(self.home, name="zh-other")
        row = self._check()
        self.assertEqual(row["conclusion"], "FAIL")
        self.assertIn("CN-SYNC-02", row["blocking_items"])

    def test_missing_resource_is_partial_fail(self):
        (self.home / ".claude" / "skills" / "zh-demo" / "references" / "a.md").unlink()
        row = self._check()
        self.assertEqual(row["install_status"], "PARTIAL")
        self.assertIn("CN-SYNC-03", row["blocking_items"])

    def test_unknown_version_unreadable(self):
        write_skill(self.home, version=None, frontmatter_version=False)
        import hashlib
        d = self.home / ".claude" / "skills" / "zh-demo"
        # 重算 manifest 指纹，隔离出"版本不可读"这一个变量
        self.entry["files"] = [
            {"path": rel, "sha256": hashlib.sha256((d / rel).read_bytes()).hexdigest()}
            for rel in ("SKILL.md", "references/a.md")
        ]
        row = self._check()
        self.assertEqual(row["version_drift"], "UNREADABLE")
        self.assertIn("CN-SYNC-04", row["blocking_items"])
        self.assertNotIn("CN-SYNC-05", row["blocking_items"])  # 04 失败 → 05 SKIP

    def test_version_drift(self):
        write_skill(self.home, version="9.9.9")
        # SKILL.md 内容变了 → 需重算 manifest 中 SKILL.md 指纹，隔离版本比对
        import hashlib
        self.entry["files"][0]["sha256"] = hashlib.sha256(
            (self.home / ".claude" / "skills" / "zh-demo" / "SKILL.md").read_bytes()
        ).hexdigest()
        row = self._check()
        self.assertEqual(row["version_drift"], "VERSION_DRIFT")
        self.assertIn("CN-SYNC-05", row["blocking_items"])

    def test_content_drift_same_version(self):
        d = self.home / ".claude" / "skills" / "zh-demo"
        (d / "references" / "a.md").write_text("被手改的内容。\n", encoding="utf-8")
        row = self._check()
        self.assertEqual(row["version_drift"], "CONTENT_DRIFT")
        self.assertIn("CN-SYNC-06", row["blocking_items"])

    def test_residue_old_dir_and_orphan_warn(self):
        root = self.home / ".claude" / "skills"
        (root / "zh-demo@1.0.0").mkdir()
        (root / "zh-demo" / "stray.md").write_text("孤儿文件。\n", encoding="utf-8")
        row = self._check()
        self.assertEqual(row["conclusion"], "WARN")  # P2 WARN 不升级为 FAIL
        self.assertEqual(row["residue"], "OLD_DIR,ORPHAN_FILES")

    def test_fail_beats_warn_in_aggregation(self):
        (self.home / ".claude" / "skills" / "zh-demo" / "references" / "a.md").unlink()
        (self.home / ".claude" / "skills" / "zh-demo-v2").mkdir()
        row = self._check()
        self.assertEqual(row["conclusion"], "FAIL")  # P1 FAIL 压过 P2 WARN
        self.assertEqual(row["blocking_items"], ["CN-SYNC-03"])

    def test_version_priority_frontmatter_over_file(self):
        d = self.home / ".claude" / "skills" / "zh-demo"
        (d / "VERSION").write_text("0.0.1\n", encoding="utf-8")
        row = self._check()
        self.assertEqual(row["installed_version"], VERSION)  # frontmatter 优先

    def test_check_is_read_only(self):
        before = sorted(str(p.relative_to(self.home))
                        for p in self.home.rglob("*") if p.is_file())
        self._check()
        after = sorted(str(p.relative_to(self.home))
                       for p in self.home.rglob("*") if p.is_file())
        self.assertEqual(before, after)  # 检查过程零写操作


if __name__ == "__main__":
    unittest.main()
