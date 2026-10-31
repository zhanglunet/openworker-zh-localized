#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD-212/T3（trend #1062）：中文触发词可用性抽查——装对之外还要唤得起。

按 PRD-212/T1 设计（docs/plans/2026-10-26-cn-skill-sync-checklist-design.md）§4 实现
（CN-SYNC-10~12，对应检查脚本 cn_skill_sync_check.py 的 T2 范围之外）：

  build_probe_suite(manifest)：每个 skill 生成 11+3 条探测样本——
    标准触发词 3（manifest triggers.standard[]）+ 口语变体 8（A 委托请求式 /
    B 名词主题式 / C 角色称呼式 / D 场景代入式 各 2）+ 反向样本 3（指向其他
    skill 或无关请求，每工具共享池）；
  run_probe_suite(probes, invoke_fn)：invoke_fn(utterance) → invoked_skill（注入式
    唤起，离线可跑）；逐条记 invoked(Y/N) 与 actual_skill；
  check_pass_criteria(records)：§4.3 通过标准——标准触发词 3/3；口语变体 ≥6/8
    且 A/B/C/D 每类 ≥1；反向 0 误触发；任一层失败 → FAIL 结论；
  write_probe_csv(records, path)：§4.4 probe 级记录（probe_id, skill_id, tool,
    variant_type, utterance, expected_skill, actual_skill, invoked, evidence_note,
    checked_at, checked_by）——抽查记录完整、可回溯。

零网络；示例全虚构。测试：tests/test_prd212_t3_probe.py
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

VARIANT_TYPES = ("STANDARD", "A", "B", "C", "D", "REVERSE")
ORAL_TYPES = ("A", "B", "C", "D")

# 口语变体模板（§4.1；{u} = 标准触发词或主题词，全部占位不指向真实包）
ORAL_TEMPLATES = {
    "A": ["帮我写个{u}", "能不能帮我{u}"],
    "B": ["{u}", "来一份{u}"],
    "C": ["让{u}来看看这段", "叫{u}把把关"],
    "D": ["周五要交{u}，一点思路都没有", "手头有{u}的活儿，帮我搭个架子"],
}
REVERSE_TEMPLATES = ["帮我写首诗（无关请求）", "查一下天气（无关请求）",
                     "（相邻技能的委托）帮我排个日程"]


class ProbeError(ValueError):
    """探测样本不合法（标准触发词不足/变体类缺失）。"""


def build_probe_suite(manifest: dict[str, Any], tool: str = "claude-code"
                      ) -> list[dict[str, Any]]:
    """每个 skill 生成 11 条正向 + 3 条反向（反向池跨 skill 共用，仅首个 skill 生成）。"""
    probes: list[dict[str, Any]] = []
    skills = manifest.get("skills") or []
    if not skills:
        raise ProbeError("manifest 无 skill")
    for entry in skills:
        skill_id = entry["skill_id"]
        standard = (entry.get("triggers", {}) or {}).get("standard") or []
        if len(standard) < 1:
            raise ProbeError(f"{skill_id} 缺标准触发词（triggers.standard）")
        seq = 0
        for word in standard[:3]:
            seq += 1
            probes.append({"probe_id": f"PRB-{skill_id}-{seq:03d}", "skill_id": skill_id,
                           "tool": tool, "variant_type": "STANDARD",
                           "utterance": word, "expected_skill": skill_id})
        theme = standard[0]
        seq += 1
        for vtype in ORAL_TYPES:
            for tpl in ORAL_TEMPLATES[vtype]:
                probes.append({"probe_id": f"PRB-{skill_id}-{seq:03d}", "skill_id": skill_id,
                               "tool": tool, "variant_type": vtype,
                               "utterance": tpl.format(u=theme),
                               "expected_skill": skill_id})
                seq += 1
    first = skills[0]["skill_id"]
    seq = 0
    for tpl in REVERSE_TEMPLATES:
        seq += 1
        probes.append({"probe_id": f"PRB-REV-{seq:03d}", "skill_id": first,
                       "tool": tool, "variant_type": "REVERSE",
                       "utterance": tpl, "expected_skill": first})
    return probes


def run_probe_suite(probes: list[dict[str, Any]],
                    invoke_fn: Callable[[str], str | None],
                    *, checked_by: str = "checker", checked_at: str | None = None
                    ) -> list[dict[str, Any]]:
    """逐条探测：invoke_fn(utterance) → 唤起的 skill（None=未唤起）。"""
    moment = checked_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    records = []
    for p in probes:
        actual = invoke_fn(p["utterance"])
        invoked = "Y" if actual == p["expected_skill"] else "N"
        records.append({
            "probe_id": p["probe_id"], "skill_id": p["skill_id"], "tool": p["tool"],
            "variant_type": p["variant_type"], "utterance": p["utterance"],
            "expected_skill": p["expected_skill"], "actual_skill": actual or "",
            "invoked": invoked,
            "evidence_note": "观测：工具调用指向该 SKILL.md（合成）" if invoked == "Y" else "未唤起",
            "checked_at": moment, "checked_by": checked_by,
        })
    return records


def check_pass_criteria(records: list[dict[str, Any]]) -> dict[str, Any]:
    """§4.3 通过标准：标准 3/3；口语 ≥6/8 且每类 ≥1；反向 0 误触发。"""
    standard = [r for r in records if r["variant_type"] == "STANDARD"]
    oral = [r for r in records if r["variant_type"] in ORAL_TYPES]
    reverse = [r for r in records if r["variant_type"] == "REVERSE"]
    standard_ok = bool(standard) and all(r["invoked"] == "Y" for r in standard)
    oral_hit = sum(1 for r in oral if r["invoked"] == "Y")
    by_type = {t: sum(1 for r in oral if r["variant_type"] == t and r["invoked"] == "Y")
               for t in ORAL_TYPES}
    oral_ok = len(oral) > 0 and oral_hit >= 6 and all(v >= 1 for v in by_type.values())
    false_triggers = sum(1 for r in reverse if r["invoked"] == "Y")
    reverse_ok = false_triggers == 0
    layers = {"standard": standard_ok, "oral": oral_ok, "reverse": reverse_ok}
    return {"schema": "probe-criteria-v1",
            "standard": f"{sum(1 for r in standard if r['invoked'] == 'Y')}/{len(standard)}",
            "oral": f"{oral_hit}/{len(oral)}", "oral_by_type": by_type,
            "false_triggers": false_triggers,
            "layers": layers, "verdict": "PASS" if all(layers.values()) else "FAIL"}


def write_probe_csv(records: list[dict[str, Any]], path: Path) -> Path:
    """§4.4 probe 级记录落盘（抽查记录完整、可回溯）。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["probe_id", "skill_id", "tool", "variant_type", "utterance",
              "expected_skill", "actual_skill", "invoked", "evidence_note",
              "checked_at", "checked_by"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in records:
            writer.writerow({k: r.get(k, "") for k in fields})
    return path
