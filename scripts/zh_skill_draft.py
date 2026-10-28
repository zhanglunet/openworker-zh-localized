#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD-267/T3（trend #1337）：中文技能草稿 + 口语化触发词。

按 PRD-267/T1 设计（docs/plans/2026-10-28-prd-267-zh-skill-recorder.md）§3.3 实现 T3 范围：
  draft_from_capture(capture, name, description) -> {"frontmatter": dict, "body_markdown": str}
    frontmatter：name/description/triggers{canonical 恰 1 条 + colloquial >=3 条}/
    required_review: true/review{state: draft, reviewer: "", decided_at: ""}/source: recorded；
    colloquial 从 say_zh 原句截取（8-24 字，真实语料优先，不编造用户没说过的"口语"）；
    say_zh 不足 3 条时按 action_zh 顺序补足到 3 条；语料仍不足则拒绝产出（宁缺毋滥）；
    canonical 由 task_summary 任务词归纳（去"示例任务："类前缀、取标点前主干、截 16 字）。
  trigger_conflict(triggers_a, triggers_b)：两技能触发词字面重叠率（交集/并集）
    > 0.5 判冲突（防误唤起）；双向对称；空集合不判冲突。
  trigger_match(draft, utterance)：触发演示——utterance 含 canonical 或任一 colloquial 即命中。
  render_markdown(draft)：SKILL.md 兼容输出（frontmatter YAML + 中文正文），确定性。
只消费 T2 录制产物（zh-capture-v1，已过 Z-1~Z-4 脱敏）；全程本地零网络。示例全虚构。
"""
from __future__ import annotations

import re
from typing import Any

SCHEMA = "zh-capture-v1"
COLLOQUIAL_MIN = 3          # 口语变体下限（T1 §3.3）
EXCERPT_MIN = 8             # 原句截取下限（短于 8 字的语料不入选）
EXCERPT_MAX = 24            # 原句截取上限
CANONICAL_MAX = 16          # canonical 任务词主干截断
CONFLICT_THRESHOLD = 0.5    # 字面重叠率（交集/并集）冲突阈值
_PUNCT = "，。！？、；：,.!?;:"
_TASK_PREFIXES = ("示例任务：", "示例任务:", "任务：", "任务:")


class DraftRejected(ValueError):
    """草稿拒绝（语料不足等）——宁缺毋滥，不编造口语。"""


def _squash(text: str) -> str:
    """去空白（触发词内不留空白，中文口语连写）。"""
    return re.sub(r"\s+", "", text or "")


def _excerpt(text: str) -> str:
    """原句截取 8-24 字：8-24 字整句入选；超长优先在 24 字内最后一个标点处截断。"""
    t = _squash(text)
    if len(t) < EXCERPT_MIN:
        return ""
    if len(t) <= EXCERPT_MAX:
        return t
    head = t[:EXCERPT_MAX]
    cut = max(head.rfind(p) for p in _PUNCT)
    if cut >= EXCERPT_MIN:  # 标点截断仍不低于 8 字才采用
        return head[:cut]
    return head


def _canonical_from_task(task_summary: str) -> str:
    """canonical：任务词归纳 1 条——去任务前缀、取首个标点前主干、截 16 字。"""
    t = (task_summary or "").strip()
    for prefix in _TASK_PREFIXES:
        if t.startswith(prefix):
            t = t[len(prefix):]
            break
    t = _squash(t)
    cut = min((i for i, ch in enumerate(t) if ch in _PUNCT), default=len(t))
    t = (t[:cut] or t)[:CANONICAL_MAX]
    if not t:
        raise DraftRejected("task_summary 无法归纳 canonical 触发词")
    return t


def draft_from_capture(capture: dict[str, Any], name: str, description: str) -> dict[str, Any]:
    """zh-capture-v1 录制产物 -> 中文技能草稿（frontmatter + 中文正文，SKILL.md 兼容）。"""
    if capture.get("schema") != SCHEMA:
        raise DraftRejected(f"capture schema 必须为 {SCHEMA}")
    steps = sorted(capture.get("steps", []), key=lambda s: s.get("seq", 0))
    if not steps:
        raise DraftRejected("capture 无步骤，无法成稿")
    canonical = _canonical_from_task(capture.get("task_summary", ""))

    # colloquial：say_zh 原句截取（真实口语优先），不足 3 条时按 action_zh 顺序补足
    seen: set[str] = set()

    def _collect(field: str) -> list[str]:
        out = []
        for step in steps:
            phrase = _excerpt(step.get(field, ""))
            if phrase and phrase not in seen and phrase != canonical:
                seen.add(phrase)
                out.append(phrase)
        return out

    colloquial = _collect("say_zh")
    if len(colloquial) < COLLOQUIAL_MIN:
        colloquial += _collect("action_zh")
    if len(colloquial) < COLLOQUIAL_MIN:
        raise DraftRejected(
            f"say_zh/action_zh 语料不足以归纳 {COLLOQUIAL_MIN} 条口语触发词"
            f"（仅得 {len(colloquial)} 条；不编造用户没说过的口语）")

    frontmatter = {
        "name": name,
        "description": description,
        "triggers": {"canonical": [canonical], "colloquial": colloquial},
        "required_review": True,
        "review": {"state": "draft", "reviewer": "", "decided_at": ""},
        "source": "recorded",
    }
    body = _body_markdown(name, capture, steps)
    return {"frontmatter": frontmatter, "body_markdown": body}


def _body_markdown(name: str, capture: dict[str, Any], steps: list[dict[str, Any]]) -> str:
    lines = [f"# {name}", "",
             f"> {capture.get('task_summary', '')}", "",
             f"- 来源：录制（zh-capture-v1，{capture.get('captured_at', '')}）",
             "- 状态：草稿（required_review: true）——未经人 review 不得入库", "",
             "## 步骤", ""]
    for step in steps:
        tool = step.get("tool", "")
        lines.append(f"{step.get('seq')}. **{step.get('action_zh', '')}**"
                     f"（工具：{tool}）——{step.get('intent_zh', '')}")
        if step.get("say_zh"):
            lines.append(f"   - 口语：「{step['say_zh']}」")
    if capture.get("summary"):
        lines += ["", "## 小结", "", capture["summary"]]
    return "\n".join(lines) + "\n"


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _yaml(value: Any, indent: int = 0) -> list[str]:
    pad = "  " * indent
    out: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                out.append(f"{pad}{key}:")
                out += _yaml(item, indent + 1)
            else:
                out.append(f"{pad}{key}: {_yaml_scalar(item)}")
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                out.append(f"{pad}-")
                out += _yaml(item, indent + 1)
            else:
                out.append(f"{pad}- {_yaml_scalar(item)}")
    else:
        out.append(f"{pad}{_yaml_scalar(value)}")
    return out


def render_markdown(draft: dict[str, Any]) -> str:
    """frontmatter（YAML）+ 中文正文 -> SKILL.md 形态文本（确定性）。"""
    fm = "\n".join(_yaml(draft["frontmatter"]))
    return f"---\n{fm}\n---\n\n{draft['body_markdown']}"


def _phrase_set(triggers: dict[str, Any]) -> set[str]:
    return {p for p in (list(triggers.get("canonical", [])) +
                        list(triggers.get("colloquial", []))) if p}


def trigger_conflict(triggers_a: dict[str, Any], triggers_b: dict[str, Any]) -> bool:
    """两技能触发词字面重叠率（交集/并集）> 0.5 判冲突；双向对称。"""
    a, b = _phrase_set(triggers_a), _phrase_set(triggers_b)
    union = a | b
    if not union:
        return False
    return len(a & b) / len(union) > CONFLICT_THRESHOLD


def trigger_match(draft: dict[str, Any], utterance: str) -> bool:
    """触发演示：utterance 含 canonical 或任一 colloquial 即命中该技能草稿。"""
    u = _squash(utterance)
    triggers = draft["frontmatter"]["triggers"]
    return any(p and p in u
               for p in list(triggers["canonical"]) + list(triggers["colloquial"]))


def main(argv: list[str]) -> int:
    if len(argv) != 4 or argv[0] != "draft":
        print("用法: zh_skill_draft.py draft <capture.json> <name> <description> "
              "-> stdout 输出 SKILL.md 形态草稿", file=__import__("sys").stderr)
        return 2
    import json
    import sys
    from pathlib import Path
    capture = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    draft = draft_from_capture(capture, argv[2], argv[3])
    sys.stdout.write(render_markdown(draft))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
