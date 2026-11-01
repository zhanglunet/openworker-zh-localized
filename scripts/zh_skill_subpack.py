#!/usr/bin/env python3
"""PRD-239/T2：中文技能包按场景分包（每包一句话定位齐全）。"""
import json
from pathlib import Path

SUBPACKS = {
    "workplace": {"one_line": "职场场景：面试/JD/汇报/邮件等职场高频中文任务"},
    "legal-contract": {"one_line": "法务合同场景：合同预审/条款/法条等法律文书任务"},
    "sales-marketing": {"one_line": "销售营销场景：客户速览/跟单/营销文案等业务任务"},
}


def build_registry(role_packs_root: str) -> dict:
    root = Path(role_packs_root)
    skills = {}
    for pack_dir in sorted(root.iterdir()):
        if not pack_dir.is_dir():
            continue
        skills_dir = pack_dir / "skills"
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            scene = pack_dir.name  # hr/legal/sales
            subpack = SUBPACKS.get(scene, {}).get("one_line", scene)
            skills[skill_dir.name] = {"subpack": scene, "subpack_one_line": subpack,
                                      "role_pack": pack_dir.name}
    return {"schema": "zh-skill-subpack/v1", "subpacks": SUBPACKS, "skills": skills}


if __name__ == "__main__":
    import sys
    print(json.dumps(build_registry(sys.argv[1] if len(sys.argv) > 1 else "role-packs"),
                     ensure_ascii=False, indent=2))
