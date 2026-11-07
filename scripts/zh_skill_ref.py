#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD-299/T2（trend issue #1497）：中文指令 @中文技能名引用解析最小实现。

按 T1 设计（docs/plans/2026-11-04-prd-299-at-zh-skill-ref-design.md）
§3/§4/§5/§6 实现：

  - normalize(text)：确定性归一四规则（R4 显形）——全角→半角、繁体→简体
    （固定小映射表，无词典扩展）、去首尾空白、不合并中间空白；归一是规范化
    不是模糊匹配；
  - parse(raw)：@中文名 / @包/名（显式限定优先于停下问）两形态；禁止形态
    （版本后缀/通配/中间空白/双写）抛 RefSyntaxError；
  - resolve(raw, skills, *, active_pack=None)：候选集注入纯函数（技能登记
    由调用方注入）；归一后精确匹配；候选数裁决：1 → resolved；0 →
    REF_NOT_FOUND（附可用技能清单：名+一句话定位）；>1 → REF_AMBIGUOUS
    （**列出候选请用户选，不猜不按频次挑**，R1；chosen_from_candidates
    人工消歧留痕由 choose_candidate() 落审计）。**二值返回**；
  - RefAudit：解析审计（§6）——normalized 字段记录归一产物（可回放验证）、
    chosen 留痕、append-only。

零网络；示例全虚构占位。
测试：tests/test_prd299_t2_zh_skill_ref.py
"""
from __future__ import annotations

import re
from typing import Any

REF_SCHEMA = "ref-resolution/v1"

#: 错误码封闭词表（PRD-299/T3，trend #1198）：refused 的 error_code 只能取自本表，
#: 新增错误必须先改词表（穷举防漂移；测试做封闭性机判）。
ERROR_CODES = ("REF_AMBIGUOUS", "REF_NOT_FOUND", "REF_SYNTAX_ERROR")
#: 繁→简固定映射表（小表内嵌，T1 §9 开放问题 1 的 T2 落法）
_S2T_TABLE = {"報": "报", "響": "响", "語": "语", "義": "义",
              "術": "术", "據": "据", "數": "数", "寫": "写"}
S2T_MAP = str.maketrans("".join(_S2T_TABLE.keys()), "".join(_S2T_TABLE.values()))
PACK_QUALIFIED_RE = re.compile(r"^@(?P<pack>[^@\s@/]+)/(?P<name>[^@\s@/]+)$")
NAME_RE = re.compile(r"^@(?P<name>[^@\s@*/]+)$")


class RefSyntaxError(ValueError):
    """§3.2 禁止形态——出现即拒绝，不尝试理解。"""


def normalize(text: str) -> str:
    """确定性归一（R4 显形）：全角→半角 → 繁→简 → 去首尾空白。不合并中间空白。"""
    if not isinstance(text, str):
        return ""
    out = text.translate(str.maketrans(
        {chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))   # 全角 ASCII → 半角
    out = out.translate(S2T_MAP)
    return out.strip()


def parse(raw: str) -> dict[str, Any]:
    """引用语法解析：{kind: skill|qualified, name, pack_hint?}；禁止形态抛错。"""
    if not isinstance(raw, str) or not raw.strip():
        raise RefSyntaxError(f"引用为空或非字符串：{raw!r}")
    token = raw.strip()
    if token.startswith("@@") or "@" in token[1:] or '"' in token:
        raise RefSyntaxError(f"禁止形态（双写/引号/内嵌@）：{raw!r}（§3.2）")
    m = PACK_QUALIFIED_RE.match(token)
    if m:
        return {"kind": "qualified", "name": m.group("name"),
                "pack_hint": m.group("pack")}
    m = NAME_RE.match(token)
    if m:
        name = m.group("name")
        if "*" in name or "?" in name:
            raise RefSyntaxError(f"通配/正则不定义：{raw!r}（§3.2）")
        if "  " in name or re.search(r"\\s+v\\d+$", name):
            raise RefSyntaxError(
                f"禁止形态（中间空白不归一/版本后缀归包管理）：{raw!r}（§3.2）")
        return {"kind": "skill", "name": name, "pack_hint": None}
    raise RefSyntaxError(f"引用须为 @中文名 / @包/名：{raw!r}（§3.1）")


def resolve(raw: str, skills: list[dict[str, Any]], *,
            active_pack: str | None = None) -> dict[str, Any]:
    """@名→技能包 解析（§4.2）：归一后精确匹配 + 候选数裁决。

    skills：[{"name","pack","positioning"}]（注入；positioning=一句话定位，
    候选列表形态的一部分）。返回 Resolution | Refusal（二值，T1 §5）。
    """
    token = parse(raw)
    normalized = normalize(token["name"])
    pool = skills or []
    if token["kind"] == "qualified":
        # 显式限定：用户自己消歧（不算猜，T1 §4.2）
        pool = [s for s in pool if s.get("pack") == token["pack_hint"]]
    elif active_pack:
        pool = [s for s in pool if s.get("pack") == active_pack]
    hits = [s for s in pool if normalize(s.get("name", "")) == normalized]
    if len(hits) == 1:
        entry = hits[0]
        return {
            "schema": REF_SCHEMA, "raw": raw, "normalized": normalized,
            "kind": "zh-skill", "skill": entry.get("name"),
            "pack": entry.get("pack"),
            "meta_summary": {"positioning": entry.get("positioning", "")},
            "resolution": {"status": "resolved", "candidates": 1,
                           "strategy": "exact"},
        }
    if not hits:
        available = [{"skill": s.get("name"), "pack": s.get("pack"),
                      "positioning": s.get("positioning", "")}
                     for s in pool]
        return {"schema": REF_SCHEMA, "raw": raw, "normalized": normalized,
                "kind": "zh-skill", "skill": None, "pack": None,
                "meta_summary": {"available": available[:10]},
                "resolution": {"status": "refused", "error_code": "REF_NOT_FOUND",
                               "candidates": [],
                               "detail": "归一后无候选（附可用技能清单）"}}
    # 歧义：列出候选（技能名+一句话定位）请用户选——不猜不按频次挑（R1）
    candidates = [{"skill": s.get("name"), "pack": s.get("pack"),
                   "positioning": s.get("positioning", "")} for s in hits]
    return {"schema": REF_SCHEMA, "raw": raw, "normalized": normalized,
            "kind": "zh-skill", "skill": None, "pack": None,
            "meta_summary": {"candidates": candidates},
            "resolution": {"status": "refused", "error_code": "REF_AMBIGUOUS",
                           "candidates": [c["skill"] for c in candidates],
                           "detail": "列出候选请用户选，不由解析层硬判（§5/R1）"}}


def choose_candidate(outcome: dict[str, Any], skill: str, *, at: str) -> dict[str, Any]:
    """人工消歧落点：从 AMBIGUOUS 候选中选定 → 生成 resolved 产物（chosen 留痕由审计落）。"""
    cands = [c["skill"] for c in (outcome.get("meta_summary", {}).get("candidates") or [])]
    if skill not in cands:
        raise ValueError(f"选择不在候选清单内：{skill!r}（{cands}）")
    meta = dict(outcome["meta_summary"])
    entry = next(c for c in meta["candidates"] if c["skill"] == skill)
    return {**outcome, "skill": skill, "pack": entry.get("pack"),
            "meta_summary": {"positioning": entry.get("positioning", "")},
            "resolution": {"status": "resolved", "candidates": len(cands),
                           "strategy": "user_choice"},
            "chosen_at": at}


class RefAudit:
    """解析审计（§6）：append-only、normalized 可回放、chosen 留痕。"""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def log(self, raw: str, outcome: dict[str, Any], *, at: str,
            chosen: str | None = None) -> dict[str, Any]:
        res = outcome.get("resolution", {})
        entry = {"ts": at, "raw": raw, "normalized": outcome.get("normalized"),
                 "kind": outcome.get("kind"), "skill": outcome.get("skill")}
        if res.get("status") == "resolved":
            entry.update({"status": "resolved",
                          "strategy": res.get("strategy")})
            if chosen:
                entry["chosen_from_candidates"] = chosen
        else:
            entry.update({"status": "refused",
                          "candidates": res.get("candidates", []),
                          "error_code": res.get("error_code"),
                          "detail": res.get("detail")})
        self.records.append(entry)  # 只增不删
        return dict(entry)

    def resolve_logged(self, raw: str, skills: list[dict[str, Any]], *, at: str,
                       active_pack: str | None = None) -> dict[str, Any]:
        """一步解析+留痕（语法错也记审计）。"""
        try:
            outcome = resolve(raw, skills, active_pack=active_pack)
        except RefSyntaxError as exc:
            entry = {"ts": at, "raw": raw, "normalized": None, "kind": None,
                     "skill": None, "status": "refused", "candidates": [],
                     "error_code": "REF_SYNTAX_ERROR", "detail": str(exc)}
            self.records.append(entry)
            return {"refused": True, "error_code": "REF_SYNTAX_ERROR",
                    "detail": str(exc), "audit": entry}
        entry = self.log(raw, outcome, at=at)
        if outcome["resolution"]["status"] == "refused":
            return {"refused": True,
                    "error_code": outcome["resolution"]["error_code"],
                    "detail": outcome["resolution"].get("detail"),
                    "outcome": outcome, "audit": entry}
        return {"refused": False, "resolution": outcome, "audit": entry}

    def log_choice(self, raw: str, outcome: dict[str, Any], skill: str, *,
                   at: str) -> dict[str, Any]:
        """人工消歧留痕：AMBIGUOUS → 用户选定。"""
        chosen = choose_candidate(outcome, skill, at=at)
        entry = self.log(raw, chosen, at=at, chosen=skill)
        return {"refused": False, "resolution": chosen, "audit": entry}
