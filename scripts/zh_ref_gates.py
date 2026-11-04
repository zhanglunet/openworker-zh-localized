# -*- coding: utf-8 -*-
"""PRD-299/T3（trend issue #1498）：中文技能引用歧义闸门与人工消歧留痕闸。

按 T1 设计（docs/plans/2026-11-04-prd-299-at-zh-skill-ref-design.md）
§5/§6 实现，叠加 T2 zh_skill_ref（解析器不变，闸门消费其产物）：

  - InstructionGate：中文指令引用闸——refused → 指令不执行（NOT_FOUND 附
    可用清单/AMBIGUOUS 列候选停下问/SYNTAX_ERROR 回显；解析层零硬判零猜）；
    resolved → 透传技能与包；AMBIGUOUS → 用户选择走 choose_candidate 人工
    消歧落点（选择不在候选内即拒，chosen_from_candidates 留痕）；
  - 误命中可解释断言面：候选列表形态机判（每条含 skill+pack+positioning——
    用户看得懂为什么列出来）；
  - 错误码封闭：三码穷举；与 239 口语命中双路径优先级断言（显式 @ 引用
    优先——T4 预埋）。

零网络；示例全虚构占位。
测试：tests/test_prd299_t3_gates.py
"""
from __future__ import annotations

from typing import Any

from zh_skill_ref import ERROR_CODES, RefAudit, choose_candidate, resolve  # noqa: F401


class InstructionGate:
    """中文指令引用闸（§5）：歧义列候选请用户选，不猜；人工消歧留痕。"""

    def __init__(self) -> None:
        self.audit = RefAudit()

    def check(self, raw: str, skills: list[dict[str, Any]], *, at: str,
              active_pack: str | None = None) -> dict[str, Any]:
        try:
            outcome = resolve(raw, skills, active_pack=active_pack)
        except Exception as exc:  # RefSyntaxError
            self.audit.records.append({"ts": at, "raw": raw, "status": "refused",
                                       "error_code": "REF_SYNTAX_ERROR",
                                       "detail": str(exc)})
            return {"allow": False, "error_code": "REF_SYNTAX_ERROR",
                    "detail": str(exc), "candidates": []}
        res = outcome["resolution"]
        if res["status"] == "refused":
            self.audit.log(raw, outcome, at=at)
            return {"allow": False, "error_code": res["error_code"],
                    "detail": res.get("detail", ""),
                    "candidates": (outcome.get("meta_summary") or {})
                    .get("candidates", [])}
        entry = self.audit.log(raw, outcome, at=at)
        return {"allow": True, "error_code": None, "skill": outcome.get("skill"),
                "pack": outcome.get("pack"), "audit_entry": entry}

    def choose(self, raw: str, refused_outcome: dict[str, Any], skill: str, *,
               at: str) -> dict[str, Any]:
        """用户从候选中选定（人工消歧唯一入口；不在候选内即拒）。"""
        out = self.audit.log_choice(raw, refused_outcome, skill, at=at)
        return {"allow": True, "skill": out["resolution"]["skill"],
                "pack": out["resolution"]["pack"],
                "chosen_from_candidates": skill}
