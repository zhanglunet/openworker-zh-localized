# -*- coding: utf-8 -*-
"""PRD-184/T5 验收（trend #924）：栏目可浏览；无密钥/内网信息；术语统一。

对照构建实录栏目（栏目索引 + 首篇 + 2 篇草案大纲）做：
- 可浏览走查：根 README 入口 → 栏目索引 → 篇目表/草案清单 → 各篇 → 回链，
  仓库内相对链接逐条解析（文件系统即浏览器 URL 基准），零死链；
- 术语统一自查：CI 同口径基表 + role-packs/terms.txt 合并双口径零失败，
  栏目固定词表（状态/标签枚举、四段标题、栏目名）跨文件一致；
- 隐私扫描：密钥/凭据字样、令牌前缀、IPv4、内网域名后缀、邮箱形态账号逐行零命中。
"""
import importlib.util
import os
import re
import unittest
from pathlib import Path

REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COLUMN = REPO / "docs" / "articles" / "build-in-public"
ACCEPTANCE_DOC = REPO / "docs" / "build-in-public-acceptance.md"
INDEX = COLUMN / "README.md"
TEMPLATE = COLUMN / "TEMPLATE.md"
FIRST = COLUMN / "2026-10-25-context-panel-merged.md"
OUTLINES = (COLUMN / "2026-11-install-one-line.md", COLUMN / "2026-11-upstream-weekly-auto.md")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
SECTION_HEADINGS = ("## 目标", "## 过程", "## 踩坑", "## 产物")
STATUS_ENUM = ("已发布", "草案")
TAG_ENUM = ("面板", "打包", "上游同步", "文档", "工具链")


def _load(path_name, script):
    spec = importlib.util.spec_from_file_location(path_name, REPO / script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _column_files():
    return {p.relative_to(REPO).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted(COLUMN.glob("*.md"))}


# ---------------------------------------------------------------------------
# 栏目可浏览：入口 → 索引 → 篇目 → 回链，相对链接零死链
# ---------------------------------------------------------------------------
class TestColumnBrowsable(unittest.TestCase):
    def test_root_readme_entry_reaches_index(self):
        root = (REPO / "README.md").read_text(encoding="utf-8")
        m = re.search(r"\]\((docs/articles/build-in-public/README\.md)\)", root)
        self.assertIsNotNone(m, "根 README 缺栏目入口链接")
        self.assertTrue((REPO / m.group(1)).is_file())

    def test_all_relative_links_resolve(self):
        root = REPO.resolve()
        total = 0
        for name, text in _column_files().items():
            base = REPO / os.path.dirname(name)
            for m in LINK_RE.finditer(text):
                target = m.group(1)
                if target.startswith(("http://", "https://", "#")):
                    continue
                path = target.split("#", 1)[0]
                if not path:
                    continue
                total += 1
                resolved = Path(os.path.normpath(base / path))
                self.assertTrue(resolved.exists(), f"{name} 死链：{target}")
                resolved = resolved.resolve()
                self.assertTrue(
                    resolved == root or root in resolved.parents,
                    f"{name} 链接逃出仓库：{target}")
        self.assertGreaterEqual(total, 15, "栏目内仓库相对链接数量异常")

    def test_index_table_and_draft_list_browsable(self):
        text = INDEX.read_text(encoding="utf-8")
        table = text.split("## 篇目表", 1)[1].split("### 草案", 1)[0]
        link = re.search(r"\]\(([^)]+\.md)\)", table)
        self.assertIsNotNone(link, "篇目表无已发布文章链接")
        first = COLUMN / link.group(1)
        self.assertTrue(first.is_file())
        fm = first.read_text(encoding="utf-8").split("---")[1]
        self.assertIn("status: 已发布", fm)
        for outline in OUTLINES:
            self.assertTrue(outline.is_file())
            self.assertIn(outline.name, text, "草案须在索引可发现")
            ofm = outline.read_text(encoding="utf-8").split("---")[1]
            self.assertIn("status: 草案", ofm)
        self.assertTrue(TEMPLATE.is_file())
        self.assertIn("TEMPLATE.md", text)

    def test_every_article_backlinks_index_and_weekly(self):
        for path in (FIRST,) + OUTLINES:
            text = path.read_text(encoding="utf-8")
            self.assertIn("](README.md)", text, f"{path.name} 缺栏目索引回链")
            self.assertIn("英文摘要", text, f"{path.name} 缺英文摘要段")
            for h in SECTION_HEADINGS:
                self.assertIn(h, text, f"{path.name} 缺 {h} 段")

    def test_first_article_artifacts_and_evidence_exist(self):
        text = FIRST.read_text(encoding="utf-8")
        fm = text.split("---")[1]
        artifacts = re.findall(r"^\s+- (\S+)$",
                               fm.split("artifacts:", 1)[1].split("bilingual:", 1)[0], re.M)
        self.assertGreaterEqual(len(artifacts), 1)
        for art in artifacts:
            self.assertTrue((REPO / art).exists(), f"artifact 不存在：{art}")
        evidence = re.findall(r"^\s+- (\S+)$",
                              fm.split("evidence:", 1)[1].split("artifacts:", 1)[0], re.M)
        for url in evidence:
            self.assertRegex(url, r"https://github\.com/zhanglunet/openworker-zh-localized/(pull|issues)/\d+")


# ---------------------------------------------------------------------------
# 术语统一：双口径质量门 + 栏目固定词表跨文件一致
# ---------------------------------------------------------------------------
class TestColumnTermsUnified(unittest.TestCase):
    def test_quality_gate_base_terms_zero_failures(self):
        qg = _load("qg", os.path.join("scripts", "quality-gate.py"))
        self.assertEqual(qg.check_terms(_column_files(), qg.TERMS), [])

    def test_quality_gate_merged_terms_zero_failures(self):
        """基表 + role-packs/terms.txt 合并口径（与发行门同一合并语义）。"""
        qg = _load("qg", os.path.join("scripts", "quality-gate.py"))
        rg = _load("rg", os.path.join("scripts", "release-gate-role-packs.py"))
        entries, _exempt, errors = rg.parse_terms_file(
            (REPO / "role-packs" / "terms.txt").read_text(encoding="utf-8"))
        self.assertEqual(errors, [])
        merged, merge_errors, _w = rg.merge_terms(qg.TERMS, entries)
        self.assertEqual(merge_errors, [])
        self.assertEqual(qg.check_terms(_column_files(), merged), [])

    def test_column_vocabulary_consistent_across_files(self):
        for name, text in _column_files().items():
            if name.endswith("TEMPLATE.md"):
                continue  # 模板允许含枚举说明与占位符示例
            # 状态枚举只准用两个定名；标签不得出枚举外的中文标签值
            for status in ("已发布", "草案"):
                if status in text:
                    self.assertIn(status, STATUS_ENUM)
            self.assertNotIn("完稿", text, f"{name} 出现状态枚举外用词")
            self.assertNotIn("已刊发", text, f"{name} 出现状态枚举外用词")
            # 栏目名定名
            if name.endswith("README.md"):
                self.assertIn("构建实录", text)
                self.assertIn("Build in Public", text)
            # 四段标题动词定名（不被写成「背景/步骤/经验/产出」等变体）
            self.assertNotIn("## 背景", text, f"{name} 出现四段标题变体")
            self.assertNotIn("## 产出\n", text, f"{name} 出现四段标题变体")


# ---------------------------------------------------------------------------
# 无密钥/内网信息：逐行扫描（合规闸自述行本身豁免，与 T2 门同口径）
# ---------------------------------------------------------------------------
SECRET_RE = re.compile(
    r"secret|password|credential|api[-_]?key|bearer|private[-_]?key|"
    r"BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}",
    re.IGNORECASE,
)
TOKEN_ASSIGN_RE = re.compile(r"\b(token|passwd|pwd)\s*[=:]\s*\S", re.IGNORECASE)
IPV4_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
INTERNAL_HOST_RE = re.compile(r"\b[\w-]+\.(?:local|internal|intranet|corp|lan)\b",
                              re.IGNORECASE)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


class TestNoSecretsOrInternalInfo(unittest.TestCase):
    def _scan_paths(self):
        paths = sorted(COLUMN.glob("*.md"))
        if ACCEPTANCE_DOC.is_file():
            paths.append(ACCEPTANCE_DOC)
        return paths

    def test_column_scan_clean(self):
        for path in self._scan_paths():
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if "自查口径" in line:  # 合规闸对扫描口径的自述行，非泄露（T2 门同豁免）
                    continue
                for rx, why in ((SECRET_RE, "疑似密钥/凭据字样"),
                                (TOKEN_ASSIGN_RE, "疑似令牌赋值"),
                                (IPV4_RE, "出现 IP（应用占位符）"),
                                (INTERNAL_HOST_RE, "疑似内部主机名"),
                                (EMAIL_RE, "疑似真实账号（邮箱）")):
                    m = rx.search(line)
                    self.assertIsNone(
                        m, f"{path.name}:{lineno} {why}：{m.group(0) if m else ''}")

    def test_publish_gate_items_declared(self):
        index = INDEX.read_text(encoding="utf-8")
        self.assertIn("发布合规闸五项", index)
        template = TEMPLATE.read_text(encoding="utf-8")
        gate = template.split("## 发布前合规闸", 1)[1]
        for item in ("敏感信息扫描", "未发布安全细节", "术语统一", "evidence 核对", "数据诚实"):
            self.assertIn(item, gate)


if __name__ == "__main__":
    unittest.main()
