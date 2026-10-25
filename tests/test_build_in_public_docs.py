# -*- coding: utf-8 -*-
"""PRD-184/T2+T3 gate — 构建实录（Build in Public）栏目自查（trend #921 / #922）。

规范依据：T1 设计（docs/plans/2026-10-25-zh-build-in-public.md，PR #49）：
- §3.2 两层结构：docs/articles/build-in-public/ 是正文唯一事实源；
- §3.3 篇目元数据七字段；§4.3 四段骨架（目标/过程/踩坑/产物），踩坑必填不得空话；
- §4.4 发布合规闸五项；§1 借鉴声明（elie222/rakazo, Apache-2.0）。
- T3（#922）：首篇已发布（evidence 指向本仓库公开 PR）+ 2 篇草案大纲 + 仓库层 README 入口。
"""
import importlib.util
import os
import re
from pathlib import Path

REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COLUMN = REPO / "docs" / "articles" / "build-in-public"
TEMPLATE = COLUMN / "TEMPLATE.md"
INDEX = COLUMN / "README.md"
FIRST_ARTICLE = COLUMN / "2026-10-25-context-panel-merged.md"
OUTLINES = (
    COLUMN / "2026-11-install-one-line.md",
    COLUMN / "2026-11-upstream-weekly-auto.md",
)
README_ZH = REPO / "README.md"

META_FIELDS = ("title", "date", "status", "tags", "evidence", "artifacts", "bilingual")
SECTION_HEADINGS = ("## 目标", "## 过程", "## 踩坑", "## 产物")
TAG_ENUM = ("面板", "打包", "上游同步", "文档", "工具链")
GATE_ITEMS = ("敏感信息扫描", "未发布安全细节", "术语统一", "evidence 核对", "数据诚实")


def _template_text() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def _frontmatter(text: str) -> str:
    assert text.startswith("---"), "模板必须以 YAML frontmatter 开头（元数据七字段）"
    end = text.find("\n---", 3)
    assert end != -1
    return text[3:end]


# ---------------------------------------------------------------------------
# 模板：元数据七字段 + 四段骨架 + 踩坑硬约束 + 合规闸五项
# ---------------------------------------------------------------------------
def test_template_has_seven_meta_fields():
    fm = _frontmatter(_template_text())
    for field in META_FIELDS:
        assert re.search(rf"^{field}:", fm, re.MULTILINE), f"frontmatter 缺 {field} 字段"
    # 字段说明表随模板走（T1 §3.3 逐字段约定）
    text = _template_text()
    for field in META_FIELDS:
        assert f"`{field}`" in text, f"元数据说明表缺 {field}"


def test_template_four_section_skeleton():
    text = _template_text()
    body = text.split("\n---", 1)[1]  # frontmatter 闭合之后的全部正文
    pos = -1
    for h in SECTION_HEADINGS:
        found = body.find(h)
        assert found != -1, f"模板缺 {h} 段"
        assert found > pos, f"{h} 段顺序不对（须为目标→过程→踩坑→产物）"
        pos = found


def test_template_pitfall_section_is_mandatory_and_concrete():
    body = _template_text().split("## 踩坑", 1)[1].split("## 产物", 1)[0]
    # 必填 + 不得空话：至少 1 条，按「现象 → 原因 → 解法」写全；写不出不立项
    for keyword in ("必填", "至少 1 条", "现象", "原因", "解法", "不立项"):
        assert keyword in body, f"踩坑段约束缺失：{keyword}"


def test_template_artifacts_reproducible_and_bilingual():
    text = _template_text()
    product = text.split("## 产物", 1)[1].split("## 英文摘要", 1)[0]
    assert "可复现" in product, "产物段须要求可复现路径"
    assert "<示例>" in product or "示例" in product
    bilingual = text.split("## 英文摘要", 1)[1].split("## 相关阅读", 1)[0]
    assert "README.en.md" in bilingual, "英文摘要须指向英文 README 入口"
    assert "3 句" in text or "三句" in text, "英文摘要须给出最低句数要求"
    # 周报互链（T1 §4.2：实录文末链当期周报）
    assert "WEEKLY.md" in text


def test_template_publish_gate_five_items():
    text = _template_text()
    gate = text.split("## 发布前合规闸", 1)[1]
    assert gate.count("[ ]") == 5, "合规闸必须恰为 5 个自查项"
    for item in GATE_ITEMS:
        assert item in gate, f"合规闸缺「{item}」"
    # 占位符纪律与扫描口径写进闸门（T1 §4.4 第 1 项）
    assert "<占位符-…>" in text and "secret" in gate and "bearer" in gate


# ---------------------------------------------------------------------------
# 栏目索引：名称/定位/篇目表/节奏/标签/借鉴声明
# ---------------------------------------------------------------------------
def test_index_name_positioning_and_format():
    text = INDEX.read_text(encoding="utf-8")
    assert "构建实录" in text and "Build in Public" in text
    assert "英文的 AI 桌面助手，中文的打开方式" in text, "栏目定位须对齐主定位"
    assert "PRD-102" in text, "须说明与双语技术传播的关系"


def test_index_article_table_columns_and_no_unpublished_rows():
    text = INDEX.read_text(encoding="utf-8")
    table = text.split("## 篇目表", 1)[1].split("## 更新节奏", 1)[0]
    header = next(
        (l for l in table.splitlines() if re.match(r"^\|\s*篇目\s*\|", l)), None
    )
    assert header is not None, "篇目表缺表头（篇目 | 一句话 | 产物 | 状态）"
    for col in ("一句话", "产物", "状态"):
        assert col in header, f"篇目表缺「{col}」列"
    # T2 交付骨架：表体暂空；T3 起每行状态只允许 已发布/草案，已发布行必须链到真实存在的文章文件
    sep_re = re.compile(r"^\|[\s:|-]+\|$")
    for line in table.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or sep_re.match(stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 4 or not any(cells) or cells[0] == "篇目":
            continue
        status = cells[3]
        assert status in ("已发布", "草案"), f"篇目表状态非法：{status!r}"
        if status == "已发布":
            link = re.search(r"\]\(([^)]+\.md)\)", line)
            assert link, "已发布行必须链接文章文件"
            assert (COLUMN / link.group(1)).is_file(), f"文章不存在：{link.group(1)}"


def test_index_cadence_and_rules():
    text = INDEX.read_text(encoding="utf-8")
    assert "至少月更一篇" in text, "更新节奏基线：至少月更"
    assert "不凑数" in text, "事件加更、不凑数不补空文"
    assert "没有背书不发文" in text, "evidence 强制"
    assert "现象 → 原因 → 解法" in text, "踩坑硬约束写入运行规则"


def test_index_tags_enum_and_template_link():
    text = INDEX.read_text(encoding="utf-8")
    for tag in TAG_ENUM:
        assert tag in text, f"标签枚举缺「{tag}」"
    assert "TEMPLATE.md" in text, "索引须指向模板"
    assert "新标签" in text and "登记" in text, "新标签须先登记"


def test_index_two_layer_structure_and_weekly_division():
    text = INDEX.read_text(encoding="utf-8")
    assert "唯一事实源" in text, "文档层为单一事实源"
    assert "转写" in text, "站内层从文档层转写，不双写"
    assert "WEEKLY.md" in text, "与周报分工表"
    for dim in ("生成方式", "粒度", "读者动作", "互链"):
        assert dim in text, f"分工表缺「{dim}」维度"


def test_index_rakazo_attribution():
    text = INDEX.read_text(encoding="utf-8")
    assert "elie222/rakazo" in text and "Apache-2.0" in text
    assert "未复制上游" in text, "借鉴声明须写明未复制上游文件"


# ---------------------------------------------------------------------------
# 术语一致性（与 CI 同口径）与占位符纪律
# ---------------------------------------------------------------------------
def _load_quality_gate():
    spec = importlib.util.spec_from_file_location(
        "quality_gate", REPO / "scripts" / "quality-gate.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_column_md_pass_quality_gate_terms():
    qg = _load_quality_gate()
    files = {}
    for path in sorted(COLUMN.glob("*.md")):
        files[path.relative_to(REPO).as_posix()] = path.read_text(encoding="utf-8")
    failures = qg.check_terms(files, qg.TERMS)
    assert failures == [], f"术语一致性失败：{failures}"


def test_no_secrets_ips_or_internal_hosts():
    """PRD 红线：栏目文档不得出现真实密钥、账号、IP 或内部主机名（占位符纪律）。

    注：合规闸第 1 项按 T1 §4.4 原文记载扫描口径（`secret|password|…`），
    该说明行本身（含「自查口径」字样）不参与命中判定。"""
    secret_re = re.compile(
        r"secret|password|credential|api[-_]?key|bearer|private[-_]?key|"
        r"BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}",
        re.IGNORECASE,
    )
    ipv4_re = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
    for path in sorted(COLUMN.glob("*.md")):
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        ):
            if "自查口径" in line:
                continue
            m = secret_re.search(line)
            assert m is None, (
                f"{path}:{lineno} 疑似密钥/凭据字样：{m.group(0) if m else ''}"
            )
            m = ipv4_re.search(line)
            assert m is None, (
                f"{path}:{lineno} 出现 IP 字样（应使用占位符）：{m.group(0) if m else ''}"
            )


# ---------------------------------------------------------------------------
# T3（trend #922）：首篇已发布 + 2 篇草案大纲 + 索引表 + 仓库层入口
# ---------------------------------------------------------------------------
def _article_lines(text: str):
    return _frontmatter(text).splitlines()


def _meta_scalar(fm_lines, field: str) -> str:
    for line in fm_lines:
        if line.startswith(field + ":"):
            return line.split(":", 1)[1].strip().strip('"')
    return ""


def _meta_list(fm_lines, field: str):
    items, started = [], False
    for line in fm_lines:
        if line.startswith(field + ":"):
            started = True
            continue
        if started:
            if line.startswith("  - "):
                items.append(line.strip().lstrip("- ").strip())
            elif line.strip():
                break
    return items


def _sections(text: str):
    """返回四段小节文本（目标/过程/踩坑/产物）。"""
    parts = {}
    for i, h in enumerate(SECTION_HEADINGS):
        start = text.find(h)
        assert start != -1, f"缺 {h} 段"
        nxt = min((text.find(x) for x in SECTION_HEADINGS[i + 1 :] + ("## 英文摘要",)
                   if text.find(x) != -1), default=len(text))
        parts[h] = text[start:nxt]
    return parts


def test_first_article_published_with_full_metadata():
    text = FIRST_ARTICLE.read_text(encoding="utf-8")
    fm = _article_lines(text)
    assert _meta_scalar(fm, "status") == "已发布", "首篇必须以已发布状态交付"
    assert _meta_scalar(fm, "date") != "1970-01-01", "发布日不得留占位"
    tags = _meta_scalar(fm, "tags")
    assert tags and all(t in TAG_ENUM for t in re.findall(r"[\u4e00-\u9fff]+", tags))
    # evidence：≥1 条且全部指向本仓库公开 PR/issue（没有背书不发文，T1 §3.3）
    evidence = _meta_list(fm, "evidence")
    assert len(evidence) >= 1
    for url in evidence:
        assert re.fullmatch(
            r"https://github\.com/zhanglunet/openworker-zh-localized/(pull|issues)/\d+",
            url), f"evidence 须为本仓库公开 PR/issue 链接：{url}"
    # artifacts：≥1 条且路径真实存在（仓库内相对路径，T1 §3.3）
    artifacts = _meta_list(fm, "artifacts")
    assert len(artifacts) >= 1
    for art in artifacts:
        rel = art.split("（")[0].strip()
        assert (REPO / rel).exists(), f"artifacts 指向不存在的路径：{rel}"
    # 四段顺序 + 踩坑两条全按「现象 → 原因 → 解法」写全
    pos = -1
    body = text.split("\n---", 1)[1]
    for h in SECTION_HEADINGS:
        found = body.find(h)
        assert found != -1 and found > pos, f"{h} 段缺失或顺序不对"
        pos = found
    pitfall = _sections(text)["## 踩坑"]
    for keyword in ("现象", "原因", "解法"):
        assert pitfall.count(keyword) >= 2, f"首篇踩坑须 ≥2 条且每条含{keyword}"
    # 英文摘要 ≥3 句并指向英文入口
    bilingual = text.split("## 英文摘要", 1)[1].split("## 相关阅读", 1)[0]
    assert bilingual.count(". ") + bilingual.count(".\n") >= 3, "英文摘要须 ≥3 句"
    assert "README.en.md" in bilingual
    assert "WEEKLY.md" in text, "文末须链当期周报（互链不互替）"


def test_first_article_evidence_covers_prd155_chain():
    """首篇讲的是 PRD-155 面板：evidence 须覆盖其 T1→T5 的合并 PR（#42/#43/#44/#46/#47）。"""
    fm = _article_lines(FIRST_ARTICLE.read_text(encoding="utf-8"))
    nums = {re.search(r"/(\d+)$", u).group(1) for u in _meta_list(fm, "evidence")}
    assert nums == {"42", "43", "44", "46", "47"}, f"evidence 未覆盖面板链：{nums}"


def test_outlines_are_drafts_with_candidate_pitfalls():
    for outline in OUTLINES:
        assert outline.is_file(), f"缺草案大纲：{outline.name}"
        text = outline.read_text(encoding="utf-8")
        fm = _article_lines(text)
        assert _meta_scalar(fm, "status") == "草案"
        assert len(_meta_list(fm, "evidence")) >= 1, "立项即须有背书（没有背书不发文）"
        body = text.split("\n---", 1)[1]
        pos = -1
        for h in SECTION_HEADINGS:
            found = body.find(h)
            assert found != -1 and found > pos, f"{outline.name} 缺 {h} 段或顺序不对"
            pos = found
        pitfall = _sections(text)["## 踩坑"]
        assert "现象" in pitfall and "原因" in pitfall, "候选坑须写出现象与原因"
        assert ("待复核" in pitfall or "在途" in pitfall), "草案坑须标注核实状态"


def test_outlines_not_in_published_table_but_listed_as_drafts():
    text = INDEX.read_text(encoding="utf-8")
    table = text.split("## 篇目表", 1)[1].split("## 更新节奏", 1)[0]
    for outline in OUTLINES:
        for line in table.splitlines():
            if line.strip().startswith("|"):
                assert outline.name not in line, f"草案不得进篇目表：{outline.name}"
        assert outline.name in table, f"草案须在「进行中」清单可发现：{outline.name}"


def test_index_table_lists_published_first_article():
    text = INDEX.read_text(encoding="utf-8")
    table = text.split("## 篇目表", 1)[1].split("## 更新节奏", 1)[0]
    row = next((l for l in table.splitlines() if FIRST_ARTICLE.name in l), None)
    assert row is not None, "首篇未进篇目表"
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    assert cells[-1] == "已发布", f"首篇行状态须为已发布：{row}"
    link = re.search(r"\]\(([^)]+\.md)\)", row)
    assert link and (COLUMN / link.group(1)).is_file()


def test_repo_readme_has_column_entry():
    """仓库层入口（T1 §3.2）：README 目录/文档区放栏目链接；英文入口属 T4 双语互通。"""
    text = README_ZH.read_text(encoding="utf-8")
    assert "构建实录" in text and "Build in Public" in text, "README 缺栏目入口"
    m = re.search(r"\]\((docs/articles/build-in-public/README\.md)\)", text)
    assert m, "README 栏目入口须链到栏目索引"
    assert (REPO / m.group(1)).is_file(), "栏目索引文件不存在"
    assert "docs/articles/build-in-public/README.md](https" not in text, \
        "入口须用仓库内相对链接"
