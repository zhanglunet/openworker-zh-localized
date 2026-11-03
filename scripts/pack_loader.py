#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD-239/T4（trend issue #1198）：按包加载与检索适配——现有使用方式不断链。

按 T1 设计（docs/plans/2026-10-26-cn-skill-layering-design.md §1.2/§6）实现：

  - load_skills_for_runtime(role_packs_root)：扫描 role-packs/*/skills/<name>/
    SKILL.md（**现有使用方式不断链**——加载路径与既有 coworker/skills/store.py
    同构：目录下有 SKILL.md 即为技能，项目目录优先于全局），产出
    {name, path, pack, description 首行}——菜单条目形态（§1.2：命中靠
    description 文本由模型判断，运行时无独立触发词引擎——诚实边界沿 T3）；
  - search_skills(entries, query)：检索路径可用——对 description 与 name 做
    大小写不敏感子串匹配（OR），命中按 (pack, name) 排序；查询过短拒绝；
  - **不断链断言**（测试）：加载路径不依赖 registry.json/REGISTRY.md 等新增
    登记资产——登记册是发行侧资产（T3），运行时加载只认目录形态。

零网络；确定性（无墙钟无随机）；示例全占位。
测试：tests/test_prd239_t4_pack_load.py
"""
from __future__ import annotations

import re
from pathlib import Path


class SkillLoadError(ValueError):
    """技能加载/检索违规。"""


def load_skills_for_runtime(role_packs_root: str | Path) -> list[dict[str, str]]:
    """扫描 role-packs/*/skills/*/SKILL.md → 运行时菜单条目（现有方式不断链）。"""
    root = Path(role_packs_root)
    if not root.is_dir():
        raise SkillLoadError(f"role-packs 根目录不存在：{root}")
    entries: list[dict[str, str]] = []
    for pack_dir in sorted(root.iterdir()):
        skills_dir = pack_dir / "skills"
        if not pack_dir.is_dir() or not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_dir.is_dir() or not skill_md.is_file():
                continue
            text = skill_md.read_text(encoding="utf-8")
            description = ""
            match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
            if match:
                description = match.group(1).strip()
            entries.append({
                "name": skill_dir.name,
                "path": str(skill_md),
                "pack": pack_dir.name,
                "description": description,
            })
    return entries


def search_skills(entries: list[dict[str, str]], query: str, min_len: int = 2) -> list[dict]:
    """检索路径可用：description/name 大小写不敏感子串（OR），命中按序返回。"""
    terms = [t for t in re.split(r"[\s/／,，、]+", (query or "").strip()) if t]
    if not terms or min(len(t) for t in terms) < min_len:
        raise SkillLoadError(f"检索词至少 {min_len} 个字符")
    hits = []
    for entry in entries:
        haystack = f"{entry['name']} {entry['description']}".lower()
        if any(term.lower() in haystack for term in terms):
            hits.append(dict(entry))
    return sorted(hits, key=lambda e: (e["pack"], e["name"]))
