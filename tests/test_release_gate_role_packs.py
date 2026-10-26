# -*- coding: utf-8 -*-
"""PRD-183/T3 gate — 中文职业角色包发行门（trend #917）。

规范依据：T1 设计（docs/plans/2026-10-25-zh-role-skill-pack.md）：
- §6 发行判据：quality-gate 自测通过 + role-packs/**/*.md 全量术语一致性
  （基表 TERMS + terms.txt 合并）零失败——未过不可发行；
- §5.3 合并语义：terms.txt 只追加、不覆盖（重复且译法不同 → 失败）；
  豁免留痕区 `# exempt: 路径 :: 术语 :: 理由 :: 日期` 解析放行、残缺即失败。

常态把关：本文件随 ci.yml 的 pytest 执行——任何让 role-packs 过不了发行门的
改动都会在这里失败并阻断合并（workflows/quality-gate.yml 触发路径扩到
role-packs/** 为后续一行接入，避开在途 workflow 改动）。
"""
import importlib.util
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "release-gate-role-packs.py"
ROLE_PACKS = REPO / "role-packs"
QUALITY_GATE = REPO / "scripts" / "quality-gate.py"

# 三包最小集（T1 §4.1）的 .md 清单：每包 persona ×1 + SKILL.md ×2，加总览 README
EXPECTED_MD_COUNT = 3 * 3 + 1


def _load_gate():
    spec = importlib.util.spec_from_file_location("release_gate_role_packs", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_base_terms():
    spec = importlib.util.spec_from_file_location("quality_gate", QUALITY_GATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.TERMS


def _run(role_packs, out, quality_gate=None):
    return _load_gate().run_gate(
        role_packs, quality_gate or QUALITY_GATE, out=out)


def _write_pack(root: Path, terms: str, pages: dict) -> Path:
    """搭一个最小 role-packs 目录：terms.txt + 若干 .md。"""
    root = root / "role-packs"
    root.mkdir(parents=True, exist_ok=True)
    (root / "terms.txt").write_text(terms, encoding="utf-8")
    for rel, text in pages.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


# ---------------------------------------------------------------------------
# 判据本体：真实三包必须过发行门（未过不可发行 → CI 阻断）
# ---------------------------------------------------------------------------
def test_real_role_packs_pass_release_gate():
    out = io.StringIO()
    rc = _run(ROLE_PACKS, out)
    text = out.getvalue()
    assert rc == 0, f"真实三包未过发行门（未过不可发行）：\n{text}"
    assert "判据 1/2" in text and "判据 2/2" in text, "两道判据都要跑"
    assert re.search(r"自测：\d+ 通过 / 0 失败", text), "quality-gate 自测确有执行且全过"
    assert "扫描文件 %d 个" % EXPECTED_MD_COUNT in text, f"全量扫描口径变了：\n{text}"
    assert "结论：可发行" in text


def test_real_terms_txt_parses_clean_with_new_parser():
    rg = _load_gate()
    entries, exempt, errors = rg.parse_terms_file(
        (ROLE_PACKS / "terms.txt").read_text(encoding="utf-8"))
    assert errors == [], f"terms.txt 解析错误：{errors}"
    assert len(entries) == 13, "T1 §5.2 拍板 13 个领域词"
    assert exempt == [], "T2/T3 首版无豁免条目"


# ---------------------------------------------------------------------------
# 合并语义（T1 §5.3：只追加、不覆盖）
# ---------------------------------------------------------------------------
def test_merge_duplicate_different_translation_fails():
    rg, base = _load_gate(), _load_base_terms()
    merged, errors, _warnings = rg.merge_terms(base, [(2, "agent", "代理")])
    assert any("重复且译法不同" in e for e in errors), errors
    assert len(merged) == len(base), "与基表重复的词条不得追加进合并表"


def test_merge_duplicate_same_translation_warns_not_fails():
    rg, base = _load_gate(), _load_base_terms()
    merged, errors, warnings = rg.merge_terms(base, [(2, "agents", "智能体")])
    assert errors == [], errors
    assert any("冗余" in w for w in warnings), warnings
    assert len(merged) == len(base)


def test_merge_new_term_appended():
    rg, base = _load_gate(), _load_base_terms()
    merged, errors, _warnings = rg.merge_terms(base, [(2, "lead", "线索")])
    assert errors == [] and len(merged) == len(base) + 1


# ---------------------------------------------------------------------------
# 豁免留痕区（误杀可豁免但留痕；残缺一律 fail-closed）
# ---------------------------------------------------------------------------
WRONG_ZH_PAGE = "# 虚构示例\n\n这份纪要给了五条「总结」。\n"


def test_gate_blocks_wrong_translation_without_exempt(tmp_path):
    root = _write_pack(tmp_path, "lead=线索\n", {"sales/persona.md": WRONG_ZH_PAGE})
    out = io.StringIO()
    rc = _run(root, out)
    text = out.getvalue()
    assert rc == 1, text
    assert "总结" in text and "摘要" in text, "失败明细要指出错译与期望译法"
    assert "未过不可发行" in text


def test_exempt_line_releases_failure_and_leaves_trace(tmp_path):
    rg = _load_gate()
    root = _write_pack(tmp_path, "lead=线索\n", {"sales/persona.md": WRONG_ZH_PAGE})
    page_key = rg.rel_key(root / "sales" / "persona.md")
    (root / "terms.txt").write_text(
        "lead=线索\n\n# ---- 豁免留痕区 ----\n"
        "# exempt: %s :: summary :: 测试用虚构豁免 :: 2026-10-25\n" % page_key,
        encoding="utf-8")
    out = io.StringIO()
    rc = _run(root, out)
    text = out.getvalue()
    assert rc == 0, text
    assert "放行（豁免留痕）" in text, "放行必须在输出里留痕"
    assert page_key in text and "测试用虚构豁免" in text and "2026-10-25" in text
    assert "结论：可发行" in text


def test_malformed_exempt_line_fails_closed(tmp_path):
    root = _write_pack(
        tmp_path, "lead=线索\n# exempt: sales/persona.md :: summary :: 理由缺日期\n",
        {"sales/persona.md": WRONG_ZH_PAGE})
    out = io.StringIO()
    rc = _run(root, out)
    assert rc == 1
    assert "豁免行残缺" in out.getvalue()


def test_exempt_bad_date_fails_closed(tmp_path):
    root = _write_pack(
        tmp_path,
        "lead=线索\n# exempt: sales/persona.md :: summary :: 理由 :: 2026-13-99\n",
        {"sales/persona.md": WRONG_ZH_PAGE})
    out = io.StringIO()
    rc = _run(root, out)
    assert rc == 1
    assert "日期非法" in out.getvalue()


def test_exempt_unknown_term_fails_closed(tmp_path):
    root = _write_pack(
        tmp_path,
        "lead=线索\n# exempt: sales/persona.md :: nosuchterm :: 理由 :: 2026-10-25\n",
        {"sales/persona.md": WRONG_ZH_PAGE})
    out = io.StringIO()
    rc = _run(root, out)
    assert rc == 1
    assert "不在基表+追加表内" in out.getvalue()


def test_exempt_scoped_to_one_path_only(tmp_path):
    """豁免只放行对应路径：同款错误出现在别的文件仍须失败。"""
    rg = _load_gate()
    root = _write_pack(tmp_path, "lead=线索\n",
                       {"sales/persona.md": WRONG_ZH_PAGE,
                        "legal/persona.md": WRONG_ZH_PAGE})
    sales_key = rg.rel_key(root / "sales" / "persona.md")
    legal_key = rg.rel_key(root / "legal" / "persona.md")
    (root / "terms.txt").write_text(
        "lead=线索\n# exempt: %s :: summary :: 仅放行 sales 包 :: 2026-10-25\n" % sales_key,
        encoding="utf-8")
    out = io.StringIO()
    rc = _run(root, out)
    text = out.getvalue()
    assert rc == 1, text
    assert "放行（豁免留痕）" in text and sales_key in text, "sales 包按豁免放行"
    assert legal_key in text, "legal 包的同款错误不得被连带放行"


# ---------------------------------------------------------------------------
# 判据 1：quality-gate 自测未过 → 门整体失败（stub 验证接线）
# ---------------------------------------------------------------------------
def test_self_test_failure_blocks_release(tmp_path):
    stub = tmp_path / "stub-quality-gate.py"
    stub.write_text(
        "TERMS = [{'en': r'agents?', 'zh': '智能体', 'wrongs': []}]\n"
        "def check_terms(files, terms):\n"
        "    return []\n"
        "def run_self_test():\n"
        "    print('stub')\n"
        "    return ['stub-case']\n",
        encoding="utf-8")
    root = _write_pack(tmp_path, "lead=线索\n", {"sales/persona.md": "# 中文\n"})
    out = io.StringIO()
    rc = _run(root, out, quality_gate=stub)
    assert rc == 1
    assert "自测未过" in out.getvalue()


def test_gate_usage_errors(tmp_path):
    rg = _load_gate()
    out = io.StringIO()
    assert rg.run_gate(tmp_path / "nope", out=out) == 2
    assert rg.run_gate(ROLE_PACKS, quality_gate=tmp_path / "nope.py", out=out) == 2


# ---------------------------------------------------------------------------
# 占位符纪律：发行门脚本自身也不得带敏感字样（PRD-183 红线）
# ---------------------------------------------------------------------------
def test_gate_script_no_secrets_or_ips():
    text = SCRIPT.read_text(encoding="utf-8")
    m = re.search(
        r"secret|password|credential|api[-_]?key|bearer|private[-_]?key|"
        r"\b\d{1,3}(?:\.\d{1,3}){3}\b",
        text, re.IGNORECASE)
    assert m is None, f"发行门脚本出现敏感字样或 IP：{m.group(0) if m else ''}"
