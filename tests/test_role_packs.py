# -*- coding: utf-8 -*-
"""PRD-183/T2 gate — 中文职业角色包（销售/法务/人力）三包最小集可安装性自查（trend #916）。

规范依据：T1 设计（docs/plans/2026-10-25-zh-role-skill-pack.md，PR #48）：
- §2.1 机制硬约束：包根只 persona.md 一个 .md（install_from_dir 对包根 *.md 逐个严格解析，
  多一个 README.md 即整包装不上）；安装动线只走本地目录。
- §3.2 字段表逐条对齐 coworker/personas/manifest.py 校验器（非法值 ManifestError 硬失败）。
- §3.3 正文四段式（身份与语言 / 职责边界 / 输出物 / 安全红线）。
- §4.1 三包边界、§4.2 共同红线。
- §5.3 terms.txt 只追加、不覆盖基表 TERMS。
"""
import importlib.util
import os
import re
from pathlib import Path

import coworker.agents  # noqa: F401  # 先建 agents 包再导 catalog，避免循环导入（同 test_catalog.py 顺序）
from coworker.agents.base import AgentContext  # noqa: F401
from coworker.catalog import CATALOG
from coworker.personas.manifest import load_manifest_file
from coworker.personas.registry import PersonaRegistry
from coworker.skills.base import _parse_skill
from coworker.skills.store import validate_name

REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROLE_PACKS = REPO / "role-packs"

# 每包最小集：1 persona + 2 skills（T1 §4.1）
EXPECTED = {
    "sales": {
        "id": "zh-sales",
        "name": "销售数字同事",
        "tools": ["files", "search", "todo", "sheets"],
        "skills": ["zh-sales-lead-brief", "zh-sales-followup-draft"],
        "tagline": "整理客户材料、起草跟进，报价与合同不越界",
    },
    "legal": {
        "id": "zh-legal",
        "name": "法务数字同事",
        "tools": ["files", "search", "todo"],
        "skills": ["zh-contract-risk-list", "zh-legal-doc-checklist"],
        "tagline": "条款风险提示与文件核对清单，不替代法律意见",
    },
    "hr": {
        "id": "zh-hr",
        "name": "人力数字同事",
        "tools": ["files", "search", "todo"],
        "skills": ["zh-hr-jd-draft", "zh-hr-interview-guide"],
        "tagline": "岗位说明与面试题纲草稿，录用与薪酬不越界",
    },
}


def _pack_dir(pack: str) -> Path:
    return ROLE_PACKS / pack


def _persona_path(pack: str) -> Path:
    return _pack_dir(pack) / "persona.md"


# ---------------------------------------------------------------------------
# 布局：包根只一个 .md；技能目录与清单一致（T1 §2.1 / §3.1）
# ---------------------------------------------------------------------------
def test_pack_root_has_exactly_one_md_named_persona():
    for pack in EXPECTED:
        mds = sorted(_pack_dir(pack).glob("*.md"))
        assert [p.name for p in mds] == ["persona.md"], (
            f"{pack}/ 包根只能有 persona.md 一个 .md（install_from_dir 会逐个严格解析），"
            f"实际：{[p.name for p in mds]}"
        )


def test_skill_dirs_match_manifest_and_each_has_skill_md():
    for pack, spec in EXPECTED.items():
        skills_root = _pack_dir(pack) / "skills"
        dirs = sorted(d.name for d in skills_root.iterdir() if d.is_dir())
        assert dirs == sorted(spec["skills"]), f"{pack} 技能目录与设计不一致: {dirs}"
        for name in spec["skills"]:
            assert (skills_root / name / "SKILL.md").is_file(), f"{name}/SKILL.md 缺失"


def test_overview_readme_and_terms_txt_present():
    assert (ROLE_PACKS / "README.md").is_file()
    assert (ROLE_PACKS / "terms.txt").is_file()
    readme = (ROLE_PACKS / "README.md").read_text(encoding="utf-8")
    # 总览含三包一览、安装动线与借鉴声明（T1 §3.1 / §3.4 / §1）
    for pack, spec in EXPECTED.items():
        assert spec["id"] in readme and spec["name"] in readme
    assert "本地目录" in readme and "Apache-2.0" in readme


# ---------------------------------------------------------------------------
# persona manifest：字段逐条对齐 T1 §3.2 与校验器枚举
# ---------------------------------------------------------------------------
def test_persona_manifest_fields_match_design():
    for pack, spec in EXPECTED.items():
        m = load_manifest_file(_persona_path(pack))
        assert m.id == spec["id"]
        assert m.name == spec["name"]
        assert m.tagline == spec["tagline"]
        assert m.icon == ""  # T1：GUI 图标集无核对结论前留空
        assert m.family == "knowledge"
        assert m.workspace == "deliverable"
        assert m.tools == spec["tools"]
        assert m.messaging is False and m.connectors is False
        assert m.default_permission_mode == "interactive"
        assert m.recommended_models == []  # 不绑模型（PRD 非目标：不做硬依赖）
        assert m.skills == spec["skills"]
        assert m.mcp == []
        assert m.recommends == []  # 最小集不推连接器，且禁 core
        assert m.description.strip() and re.search(r"[\u4e00-\u9fff]", m.description)


def test_persona_tools_minimal_and_known():
    for pack, spec in EXPECTED.items():
        m = load_manifest_file(_persona_path(pack))
        assert set(m.tools) <= set(CATALOG), f"{m.id} 引用了未知工具能力"
        assert "shell" not in m.tools and "git" not in m.tools  # 不做本机操作
        assert set(m.tools) == set(spec["tools"])


def test_persona_body_four_part_structure_and_redlines():
    for pack, spec in EXPECTED.items():
        m = load_manifest_file(_persona_path(pack))
        body = m.system_prompt
        # 段 1 身份与语言：以「你是」开场 + 中文回复约定（品牌词豁免口径）
        assert body.startswith("你是"), f"{m.id} 正文未以身份段开场"
        assert "始终用中文回复" in body
        # 段 2/3/4 固定标题（T1 §3.3）
        for heading in ("## 职责边界", "## 输出物", "## 安全红线"):
            assert heading in body, f"{m.id} 缺少 {heading} 段"
        # 共同红线（T1 §4.2）：占位符纪律 + 不可信数据
        assert "占位符" in body
        assert "不可信数据" in body
    legal = load_manifest_file(_persona_path("legal")).system_prompt
    assert "请咨询执业律师" in legal  # 不替代法律意见
    sales = load_manifest_file(_persona_path("sales")).system_prompt
    assert "不代发" in sales and "外发止步于草稿" in sales
    hr = load_manifest_file(_persona_path("hr")).system_prompt
    assert "不做录用决定" in hr and "歧视性筛选条件" in hr


# ---------------------------------------------------------------------------
# 技能：名字与目录严格一致、中文描述含触发短语、正文有红线
# ---------------------------------------------------------------------------
def test_skills_parse_and_name_matches_dir():
    for pack, spec in EXPECTED.items():
        for name in spec["skills"]:
            md = _pack_dir(pack) / "skills" / name / "SKILL.md"
            skill = _parse_skill(md)
            assert skill.name == name, "技能名必须与目录名严格一致"
            validate_name(skill.name)  # 名字合法且 ≤64 字符（越界会 raise）
            assert len(skill.name) <= 64
            assert re.search(r"[\u4e00-\u9fff]", skill.description)
            assert len(skill.description) >= 30, "description 质量决定技能是否被选中，须含触发短语"
            assert skill.instructions.strip()


def test_skill_body_has_redline_section():
    for pack, spec in EXPECTED.items():
        for name in spec["skills"]:
            text = (_pack_dir(pack) / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            assert "## 红线" in text
            assert "占位符" in text
            assert "不可信数据" in text


# ---------------------------------------------------------------------------
# 安装冒烟：本地目录动线（T1 §3.4）——可安装、默认停用、授权摘要是中文
# ---------------------------------------------------------------------------
def test_install_from_dir_smoke_each_pack(tmp_path):
    for pack, spec in EXPECTED.items():
        reg = PersonaRegistry(state_path=tmp_path / f"{pack}.json")
        summaries = reg.install_from_dir(_pack_dir(pack))
        assert len(summaries) == 1
        s = summaries[0]
        assert s["id"] == spec["id"] and s["name"] == spec["name"]
        assert sorted(s["tools"]) == sorted(spec["tools"])
        assert s["mcp"] == [] and s["messaging"] is False
        assert s["recommended_mode"] == "interactive"
        # 默认 disabled + unsurfaced，等用户确认（复用既有授权同意流程）
        assert reg.is_enabled(spec["id"]) is False
        assert reg.is_surfaced(spec["id"]) is False
        # 快照进托管区，manifest 可从快照重新解析
        snapshot = tmp_path / "personas-installed" / spec["id"] / "manifest.md"
        assert snapshot.is_file()
        assert load_manifest_file(snapshot).id == spec["id"]


# ---------------------------------------------------------------------------
# terms.txt：格式、只追加不覆盖、豁免留痕区（T1 §5.3）
# ---------------------------------------------------------------------------
def _load_quality_gate():
    spec = importlib.util.spec_from_file_location(
        "quality_gate", REPO / "scripts" / "quality-gate.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _terms_lines():
    lines = []
    for raw in (ROLE_PACKS / "terms.txt").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        lines.append(line)
    return lines


def test_terms_txt_format_and_only_append_semantics():
    qg = _load_quality_gate()
    base_en = {t["en"] for t in qg.TERMS}
    pairs = []
    for line in _terms_lines():
        en, zh = line.split("=", 1)
        en, zh = en.strip(), zh.strip()
        assert en and zh, f"terms.txt 行残缺：{line!r}"
        assert re.escape(en) not in base_en, (
            f"terms.txt 键 {en!r} 与基表 TERMS 重复——只追加、不覆盖，"
            f"语境分叉走备注行（T1 §5.3）"
        )
        pairs.append((en, zh))
    # T1 §5.2 拍板的 13 个领域词（onboarding 走备注，不在词条内）
    assert dict(pairs) == {
        "lead": "线索", "pipeline": "商机管道", "follow-up": "跟进",
        "quotation": "报价单", "contract": "合同", "clause": "条款",
        "liability": "责任条款", "NDA": "保密协议（NDA）", "compliance": "合规",
        "signing": "签署", "renewal": "续约", "offer letter": "录用通知",
        "job description": "岗位说明",
    }
    merged = qg.load_terms_file(ROLE_PACKS / "terms.txt")
    assert len(merged) == len(qg.TERMS) + len(pairs)  # 纯追加，未顶掉基表任何条目


def test_terms_txt_onboarding_domain_split_and_exempt_block():
    text = (ROLE_PACKS / "terms.txt").read_text(encoding="utf-8")
    # onboarding 领域分叉：只允许出现在注释备注，不作为词条
    for line in _terms_lines():
        assert not line.startswith("onboarding=")
    assert "onboarding" in text and "新手引导" in text and "入职" in text
    # 豁免留痕区：格式说明在位（T2 首版允许 0 条目）
    assert "exempt:" in text and "::" in text


# ---------------------------------------------------------------------------
# 术语一致性与占位符纪律（质量门口径预演，T3 正式接线）
# ---------------------------------------------------------------------------
def test_role_packs_md_pass_quality_gate_terms():
    qg = _load_quality_gate()
    files = {}
    for path in sorted(ROLE_PACKS.rglob("*.md")):
        files[path.relative_to(REPO).as_posix()] = path.read_text(encoding="utf-8")
    failures = qg.check_terms(files, qg.load_terms_file(ROLE_PACKS / "terms.txt"))
    assert failures == [], f"术语一致性失败：{failures}"


def test_no_secrets_ips_or_internal_hosts():
    """PRD 红线：文档与示例不得出现真实密钥、账号、IP 或内部主机名（占位符纪律）。"""
    secret_re = re.compile(
        r"secret|password|credential|api[-_]?key|bearer|private[-_]?key|"
        r"BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}",
        re.IGNORECASE,
    )
    ipv4_re = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
    for path in sorted(ROLE_PACKS.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        m = secret_re.search(text)
        assert m is None, f"{path} 疑似密钥/凭据字样：{m.group(0) if m else ''}"
        m = ipv4_re.search(text)
        assert m is None, f"{path} 出现 IP 字样（应使用占位符）：{m.group(0) if m else ''}"
