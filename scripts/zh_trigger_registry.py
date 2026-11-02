#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD-239/T3（trend issue #1197）：中文触发词登记册——口语化触发词收录与冲突处理。

按 T1 设计（docs/plans/2026-10-26-cn-skill-layering-design.md）§5 实现，叠加
T2 分包（scripts/zh_skill_subpack.py 三场景包）：

  - SEED_TRIGGERS：§5.3 的 19 条种子逐条入册（§5.2 全部必填字段：entry_id
    TRG-<包>-NNN / 触发词（口语原文全貌）/ 触发词类型（句式|场景词|产物词）/
    所属技能 / 所属包 / 优先级 P0–P3 / 冲突标注 / 来源=description 抽取 /
    状态）——登记册是单一事实源，description 例句应与登记册一致；
  - 收录冲突处理（§5.4）：同触发词登记到不同技能 → RegistrationError 并列出
    冲突对象（人工消歧；不由登记册硬判）；场景词跨技能命中属已知冲突形态
    （同包多技能），条目内显式登记冲突标注与处理方式（优先级裁决/待澄清）；
  - lookup(utterance)（登记册可用的机判形态）：口语原句归一（全角→半角、去
    空白与首尾标点）后先整句精确、再包含匹配；命中按 §5.4 裁决顺序排序
    （P0 > P1 > P2 > P3，同级同技能合并、跨技能 → ambiguous 待澄清——
    **误命中可解释**：返回候选与各自优先级，不静默硬判）；停用条目不参与
    命中但保留留痕（不删行）；
  - 诚实边界（T1 §5.1 原样声明）：登记册是发行侧登记资产，**不声称运行时
    已有触发词匹配机制**——当前运行时靠 description 菜单条目由模型判断，
    本 lookup 是登记册数据的可复核命中形态，供 T4 检索适配与 T5 抽样比对。

零网络；确定性（归一与排序无随机无墙钟）；触发词全部为口语占位例句。
测试：tests/test_prd239_t3_registry.py
"""
from __future__ import annotations

import re

#: 包代码 → T2 场景包（scripts/zh_skill_subpack.py SUBPACKS 键）
PACK_OF = {"hr": "workplace", "legal": "legal-contract", "sales": "sales-marketing"}
PRIORITIES = ("P0", "P1", "P2", "P3")
TRIGGER_TYPES = ("句式", "场景词", "产物词")


class RegistrationError(ValueError):
    """收录违规（触发词跨技能冲突等——人工消歧，不由登记册硬判）。"""


def _entry(entry_id, phrase, ttype, skill, pack_code, priority, note="",
           *, conflict="无", conflict_targets=None, resolution=""):
    """§5.2 字段表的一行登记（必填齐全；冲突非「无」时对象与处理方式必填）。"""
    if conflict != "无" and (not conflict_targets or not resolution):
        raise RegistrationError(f"{entry_id}: 冲突标注非「无」时，冲突对象与处理方式必填")
    if ttype not in TRIGGER_TYPES:
        raise RegistrationError(f"{entry_id}: 触发词类型非法 {ttype!r}")
    if priority not in PRIORITIES:
        raise RegistrationError(f"{entry_id}: 优先级非法 {priority!r}")
    return {
        "entry_id": entry_id,
        "phrase": phrase,
        "type": ttype,
        "skill": skill,
        "pack": PACK_OF[pack_code],
        "priority": priority,
        "conflict": conflict,
        "conflict_targets": list(conflict_targets or []),
        "resolution": resolution,
        "source": "description 抽取（docs/plans/2026-10-26-cn-skill-layering-design.md §5.3）",
        "status": "启用",
        "note": note,
    }


def _seed_entries() -> list[dict]:
    """§5.3 的 19 条种子（逐条登记，类型/优先级按 §5.4 规则赋值并注记）。"""
    entries = [
        # zh-sales-lead-brief（sales → sales-marketing）
        ("TRG-SALES-001", "帮我整理一下这家客户", "句式", "zh-sales-lead-brief", "sales", "P1"),
        ("TRG-SALES-002", "做个客户速览", "产物词", "zh-sales-lead-brief", "sales", "P0",
         "点到技能产物名「客户速览」（P0 规则示例形态）"),
        ("TRG-SALES-003", "梳理一下决策链", "句式", "zh-sales-lead-brief", "sales", "P1"),
        ("TRG-SALES-004", "把和他们的历史沟通整理成档案", "句式", "zh-sales-lead-brief", "sales", "P1"),
        # zh-sales-followup-draft
        ("TRG-SALES-005", "写一封跟进邮件", "产物词", "zh-sales-followup-draft", "sales", "P2"),
        ("TRG-SALES-006", "帮我起草一条跟进消息", "句式", "zh-sales-followup-draft", "sales", "P1"),
        ("TRG-SALES-007", "跟进上次沟通写点什么", "句式", "zh-sales-followup-draft", "sales", "P1"),
        # zh-contract-risk-list（legal → legal-contract）
        ("TRG-LEGAL-001", "看看这份合同有什么风险", "句式", "zh-contract-risk-list", "legal", "P1"),
        ("TRG-LEGAL-002", "帮我过一遍条款", "句式", "zh-contract-risk-list", "legal", "P1"),
        ("TRG-LEGAL-003", "标出对我不利的地方", "句式", "zh-contract-risk-list", "legal", "P1"),
        ("TRG-LEGAL-004", "做一份合同风险清单", "产物词", "zh-contract-risk-list", "legal", "P0",
         "点到技能产物名（T1 §5.4 P0 规则示例原句）"),
        # zh-legal-doc-checklist
        ("TRG-LEGAL-005", "这份合同还缺什么材料", "句式", "zh-legal-doc-checklist", "legal", "P1"),
        ("TRG-LEGAL-006", "帮我核对签约要带的文件", "句式", "zh-legal-doc-checklist", "legal", "P1"),
        ("TRG-LEGAL-007", "有哪些时间节点要盯", "句式", "zh-legal-doc-checklist", "legal", "P1"),
        # 场景词「合同」同包多技能冲突（§5.2 冲突标注示范；T5 误命中验证用）
        ("TRG-LEGAL-008", "合同", "场景词", "zh-contract-risk-list", "legal", "P3",
         "场景词仅限无产物词/句式命中时的兜底",
         {"conflict": "同包多技能", "conflict_targets": ["TRG-LEGAL-009"],
          "resolution": "优先级裁决（同级 P3 → 待澄清，不由登记册硬判，运行时应反问用户）"}),
        ("TRG-LEGAL-009", "合同", "场景词", "zh-legal-doc-checklist", "legal", "P3",
         "场景词仅限无产物词/句式命中时的兜底",
         {"conflict": "同包多技能", "conflict_targets": ["TRG-LEGAL-008"],
          "resolution": "优先级裁决（同级 P3 → 待澄清，不由登记册硬判，运行时应反问用户）"}),
        # zh-hr-jd-draft（hr → workplace）
        ("TRG-HR-001", "帮我写个 JD", "句式", "zh-hr-jd-draft", "hr", "P1",
         "T1 §5.4 P1 规则示例原句"),
        ("TRG-HR-002", "起草一份岗位说明", "产物词", "zh-hr-jd-draft", "hr", "P2"),
        ("TRG-HR-003", "这个职位要招人了怎么写", "句式", "zh-hr-jd-draft", "hr", "P1"),
        # zh-hr-interview-guide
        ("TRG-HR-004", "帮我准备面试问题", "句式", "zh-hr-interview-guide", "hr", "P1"),
        ("TRG-HR-005", "出一份面试题纲", "产物词", "zh-hr-interview-guide", "hr", "P2"),
        ("TRG-HR-006", "这场面试怎么评估", "句式", "zh-hr-interview-guide", "hr", "P1"),
    ]
    return [_entry(*item[:7], **item[7]) if len(item) > 7 else _entry(*item)
            for item in entries]


def check_conflicts(entries: list[dict]) -> None:
    """收录冲突校验（§5.4）：同触发词（归一后）登记到不同技能且未标注冲突
    → RegistrationError 并列出冲突双方（人工消歧）；已按 §5.2 显式登记冲突
    标注与处理方式的条目放行（如同包多技能的场景词兜底）。"""
    seen: dict[str, dict] = {}
    for entry in entries:
        key = normalize(entry["phrase"])
        existing = seen.get(key)
        if existing and existing["skill"] != entry["skill"] \
                and existing["conflict"] == "无" and entry["conflict"] == "无":
            raise RegistrationError(
                f"触发词冲突：{entry['phrase']!r} 已登记给 {existing['skill']}"
                f"（{existing['entry_id']}），现又登记给 {entry['skill']}"
                f"（{entry['entry_id']}）——请人工消歧后再收录（§5.4）")
        seen[key] = entry


def build_registry() -> dict:
    """19 条种子 + 2 条场景词冲突示范 → 登记册（结构化机读形态）。"""
    entries = _seed_entries()
    # 收录时冲突校验：同触发词（归一后）登记到不同技能 → 拒绝（人工消歧）
    check_conflicts(entries)
    packs = sorted({e["pack"] for e in entries})
    return {
        "schema": "zh-trigger-registry/v1",
        "note": "发行侧登记资产（T1 §5.1）：不声称运行时已有触发词匹配机制；"
                "登记册是单一事实源，description 例句应与本册一致",
        "packs": packs,
        "total": len(entries),
        "entries": entries,
    }


def normalize(text: str) -> str:
    """口语原句归一：全角→半角、去全部空白与标点（保留字词全貌，仅消形差）。"""
    table = str.maketrans("，。！？：；（）「」『』、ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９",
                          "，。！？：；（）「」『』、ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
    text = (text or "").translate(table)
    return re.sub(r"[\s，。！？：；（）「」『』、,.!?;:()'\"]+", "", text).lower()


def lookup(registry: dict, utterance: str) -> dict:
    """口语触发命中（§5.4 裁决顺序）：返回 {status: hit|ambiguous|miss,
    skill?, candidates}——候选带优先级，**误命中可解释**（不静默硬判）。"""
    query = normalize(utterance)
    if not query:
        return {"status": "miss", "skill": None, "candidates": []}
    candidates = []
    for entry in registry["entries"]:
        if entry["status"] != "启用":
            continue  # 停用条目不参与命中（留痕不删行）
        phrase = normalize(entry["phrase"])
        if not phrase:
            continue
        if query == phrase:
            score = 3       # 整句精确
        elif phrase in query:
            score = 2       # 包含命中：条目短语嵌在用户长句里；反向不算——
        else:               # 裸场景词不得误中含该词的长命令句（§5.4 可解释）
            continue
        candidates.append({"entry_id": entry["entry_id"], "skill": entry["skill"],
                           "pack": entry["pack"], "priority": entry["priority"],
                           "type": entry["type"], "match": "exact" if score == 3 else "contain",
                           "phrase": entry["phrase"]})
    if not candidates:
        return {"status": "miss", "skill": None, "candidates": []}
    candidates.sort(key=lambda c: (PRIORITIES.index(c["priority"]), c["match"] != "exact",
                                   c["entry_id"]))
    top = candidates[0]
    top_group = [c for c in candidates
                 if c["priority"] == top["priority"] and c["match"] == top["match"]]
    skills = sorted({c["skill"] for c in top_group})
    if len(skills) == 1:
        return {"status": "hit", "skill": skills[0], "candidates": candidates}
    return {"status": "ambiguous", "skill": None, "candidates": candidates,
            "reason": f"同级候选跨技能（{', '.join(skills)}）：待澄清，"
                      "不由登记册硬判（§5.4 裁决顺序）"}


def coverage(registry: dict) -> dict:
    """包覆盖检查（登记册可用前提）：每包 ≥1 条启用触发词。"""
    counts: dict[str, int] = {}
    for entry in registry["entries"]:
        if entry["status"] == "启用":
            counts[entry["pack"]] = counts.get(entry["pack"], 0) + 1
    missing = [p for p in registry["packs"] if counts.get(p, 0) == 0]
    return {"counts": counts, "missing_packs": missing,
            "ok": not missing}


def disable(registry: dict, entry_id: str, reason: str) -> dict:
    """停用（不删行，保留留痕；原因必填）。"""
    if not reason.strip():
        raise RegistrationError("停用须注明原因（§5.2 状态字段口径）")
    for entry in registry["entries"]:
        if entry["entry_id"] == entry_id:
            entry["status"] = "停用"
            entry["note"] = (entry["note"] + "；" if entry["note"] else "") + f"停用原因：{reason}"
            return entry
    raise RegistrationError(f"条目不存在：{entry_id}")


def main(argv: list[str]) -> int:
    import sys
    registry = build_registry()
    if not argv:
        print(json.dumps(coverage(registry), ensure_ascii=False))
        return 0
    result = lookup(registry, " ".join(argv))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    import json
    import sys
    sys.exit(main(sys.argv[1:]))
