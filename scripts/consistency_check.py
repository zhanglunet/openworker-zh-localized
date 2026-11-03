#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD-240/T4（trend issue #1203）：一致性校验——规则/知识/原文三方对齐检查。

按 T1 设计（docs/plans/2026-10-26-three-layer-knowledge-design.md）§6.3/§6.4
实现，叠加 T2 三层迁移（scripts/knowledge_migration.py）：

  - check_consistency(knowledge)：三层主键集合全量收集 + 逐条比对——
    * E-DANGLING-REF 悬空引用：规则 kb_refs 指向不存在的 entry_id、
      知识条目回指的 source 缺失（§6.3 不得悬空）；
    * E-CIRCULAR-REF 循环引用：知识条目 → 规则（§6.2 禁止方向）；
    * E-ORPHAN-SOURCE 孤儿原文：原文层条目未被任何知识条目回指（提示级）；
  - 输出清单（每条 {code, location, detail}），**不一致条目可被检出并列出**
    （验收）；空清单 = 三方对齐。

零网络；确定性；全合成。
测试：tests/test_prd240_t4_consistency.py
"""
from __future__ import annotations

from typing import Any


def check_consistency(knowledge: dict[str, Any]) -> dict[str, Any]:
    """三层对齐检查，返回 {schema, issues, summary}（issues 空 = 对齐）。"""
    issues: list[dict[str, str]] = []
    layers = knowledge.get("layers", {})
    rules = layers.get("rules", [])
    entries = layers.get("knowledge", [])
    sources = layers.get("sources", [])

    rule_ids = {r.get("entry_id") for r in rules}
    entry_ids = {e.get("entry_id") for e in entries}
    source_ids = {s.get("entry_id") for s in sources}

    # §6.2 引用方向：规则 → 知识必须非空且不悬空
    for rule in rules:
        for ref in rule.get("kb_refs", []) or []:
            if ref not in entry_ids:
                issues.append({"code": "E-DANGLING-REF",
                               "location": f"rules/{rule.get('entry_id')}",
                               "detail": f"规则 kb_ref 悬空：{ref}"})
    # 知识 → 原文必须非空（§6.2 主链路）
    for entry in entries:
        origin = entry.get("origin_file")
        matched = any(s.get("origin_file") == origin for s in sources) if origin else True
        if origin and not matched:
            issues.append({"code": "E-DANGLING-REF",
                           "location": f"knowledge/{entry.get('entry_id')}",
                           "detail": f"知识条目回指原文缺失：{origin}"})
    # 知识 → 规则 禁止（§6.2 单向）
    for entry in entries:
        if entry.get("rule_ref"):
            issues.append({"code": "E-CIRCULAR-REF",
                           "location": f"knowledge/{entry.get('entry_id')}",
                           "detail": "知识条目引用规则（反向引用禁止，§6.2）"})
    # 原文孤儿（提示级，不算不一致但列出）
    referenced_origins = {e.get("origin_file") for e in entries if e.get("origin_file")}
    for source in sources:
        if source.get("origin_file") and \
                source["origin_file"] not in referenced_origins:
            issues.append({"code": "E-ORPHAN-SOURCE",
                           "location": f"sources/{source.get('entry_id')}",
                           "detail": "原文未被任何知识条目回指（提示级，§6.4）"})
    return {
        "schema": "three-layer-consistency/v1",
        "issues": issues,
        "summary": {
            "total": len(issues),
            "errors": sum(1 for i in issues if not i["code"].startswith("E-ORPHAN")),
            "warnings": sum(1 for i in issues if i["code"].startswith("E-ORPHAN")),
            "aligned": not any(i["code"] != "E-ORPHAN-SOURCE" for i in issues),
        },
    }
