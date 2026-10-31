#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD-268/T2（trend #1341）：中文公开源能力层——注册表 + 健康状态机 + doctor 最小实现。

按 PRD-268/T1 设计（docs/plans/2026-10-28-prd-268-zh-sources.md）实现 T2 范围：
  zh-source-v1 注册表校验：auth 只许 "none"、data_class 只许 "public"、
  tos_url 必填、robots_respected 必须 true，platform 封闭枚举（bilibili/xiaohongshu/generic-rss）；
  **平台级限流预算**：同平台全部源共享 requests_per_min 预算（平台维度限流器）；
  健康四态：healthy→degraded→failed；429 throttled 分列；
  doctor：中文界面人读表格 + JSON（字段名英文——机读纪律）。
  零网络（只消费调用方喂入的结果码）。被拒来源 disallowed 停用语义 T3 深化。
示例全虚构（example.com 占位）。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA = "zh-source-v1"
PLATFORMS = ("bilibili", "xiaohongshu", "generic-rss")
STATES = ("healthy", "degraded", "failed", "throttled", "disallowed")
DEFAULT_BUDGET_PER_PLATFORM = 2  # 中文平台默认保守值：2 req/min


class SourceRejected(ValueError):
    def __init__(self, source_id: str, reason: str) -> None:
        super().__init__(f"{source_id}: {reason}")
        self.source_id = source_id
        self.reason = reason


def validate_source(entry: dict[str, Any]) -> dict[str, Any]:
    sid = entry.get("source_id", "<missing>")
    if entry.get("schema") != SCHEMA:
        raise SourceRejected(sid, f"schema 必须为 {SCHEMA}")
    if entry.get("platform") not in PLATFORMS:
        raise SourceRejected(sid, f"platform 必须是 {PLATFORMS}")
    if entry.get("auth") != "none":
        raise SourceRejected(sid, "auth 必须为 none（不绕登录墙）")
    if entry.get("data_class") != "public":
        raise SourceRejected(sid, "data_class 必须为 public")
    if entry.get("robots_respected") is not True:
        raise SourceRejected(sid, "robots_respected 必须为 true（遵守 robots 硬要求）")
    primary = entry.get("primary") or {}
    if not primary.get("tos_url"):
        raise SourceRejected(sid, "primary.tos_url 必填")
    if not primary.get("url"):
        raise SourceRejected(sid, "primary.url 必填")
    return entry


class ZhSourceLayer:
    def __init__(self, entries: list[dict[str, Any]],
                 platform_budgets: dict[str, int] | None = None) -> None:
        self._sources: dict[str, dict[str, Any]] = {}
        self._health: dict[str, dict[str, Any]] = {}
        self._budgets: dict[str, int] = {}
        for entry in entries:
            validate_source(entry)
            sid = entry["source_id"]
            self._sources[sid] = entry
            self._health[sid] = {"state": "healthy", "consecutive_failures": 0,
                                  "last_error_class": None, "used_per_min": 0}
            platform = entry["platform"]
            # 平台级预算：默认保守值；同平台共享
            self._budgets.setdefault(platform,
                                      (platform_budgets or {}).get(platform, DEFAULT_BUDGET_PER_PLATFORM))

    def ids(self) -> list[str]:
        return list(self._sources)

    def platform_budget(self, platform: str) -> int:
        return self._budgets[platform]

    def try_acquire(self, source_id: str) -> bool:
        """平台维度限流器：同平台 used 总和超预算即拒绝（宁慢勿冲）。"""
        entry = self._sources[source_id]
        platform = entry["platform"]
        used = sum(h["used_per_min"] for s, h in self._health.items()
                   if self._sources[s]["platform"] == platform)
        if used >= self._budgets[platform]:
            return False
        self._health[source_id]["used_per_min"] += 1
        return True

    def record_result(self, source_id: str, status: str,
                      error_class: str | None = None) -> str:
        h = self._health[source_id]
        if status == "429":
            h["last_error_class"] = "throttled"
            h["state"] = "throttled"
        elif status == "disallowed":
            h["state"] = "disallowed"
            h["last_error_class"] = "rejected_by_platform"
        elif status == "ok":
            h["consecutive_failures"] = 0
            h["last_error_class"] = None
            h["state"] = "healthy"
        else:
            h["consecutive_failures"] += 1
            h["last_error_class"] = error_class or {"403": "forbidden", "404": "gone"}.get(status, "error")
            if status in (403, 404) or h["consecutive_failures"] >= 5:
                h["state"] = "failed"
            elif h["consecutive_failures"] >= 2:
                h["state"] = "degraded"
            else:
                h["state"] = "healthy"
        return h["state"]

    def doctor_json(self) -> dict[str, Any]:
        per_source = []
        for sid, entry in self._sources.items():
            h = self._health[sid]
            per_source.append({
                "source_id": sid, "platform": entry["platform"], "state": h["state"],
                "throttled": h["state"] == "throttled",
                "rate": {"used_per_min": h["used_per_min"],
                          "platform_budget_per_min": self._budgets[entry["platform"]]},
                "last_error_class": h["last_error_class"],
                "tos_url": entry["primary"]["tos_url"],
            })
        return {
            "schema": "zh-doctor-report-v1",
            "per_source": per_source,
            "summary": {"total": len(per_source),
                         **{s: sum(1 for p in per_source if p["state"] == s)
                             for s in ("healthy", "degraded", "failed", "throttled", "disallowed")}},
        }

    def doctor_text(self) -> str:
        """中文界面人读表格（JSON 字段名保持英文机读纪律）。"""
        state_zh = {"healthy": "健康", "degraded": "降级", "failed": "故障",
                     "throttled": "限流", "disallowed": "已停用"}
        lines = ["来源ID                平台          状态    本分钟用量/平台预算   最近错误     ToS"]
        for sid, entry in self._sources.items():
            h = self._health[sid]
            budget = self._budgets[entry["platform"]]
            lines.append(
                f"{sid:<20} {entry['platform']:<12} {state_zh[h['state']]:<6} "
                f"{h['used_per_min']}/{budget:<10} {str(h['last_error_class'] or '-'):<12} "
                f"{entry['primary']['tos_url']}")
        return "\n".join(lines) + "\n"


def load_registry(path: Path) -> tuple[list[dict[str, Any]], list[SourceRejected]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries = raw.get("sources", []) if isinstance(raw, dict) else raw
    ok, rejected = [], []
    for entry in entries:
        try:
            ok.append(validate_source(entry))
        except SourceRejected as exc:
            rejected.append(exc)
    return ok, rejected
