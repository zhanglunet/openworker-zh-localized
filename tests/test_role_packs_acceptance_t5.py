# -*- coding: utf-8 -*-
"""PRD-183/T5 验收（trend #919）：三包演示；质量门报告齐全；无密钥。

走查口径：按 docs/role-packs-onboarding.md 的动线真实走一遍——
安装（PersonaRegistry.install_from_dir 本地目录动线 + 技能目录拷入）、
触发（skill_catalog_text 技能列表 + skill_tools 的 load_skill 真实工具路径）、
质量门（release-gate-role-packs.py 报告齐全性）、卸载/迭代、无密钥扫描。
全部走产品真实代码路径，状态落在 pytest 临时目录，不碰真实 state_dir。
"""
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROLE_PACKS = Path(REPO) / "role-packs"
ONBOARDING = Path(REPO) / "docs" / "role-packs-onboarding.md"
ACCEPTANCE_DOC = Path(REPO) / "docs" / "role-packs-acceptance.md"
PACKS = ("hr", "legal", "sales")
ALL_SKILLS = {
    "zh-sales-lead-brief", "zh-sales-followup-draft",
    "zh-contract-risk-list", "zh-legal-doc-checklist",
    "zh-hr-jd-draft", "zh-hr-interview-guide",
}
# 每包一个触发话术（取自技能 description 的触发短语——模型据 catalog 选技能的真实依据）
TRIGGERS = {
    "zh-hr-jd-draft": "帮我写个 JD",
    "zh-contract-risk-list": "看看这份合同有什么风险",
    "zh-sales-lead-brief": "做个客户速览",
}


def _load_quality_gate():
    spec = importlib.util.spec_from_file_location(
        "quality_gate", os.path.join(REPO, "scripts", "quality-gate.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# 三包演示：安装 → 技能列表 → 用户确认启用 → 触发（真实 install/load_skill 路径）
# ---------------------------------------------------------------------------
class TestThreePackDemo(unittest.TestCase):
    def _install_all(self, tmp):
        from coworker.personas.registry import PersonaRegistry
        reg = PersonaRegistry(state_path=tmp / "personas.json")
        consent = {}
        skills_dir = tmp / "skills"
        skills_dir.mkdir()
        for pack in PACKS:
            summaries = reg.install_from_dir(ROLE_PACKS / pack)  # 本地目录动线
            self.assertEqual(len(summaries), 1)
            s = summaries[0]
            self.assertEqual(s["id"], f"zh-{pack}")
            # 默认停用、不出现在选择器，等用户核对中文授权摘要后确认
            self.assertFalse(reg.is_enabled(s["id"]))
            self.assertFalse(reg.is_surfaced(s["id"]))
            self.assertEqual(s["mcp"], [])
            self.assertFalse(s["messaging"])
            consent[pack] = s
            for skill_dir in (ROLE_PACKS / pack / "skills").iterdir():
                if skill_dir.is_dir():  # README 安装动线：整目录拷入全局技能目录
                    shutil.copytree(skill_dir, skills_dir / skill_dir.name)
        return reg, skills_dir

    def test_install_creates_consent_summary_and_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            reg, _ = self._install_all(tmp)
            from coworker.personas.manifest import load_manifest_file
            for pack in PACKS:
                snapshot = tmp / "personas-installed" / f"zh-{pack}" / "manifest.md"
                self.assertTrue(snapshot.is_file(), f"{pack} 快照缺失")
                self.assertEqual(load_manifest_file(snapshot).id, f"zh-{pack}")

    def test_skill_list_shows_all_six_pack_skills_with_zh_triggers(self):
        from coworker.skills.base import SkillLoader, skill_catalog_text
        with tempfile.TemporaryDirectory() as td:
            _, skills_dir = self._install_all(Path(td))
            loader = SkillLoader([skills_dir])
            self.assertTrue(ALL_SKILLS <= set(loader.names()))
            catalog = skill_catalog_text(loader)
            for name, phrase in TRIGGERS.items():
                desc = loader.get(name).description
                self.assertIn(phrase, desc, f"{name} 的触发话术不在 description")
                self.assertIn(name, catalog)

    def test_enable_after_consent_then_trigger_each_pack(self):
        from coworker.skills.base import SkillLoader, skill_tools
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            reg, skills_dir = self._install_all(tmp)
            loader = SkillLoader([skills_dir])
            triggered_any = False
            for pack in PACKS:
                pid = f"zh-{pack}"
                reg.set_enabled(pid, True)  # 用户核对中文授权摘要后确认启用
                entry = reg.get(pid)
                self.assertIn(
                    {"name": pid},  # 选择器（sidebar）出现该角色
                    [{"name": p["name"]} for p in reg.sidebar()],
                )
                prompt = entry.agent().system_prompt
                self.assertIn("始终用中文回复", prompt)  # persona 中文提示词生效
            # 触发：每包一次真实 load_skill 工具调用
            load_skill = skill_tools(loader, allowed=set(loader.names()))[0]
            for name in TRIGGERS:
                out = load_skill(name=name)
                self.assertNotIn("error", out)
                self.assertIn("红线", out["instructions"])
                self.assertIn("占位符", out["instructions"])
                self.assertIn("不可信数据", out["instructions"])
                self.assertTrue(any("\u4e00" <= ch <= "\u9fff"
                                    for ch in out["instructions"]),
                                f"{name} 触发结果不是中文")
                triggered_any = True
            self.assertTrue(triggered_any)

    def test_iterate_uninstall_and_skill_removal(self):
        from coworker.skills.base import SkillLoader
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            reg, skills_dir = self._install_all(tmp)
            reg.uninstall("zh-legal")
            self.assertTrue(reg.get("zh-legal") is None or
                            all(p["name"] != "zh-legal" for p in reg.sidebar()))
            self.assertFalse((tmp / "personas-installed" / "zh-legal").exists())
            shutil.rmtree(skills_dir / "zh-contract-risk-list")
            loader = SkillLoader([skills_dir])
            self.assertNotIn("zh-contract-risk-list", loader.names())


# ---------------------------------------------------------------------------
# 质量门报告齐全：自测可跑、发行门报告要素完整、结论可发行
# ---------------------------------------------------------------------------
class TestQualityGateReports(unittest.TestCase):
    def test_gate_self_test_all_pass(self):
        qg = _load_quality_gate()
        import contextlib, io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            failed = qg.run_self_test()
        self.assertEqual(failed, [])
        out = buf.getvalue()
        self.assertIn("自测：20 通过 / 0 失败", out)

    def test_release_gate_report_complete_and_passes(self):
        script = os.path.join(REPO, "scripts", "release-gate-role-packs.py")
        r = subprocess.run([sys.executable, script], cwd=REPO,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        report = r.stdout
        # 报告要素：两条判据 + 自测结论 + 全量扫描口径 + 失败/错误计数 + 发行结论
        for marker in ("== 判据 1/2：quality-gate 自测 ==",
                       "== 判据 2/2：role-packs/**/*.md 全量术语一致性",
                       "发行门：自测通过；术语失败 0（放行 0）；错误 0",
                       "结论：可发行"):
            self.assertIn(marker, report)
        scanned = int(re.search(r"扫描文件 (\d+) 个", report).group(1))
        total_md = len(list(ROLE_PACKS.rglob("*.md")))
        self.assertEqual(scanned, total_md, "发行门须全量扫描 role-packs/**/*.md")

    def test_release_gate_fails_closed_on_bad_terms(self):
        """门必须能 fail：注入一个错误译法后发行门须拒绝发行（未过不可发行）。"""
        script = os.path.join(REPO, "scripts", "release-gate-role-packs.py")
        with tempfile.TemporaryDirectory() as td:
            packs = Path(td) / "role-packs"
            shutil.copytree(ROLE_PACKS, packs)
            victim = packs / "hr" / "persona.md"
            victim.write_text(
                victim.read_text(encoding="utf-8") + "\n服务商配置说明：也可叫供应商。\n",
                encoding="utf-8")
            r = subprocess.run([sys.executable, script, "--role-packs", str(packs)],
                               cwd=REPO, capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("结论：未过不可发行", r.stdout)


# ---------------------------------------------------------------------------
# 无密钥/无内网：红线扫描（角色包 + 开箱指南 + 验收记录）
# ---------------------------------------------------------------------------
SCAN_FILES = sorted(ROLE_PACKS.rglob("*.md")) + [ROLE_PACKS / "terms.txt", ONBOARDING]
if ACCEPTANCE_DOC.is_file():
    SCAN_FILES.append(ACCEPTANCE_DOC)

SECRET_RE = re.compile(
    r"secret|password|credential|api[-_]?key|bearer|"
    r"BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}"
    r"|AKIA[A-Z0-9]{16}",
    re.IGNORECASE,
)
TOKEN_ASSIGN_RE = re.compile(r"\b(token|passwd|pwd)\s*[=:]\s*\S", re.IGNORECASE)
IPV4_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
INTERNAL_HOST_RE = re.compile(
    r"\b[\w-]+\.(?:local|internal|intranet|corp|lan)\b", re.IGNORECASE)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


class TestNoSecretsOrInternalInfo(unittest.TestCase):
    def test_scope_files_scan_clean(self):
        for path in SCAN_FILES:
            self.assertTrue(path.is_file(), f"扫描对象缺失：{path}")
            for lineno, line in enumerate(
                    path.read_text(encoding="utf-8").splitlines(), 1):
                for rx, why in ((SECRET_RE, "疑似密钥/凭据字样"),
                                (TOKEN_ASSIGN_RE, "疑似令牌赋值"),
                                (IPV4_RE, "出现 IP（应用占位符）"),
                                (INTERNAL_HOST_RE, "疑似内部主机名"),
                                (EMAIL_RE, "疑似真实账号（邮箱）")):
                    m = rx.search(line)
                    self.assertIsNone(m, f"{path}:{lineno} {why}：{m.group(0) if m else ''}")

    def test_redline_declaration_present_in_packs(self):
        readme = (ROLE_PACKS / "README.md").read_text(encoding="utf-8")
        self.assertIn("无真实主机名 / IP / 账号 / 密钥", readme)


# ---------------------------------------------------------------------------
# 术语：开箱指南与验收记录不引入术语回退（与发行门同口径，含 terms.txt 合并）
# ---------------------------------------------------------------------------
class TestDocsTermsConsistency(unittest.TestCase):
    def test_onboarding_and_acceptance_docs_pass_terms(self):
        qg = _load_quality_gate()
        # 复用发行门的合并语义（脚本名带连字符，按路径加载）
        spec = importlib.util.spec_from_file_location(
            "release_gate", os.path.join(REPO, "scripts", "release-gate-role-packs.py"))
        rg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rg)
        entries, _exempt, errors = rg.parse_terms_file(
            (ROLE_PACKS / "terms.txt").read_text(encoding="utf-8"))
        self.assertEqual(errors, [])
        merged, merge_errors, _warnings = rg.merge_terms(qg.TERMS, entries)
        self.assertEqual(merge_errors, [])
        files = {str(p.relative_to(REPO)): p.read_text(encoding="utf-8")
                 for p in (ONBOARDING, ACCEPTANCE_DOC) if p.is_file()}
        failures = qg.check_terms(files, merged)
        self.assertEqual(failures, [], f"文档术语一致性失败：{failures}")


if __name__ == "__main__":
    unittest.main()
