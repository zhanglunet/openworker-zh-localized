#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD-267/T2（trend #1336）：中文实操录制管线——zh-capture-v1 最小实现。

按 PRD-267/T1 设计（docs/plans/2026-10-28-prd-267-zh-skill-recorder.md）实现 T2 范围：
  zh-capture-v1 字段白名单封闭：顶层 {schema, captured_at, user, task_summary, steps, summary}；
  step 仅 {seq, action_zh, say_zh, tool, intent_zh}——**say_zh 是口语语料来源**（技能触发词归纳用）；
  值类禁录字段出现即失败（录制前 PII 确认由调用方执行，Z 规则兜底）；
  脱敏 Z-1~Z-4 阻断式（全半角覆盖）：Z-1 手机/证件/邮箱（含全角数字）；Z-2 姓名称谓组合；
  Z-3 用户名路径 → <USER>；Z-4 内部词 → <INTERNAL>。
  最终自检双保险；全程本地零网络。示例全虚构。
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

SCHEMA = "zh-capture-v1"

RECORDING_FIELDS = ("schema", "captured_at", "user", "task_summary", "steps", "summary")
STEP_FIELDS = ("seq", "action_zh", "say_zh", "tool", "intent_zh")
FORBIDDEN_FIELDS = ("field_value", "path", "account", "screenshot", "clipboard", "value")

# Z-1 个人信息（全半角数字统一后匹配）
_Z1_PATTERNS = (
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    re.compile(r"(?<!\d)\d{17}[0-9Xx](?!\d)"),
)
# Z-2 姓名称谓组合（常见姓+称谓，全半角括号）
_Z2_RE = re.compile(r"[张王李刘陈杨黄赵周吴][一二三四五六七八九十甲乙丙丁]?（?(?:经理|总|工|老师|主任)）?")
# Z-3 用户名路径（POSIX/Windows）
_Z3_RE = re.compile(r"(?P<keep>(?:/home/|/Users/|C:\\\\Users\\\\))(?P<user>[^/\\\\]+)")
# Z-4 内部词
_Z4_RE = re.compile(r"内部系统|内网平台")


class CaptureBlocked(Exception):
    def __init__(self, rule: str, detail: str) -> None:
        super().__init__(f"[{rule}] {detail}")
        self.rule = rule
        self.detail = detail


def _normalize(text: str) -> str:
    """全角数字/字母转半角（Z-1 全半角覆盖）。"""
    return unicodedata.normalize("NFKC", text)


def _check_blockers(text: str, where: str) -> None:
    norm = _normalize(text)
    for pat in _Z1_PATTERNS:
        if pat.search(norm):
            raise CaptureBlocked("Z-1", f"{where} 命中个人信息模式（全半角归一后）")
    if _Z2_RE.search(text):
        raise CaptureBlocked("Z-2", f"{where} 命中姓名称谓组合")


def _apply_replacements(text: str) -> tuple[str, list[str]]:
    hits: list[str] = []
    if _Z3_RE.search(text):
        text = _Z3_RE.sub(lambda m: m.group("keep") + "<USER>", text)
        hits.append("Z-3")
    if _Z4_RE.search(text):
        text = _Z4_RE.sub("<INTERNAL>", text)
        hits.append("Z-4")
    return text, hits


def new_capture(captured_at: str, user: str, task_summary: str) -> dict[str, Any]:
    user, _ = _apply_replacements(user)
    _check_blockers(user, "user")
    _check_blockers(task_summary, "task_summary")
    task_summary, _ = _apply_replacements(task_summary)
    return {"schema": SCHEMA, "captured_at": captured_at, "user": user,
            "task_summary": task_summary, "steps": [], "summary": ""}


def add_step(cap: dict[str, Any], step: dict[str, Any]) -> dict[str, Any]:
    if cap.get("schema") != SCHEMA:
        raise CaptureBlocked("SCHEMA", "capture 未初始化")
    warnings: list[str] = []
    forbidden = [k for k in step if k in FORBIDDEN_FIELDS]
    if forbidden:
        raise CaptureBlocked("FORBIDDEN", f"值类禁录字段出现: {','.join(forbidden)}")
    extra = [k for k in step if k not in STEP_FIELDS]
    if extra:
        warnings.append(f"丢弃非白名单字段: {','.join(extra)}")
        step = {k: v for k, v in step.items() if k in STEP_FIELDS}
    if "seq" not in step or "action_zh" not in step:
        raise CaptureBlocked("WHITELIST", "缺少必填字段 seq/action_zh")

    for field in ("action_zh", "say_zh", "intent_zh"):
        val = step.get(field)
        if isinstance(val, str):
            _check_blockers(val, field)
            new_val, hits = _apply_replacements(val)
            if hits:
                warnings.append(f"{field} 命中 {','.join(hits)}")
            step[field] = new_val
    cap["steps"].append(step)
    cap.setdefault("_warnings", []).extend(warnings)
    return cap


def finish_capture(cap: dict[str, Any], summary: str) -> dict[str, Any]:
    _check_blockers(summary, "summary")
    summary, _ = _apply_replacements(summary)
    cap["summary"] = summary
    warnings = cap.pop("_warnings", [])
    blob = json.dumps({k: v for k, v in cap.items() if not k.startswith("_")},
                      ensure_ascii=False)
    _check_blockers(blob, "最终自检")
    cap["_warnings"] = warnings
    return cap


def dump_capture(cap: dict[str, Any]) -> str:
    out = {k: v for k, v in cap.items() if not k.startswith("_")}
    return json.dumps(out, ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] != "record":
        print("用法: zh_skill_recorder.py record <input.json> <out.json>", file=sys.stderr)
        return 2
    data = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    cap = new_capture(data["captured_at"], data["user"], data["task_summary"])
    for i, step in enumerate(data.get("steps", []), 1):
        try:
            add_step(cap, dict(step))
        except CaptureBlocked as exc:
            print(f"step {i} blocked: {exc}", file=sys.stderr)
            return 2
    cap = finish_capture(cap, data.get("summary", ""))
    Path(argv[2]).write_text(dump_capture(cap), encoding="utf-8")
    print(f"ok: {len(cap['steps'])} steps -> {argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
