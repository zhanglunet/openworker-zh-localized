# -*- coding: utf-8 -*-
"""PRD-327/T3：国际化技能包发布闸门（trend #1604 区段）。

T2（skills/i18n-skill 双语技能包）在对外发布前必过本闸门：
- manifest 完整（name/description/description_en 成对 + version 语义化）；
- SKILL.md frontmatter name 与 manifest 一致（双载体同源）；
- description 双语成对：中文含 CJK、英文为 ASCII 技术句（PRD-102 口径）。
MATCH 唯一放行；I18N_PUBLISH_REFUSED 逐条点名，零静默。
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any

GATE_ALLOWED = "MATCH"
REFUSED = "I18N_PUBLISH_REFUSED"
CJK = re.compile(r"[\u4e00-\u9fff]")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def verify_i18n_publish(manifest: dict[str, Any], skill_md_text: str) -> dict[str, Any]:
    evidence: list[str] = []
    if not isinstance(manifest, dict):
        return {"status": "REFUSED", "evidence": ["manifest 不是 JSON 对象"]}
    name = str(manifest.get("name", "")).strip()
    if not name:
        evidence.append("manifest.name 为空")
    zh = str(manifest.get("description", ""))
    en = str(manifest.get("description_en", ""))
    if not zh or not en:
        evidence.append("description/description_en 必须成对（双语口径）")
    else:
        if not CJK.search(zh):
            evidence.append("description 应为中文句（未检出 CJK）")
        if CJK.search(en):
            evidence.append("description_en 应为英文技术句（检出 CJK）")
    if not SEMVER.match(str(manifest.get("version", ""))):
        evidence.append(f"version 非语义化：{manifest.get('version')!r}（应 x.y.z）")
    m = re.search(r"^name:\s*(\S+)", skill_md_text or "", re.M)
    fm_name = m.group(1) if m else None
    if fm_name != name:
        evidence.append(f"SKILL.md frontmatter name 与 manifest 不同源：{fm_name!r} vs {name!r}")
    if evidence:
        return {"status": "REFUSED", "evidence": evidence}
    return {"status": GATE_ALLOWED, "name": name}


def i18n_publish_gate(skill_dir: str | Path) -> dict[str, Any]:
    """闸门：读 manifest + SKILL.md → 校验（MATCH 放行 / 逐条点名零静默）。"""
    d = Path(skill_dir)
    mf, smd = d / "manifest.json", d / "SKILL.md"
    if not mf.is_file() or not smd.is_file():
        return {"allow": False, "code": REFUSED,
                "evidence": [f"缺 {'manifest.json' if not mf.is_file() else 'SKILL.md'}：{d}"]}
    manifest = json.loads(mf.read_text(encoding="utf-8"))
    verdict = verify_i18n_publish(manifest, smd.read_text(encoding="utf-8"))
    if verdict["status"] == GATE_ALLOWED:
        return {"allow": True, "code": None, "status": GATE_ALLOWED, "name": verdict["name"]}
    return {"allow": False, "code": REFUSED, "status": verdict["status"],
            "evidence": verdict["evidence"]}
