#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD-267/T4（trend #1338）：人 review 入库门——未 review 不可入库。

按 PRD-267/T1 设计（docs/plans/2026-10-28-prd-267-zh-skill-recorder.md）§3.4 实现 T4 范围：
  intake(draft, existing_triggers_list) -> {"admitted": bool, "reason": str, ...}
  三条件全过才入库（任一失败硬拒，admitted=False + 可读 reason）：
    (a) review 签字齐全：review.state == "approved" 且 reviewer/decided_at 非空
        （required_review: true 的草稿未经人 review 闸门硬拒——PRD 红线）；
    (b) 触发词冲突复检：对每个既有技能跑 zh_skill_draft.trigger_conflict
        （字面重叠率 >0.5 判冲突，防误唤起），命中即拒；
    (c) Z 复扫干净：复用 zh_skill_recorder 的阻断检查（Z-1 个人信息/Z-2 姓名称谓，
        全半角归一覆盖）对 body_markdown 与 frontmatter 全量再跑一遍——
        草稿生成后若被篡改或夹带敏感串，入库前最后一道拦截。
  通过时返回 version "0.1.0"（入库目标=既有技能注册通道，版本从 0.1.0 起）。
确定性；全程本地零网络；示例全虚构。
"""
from __future__ import annotations

import json
from typing import Any

from zh_skill_draft import trigger_conflict
from zh_skill_recorder import CaptureBlocked, _check_blockers

ENTRY_VERSION = "0.1.0"   # 入库版本从 0.1.0 起（T1 §3.4）


def _review_signed(review: Any) -> tuple[bool, str]:
    """(a) review 签字检查：state=approved 且 reviewer/decided_at 非空。"""
    if not isinstance(review, dict):
        return False, "review 块缺失——未经人 review 不可入库（required_review: true）"
    state = review.get("state", "")
    reviewer = (review.get("reviewer") or "").strip()
    decided_at = (review.get("decided_at") or "").strip()
    if state != "approved":
        return False, (f"review.state={state!r} 非 approved——"
                       "未 review 不可入库（闸门硬拒）")
    if not reviewer:
        return False, "review 已 approved 但 reviewer 为空——缺签字，不可入库"
    if not decided_at:
        return False, "review 已 approved 但 decided_at 为空——缺签字时间，不可入库"
    return True, ""


def _conflicting(existing_triggers_list: list[Any],
                 triggers: dict[str, Any]) -> tuple[bool, str]:
    """(b) 触发词冲突复检：与任一既有技能重叠率 >0.5 即拒（防误唤起）。"""
    for idx, existing in enumerate(existing_triggers_list or []):
        if trigger_conflict(triggers, existing or {}):
            return False, (f"触发词与既有技能 #{idx} 冲突（字面重叠率 >0.5）"
                           "——防误唤起，先改触发词再入库")
    return True, ""


def _z_rescan_clean(draft: dict[str, Any]) -> tuple[bool, str]:
    """(c) Z 复扫：阻断检查（Z-1/Z-2，全半角覆盖）对正文与 frontmatter 再跑一遍。"""
    body = draft.get("body_markdown", "")
    try:
        _check_blockers(body, "body_markdown 复扫")
        blob = json.dumps(draft.get("frontmatter", {}), ensure_ascii=False)
        _check_blockers(blob, "frontmatter 复扫")
    except CaptureBlocked as exc:
        return False, f"入库复扫未过：{exc}"
    return True, ""


def intake(draft: dict[str, Any], existing_triggers_list: list[dict[str, Any]]) -> dict[str, Any]:
    """人 review 入库门：三条件（review 签字/触发词无冲突/Z 复扫干净）全过才 admitted。

    任一失败返回 {"admitted": False, "reason": 可读原因}；通过返回
    {"admitted": True, "reason": ..., "version": "0.1.0"}。不抛异常（门只放行/拦截）。
    """
    fm = draft.get("frontmatter", {}) or {}
    if fm.get("required_review") is not True:
        return {"admitted": False,
                "reason": "required_review 非 true——录制产物必须走人 review 门（闸门配置错误）"}

    ok, why = _review_signed(fm.get("review"))
    if not ok:
        return {"admitted": False, "reason": why}

    ok, why = _conflicting(existing_triggers_list, fm.get("triggers", {}) or {})
    if not ok:
        return {"admitted": False, "reason": why}

    ok, why = _z_rescan_clean(draft)
    if not ok:
        return {"admitted": False, "reason": why}

    return {"admitted": True,
            "reason": "review 签字齐全 + 触发词无冲突 + Z 复扫干净——三条件全过，准予入库",
            "version": ENTRY_VERSION}


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "intake":
        print("用法: zh_intake_gate.py intake <draft.json> "
              "-> stdout 输出闸门判定 JSON（existing_triggers 用 stdin JSON 数组喂入）",
              file=__import__("sys").stderr)
        return 2
    import sys
    from pathlib import Path
    draft = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    existing = json.loads(sys.stdin.read() or "[]")
    sys.stdout.write(json.dumps(intake(draft, existing), ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
