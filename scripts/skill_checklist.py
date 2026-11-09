# -*- coding: utf-8 -*-
"""PRD-341/T2（trend issue #1620 的 T2 环节）：生产级 agent 十二原则 checklist
最小实现（声明式数据 + 机检器反射 + honest 三态）。

按 T1 设计（docs/plans/2026-11-09-prd-341-twelve-factors-design.md）
§3/§4/§6 实现，并裁决 §6 两个开放问题：

  §6.1 粒度 → **每 skill 一份报告 + 全库汇总视图**：run_checklist 逐 skill
  产出，summarize 聚合（全库 failing 清单一眼可见）；
  §6.2 人工评审留痕 → **JSON 附答**：manual_answers 参数按原则 id 附答
  （机读），答案只留痕不改状态——引擎零「manual 视为通过」路径（R4）。

数据形态（R3 数据驱动，§4）：CHECKLIST 每条
{id, principle, check_kind, check_ref?/manual_questions?}——增补/修订原则
改数据不改引擎（T4 断言：引擎零 checklist 硬编码）。

机检（P1–P9，R1 全部指向既有机检器零新建判定逻辑）：check_ref 形如
"<既有模块>.<既有函数>"（zh_trigger_registry / zh_sources /
consistency_check / zh_skill_ref / skillpack_snapshot /
cn_skill_sync_check / trigger_probe / zh_intake_gate）；引擎按 check_ref
从注入的 checkers 注册表反射取用（适配器把既有函数包成零参调用），**绑定
具体输入是调用方（T5 试运行）的职责**——本模块零判定逻辑零 IO。

适配器契约（honest 映射，R4）：零参调用返回 None（clean 约定，如
check_conflicts）或真值 → pass；False/其他假值 → fail(带 reason)；抛异常
→ fail(带 reason) 显形零伪装；check_ref 未注册 → fail 显形（零视为通过）。

R2 零复用：十二条为中文原创表述，本模块零借鉴仓符号（T4 抽样比对预埋）。
零网络；示例全虚构占位。
测试：tests/test_prd341_t2_checklist.py
"""
from __future__ import annotations

from typing import Any, Callable

#: 十二原则声明式数据（§3 表格数据化；check_ref 全部指向 scripts/ 既有模块）
CHECKLIST: list[dict[str, Any]] = [
    {"id": "P1", "principle": "入册合规：技能必须过登记册校验",
     "check_kind": "machine", "check_ref": "zh_trigger_registry.build_registry"},
    {"id": "P2", "principle": "触发词可辩护：每个触发词有收录依据与冲突处理记录",
     "check_kind": "machine", "check_ref": "zh_trigger_registry.check_conflicts"},
    {"id": "P3", "principle": "原文可溯源：规则/知识条目能回指原文",
     "check_kind": "machine", "check_ref": "zh_sources.validate_source"},
    {"id": "P4", "principle": "三层对齐：规则/知识/原文三方引用无悬空无环",
     "check_kind": "machine", "check_ref": "consistency_check.check_consistency"},
    {"id": "P5", "principle": "引用合法：@引用解析目标全部存在且无环",
     "check_kind": "machine", "check_ref": "zh_skill_ref.resolve"},
    {"id": "P6", "principle": "升级可逆：skillpack 有快照且可回滚",
     "check_kind": "machine", "check_ref": "skillpack_snapshot.restore"},
    {"id": "P7", "principle": "快照同步：cn_skill_sync_check 漂移检出为零",
     "check_kind": "machine", "check_ref": "cn_skill_sync_check.run_check"},
    {"id": "P8", "principle": "触发探针零冲突：探针样本命中预期技能",
     "check_kind": "machine", "check_ref": "trigger_probe.check_pass_criteria"},
    {"id": "P9", "principle": "敏感词闸门通过：入库词表无敏感形态",
     "check_kind": "machine", "check_ref": "zh_intake_gate.intake"},
    {"id": "P10", "principle": "描述质量人工评审：description 是否让人一眼知道边界",
     "check_kind": "manual",
     "manual_questions": ["给三个新用户读 description，能否不动手册说清何时用？",
                          "能否同样说清何时不用？"]},
    {"id": "P11", "principle": "失败模式人工评审：技能最常见的三种误用是什么、有什么护栏",
     "check_kind": "manual",
     "manual_questions": ["三种最可能误用是否各有一条护栏？",
                          "误用演练记录是否在册？"]},
    {"id": "P12", "principle": "中文措辞人工评审：触发词与示例是否口语自然",
     "check_kind": "manual",
     "manual_questions": ["非作者本人朗读能否复述用途？",
                          "触发词是否口语自然（非书面语硬凑）？"]},
]

MANUAL_IDS = frozenset(i["id"] for i in CHECKLIST if i["check_kind"] == "manual")


def run_checklist(skill_name: str, checkers: dict[str, Callable[[], Any]],
                  manual_answers: dict[str, Any] | None = None
                  ) -> dict[str, Any]:
    """跑单个 skill 的全量 checklist（§6.1 每 skill 一份）。

    checkers：{check_ref: 零参适配器}——适配器由调用方把既有机检器绑定到
    本 skill 的输入上；引擎只做 honest 映射（见模块 docstring 契约）。
    manual_answers：{原则 id: 附答}（§6.2 JSON 附答机读留痕）——只附在
    manual 项上，不改状态（R4 零视为通过）；未知 id / 指到机检项 → 显形
    ValueError。
    """
    if manual_answers:
        bad = sorted(set(manual_answers) - MANUAL_IDS)
        if bad:
            raise ValueError(f"manual_answers 指到非人工评审项或未知 id：{bad}"
                             "（附答只接受 " + "/".join(sorted(MANUAL_IDS)) + "）")
    results: list[dict[str, Any]] = []
    for item in CHECKLIST:
        if item["check_kind"] == "manual":
            entry = {"id": item["id"], "principle": item["principle"],
                     "state": "manual", "questions": item["manual_questions"]}
            if manual_answers and item["id"] in manual_answers:
                entry["answers"] = manual_answers[item["id"]]
            results.append(entry)
            continue
        ref = item["check_ref"]
        check_fn = checkers.get(ref)
        if check_fn is None:
            results.append({"id": item["id"], "principle": item["principle"],
                            "state": "fail",
                            "reason": f"{ref} 未注册适配器——如实 fail，不视为通过"})
            continue
        try:
            out = check_fn()
        except Exception as exc:  # 机检器异常 = fail 显形（零伪装）
            results.append({"id": item["id"], "principle": item["principle"],
                            "state": "fail", "reason": f"{ref} 异常：{exc}"})
            continue
        ok = out is None or bool(out)
        results.append({"id": item["id"], "principle": item["principle"],
                        "state": "pass" if ok else "fail",
                        "reason": "" if ok else f"{ref} 未过"})
    counts = {"pass": 0, "fail": 0, "manual": 0}
    for r in results:
        counts[r["state"]] += 1
    return {"skill": skill_name, "results": results, "counts": counts,
            "all_machine_pass": counts["fail"] == 0}


def summarize(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """全库汇总视图（§6.1）：逐 skill counts + 全库 failing 清单。"""
    failing = [{"skill": r["skill"], "id": res["id"],
                "reason": res.get("reason", "")}
               for r in reports for res in r["results"]
               if res["state"] == "fail"]
    totals = {"pass": 0, "fail": 0, "manual": 0}
    for r in reports:
        for k in totals:
            totals[k] += r["counts"][k]
    return {"schema": "skill-checklist-summary/v1", "skills": len(reports),
            "totals": totals, "all_machine_pass": totals["fail"] == 0,
            "failing": failing}
