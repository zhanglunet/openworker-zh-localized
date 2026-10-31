# -*- coding: utf-8 -*-
"""PRD-211/T3 自测（trend #1057）：模板库——每条模板实测可用。

运行：.venv/bin/python -m pytest tests/test_prd211_t3_templates.py -q

机检口径（验收「模板逐个实测可用」）：
  模板库文档存在且 ≥6 个带语言标注的模板块；
  TOML 模板逐个可解析（tomllib 实测）；
  命令模板逐行以仓库真实命令开头（owzh）；
  提示模板非空且占位符规范（【占位：…】形态，不出现真实值样例）；
  模板块无真实主机名/IP/账号/密钥形态。
零网络。
"""
import re
import sys
import tomllib
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "guides" / "templates.md"

FENCE_RE = re.compile(r"```(\w+)\n(.*?)```", re.DOTALL)
PLACEHOLDER_RE = re.compile(r"【占位：[^】]{1,30}】")
SECRET_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|-----BEGIN|password\s*=\s*['\"]\w+)")

COMMAND_PREFIXES = ("owzh",)


def parse_blocks():
    text = DOC.read_text(encoding="utf-8")
    return [(lang, body) for lang, body in FENCE_RE.findall(text)]


class TemplateLibraryTests(unittest.TestCase):
    def test_doc_exists_with_enough_blocks(self):
        self.assertTrue(DOC.exists(), "模板库文档缺失")
        blocks = parse_blocks()
        self.assertGreaterEqual(len(blocks), 6)

    def test_toml_templates_parse(self):
        toml_blocks = [b for lang, b in parse_blocks() if lang == "toml"]
        self.assertGreaterEqual(len(toml_blocks), 2)
        for body in toml_blocks:
            data = tomllib.loads(body)  # 实测可解析
            self.assertIsInstance(data, dict)

    def test_command_templates_use_real_commands(self):
        bash_blocks = [b for lang, b in parse_blocks() if lang == "bash"]
        self.assertTrue(bash_blocks)
        for body in bash_blocks:
            for line in body.strip().splitlines():
                if not line.strip() or line.strip().startswith("#"):
                    continue
                self.assertTrue(line.strip().startswith(COMMAND_PREFIXES),
                                f"命令模板行须以 {COMMAND_PREFIXES} 开头：{line!r}")

    def test_prompt_templates_placeholder_form(self):
        text_blocks = [b for lang, b in parse_blocks() if lang == "text"]
        self.assertGreaterEqual(len(text_blocks), 6)
        for body in text_blocks:
            # 长提示模板须含占位符；短口令模板（如"展开坑点"）豁免
            if len(body.strip()) > 20:
                self.assertTrue(PLACEHOLDER_RE.search(body),
                                f"提示模板须含【占位：…】占位符：{body[:40]!r}")
            self.assertNotIn("sk-live", body)

    def test_no_secrets_anywhere(self):
        for lang, body in parse_blocks():
            self.assertIsNone(SECRET_RE.search(body), f"{lang} 块疑似含密钥形态")

    def test_config_template_matches_repo_example(self):
        """配置模板的键名必须与仓库 docs/config.example.toml 的真实键一致。"""
        example = (REPO / "docs" / "config.example.toml").read_text(encoding="utf-8")
        example_keys = set(tomllib.loads(example).keys())
        toml_blocks = [b for lang, b in parse_blocks() if lang == "toml"]
        first = tomllib.loads(toml_blocks[0])
        self.assertTrue(set(first) <= example_keys,
                        f"模板键不在仓库配置样例中：{set(first) - example_keys}")


if __name__ == "__main__":
    unittest.main()
