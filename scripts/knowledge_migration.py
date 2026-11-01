#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD-240/T2（trend #1201）：存量中文知识条目迁移——术语表等按三层重组。

三层结构：规则层（可算的规则）+ 知识层（可查的知识库）+ 原文层（可对的原文）。
迁移后条目可查、可回指原文。零网络。
"""
from __future__ import annotations
from pathlib import Path
from typing import Any


def migrate_terms(raw_lines: list[dict[str, Any]]) -> dict[str, Any]:
    """术语表按三层重组：rule 层（可查/可算）+ knowledge 层（结构化条目）+ source 层（原文引用）。"""
    rules_layer: list[dict[str, Any]] = []
    knowledge_layer: list[dict[str, Any]] = []
    source_layer: list[dict[str, Any]] = []
    for i, line in enumerate(raw_lines):
        entry_id = f"term-{i:04d}"
        rule = {"entry_id": entry_id, "type": "term",
                "pattern": line.get("term", ""), "replacement": line.get("standard", ""),
                "check": "terminology"}
        knowledge = {"entry_id": entry_id, "term": line.get("term", ""),
                     "standard": line.get("standard", ""),
                     "note": line.get("note", ""), "category": "terminology"}
        source = {"entry_id": entry_id, "origin_file": line.get("origin", "terms.txt"),
                  "line_number": line.get("line_number", i + 1),
                  "raw_text": line.get("raw", "")}
        rules_layer.append(rule)
        knowledge_layer.append(knowledge)
        source_layer.append(source)
    return {
        "schema": "knowledge-migration/v1",
        "layers": {"rules": rules_layer, "knowledge": knowledge_layer, "sources": source_layer},
        "total": len(raw_lines),
    }


def lookup(knowledge_base: dict[str, Any], term: str) -> list[dict[str, Any]]:
    """查询：按术语查知识层条目。"""
    return [k for k in knowledge_base["layers"]["knowledge"]
            if term.lower() in (k.get("term", "") + k.get("standard", "")).lower()]


def trace_to_source(knowledge_base: dict[str, Any], entry_id: str) -> dict[str, Any] | None:
    """回指原文：按 entry_id 查 source 层。"""
    for s in knowledge_base["layers"]["sources"]:
        if s["entry_id"] == entry_id:
            return s
    return None
