#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD-240/T3（trend issue #1202）：规则层计算接口——可算规则的表达与执行。

按 T1 设计（docs/plans/2026-10-26-three-layer-knowledge-design.md）§5/§5.1/§6
实现，叠加 T2 三层迁移产物（scripts/knowledge_migration.py 的三层结构与
trace_to_source 回指）：

  - validate_rule()：§5 数据模型全字段校验（rule_id 格式 RULE-<DOMAIN>-NNNN /
    form 词表 expr|table|formula|script / inputs·outputs 封闭类型 /
    kb_refs 非空且不悬空（§6.3）/ source_refs 可选不悬空 /
    determinism 恒 strict / status 词表 / updated_at·updated_by 必填占位）；
  - evaluate_rule()：可算执行（§5.1 四条钉死）——
    * 纯函数：输出仅由声明输入决定，零外部状态/时钟/随机/网络；
    * 类型封闭：输入值按声明类型校验（string/integer/boolean/enum）；
    * 确定性：precondition 不满足 → 统一 `not_applicable`（不随机失败）；
    * 可重放：同输入必同输出；
  - 三种可执行形态（form）：`expr`（单赋值声明式表达式，ast 白名单求值——
    比较/逻辑/算术/条件表达式 + min/max/abs，**其余节点一律拒绝**）；
    `table`（判定表：match_on 精确匹配 → then 输出集）；`formula`（算术单赋值）；
    `script` **拒绝执行**（§5.1：须沙箱评审解锁，T3 不放行，给明确原因）；
  - 回指原文依据（验收「可算出结果并回指原文依据」）：结果自带 evidence——
    rule 的 kb_refs/source_refs + 经 T2 trace_to_source 解析的原文层记录
    （origin_file/line_number/raw_text）。

零网络；无时钟无随机；示例规则/数值全为占位。
测试：tests/test_prd240_t3_rule_engine.py
"""
from __future__ import annotations

import ast
import re
from typing import Any

RULE_ID_RE = re.compile(r"^RULE-[A-Z]+-[0-9]{4}$")
FORMS = ("expr", "table", "formula", "script")
EXECUTABLE_FORMS = ("expr", "table", "formula")  # script 需沙箱评审（§5.1）
STATUSES = ("draft", "active", "deprecated")
INPUT_TYPES = ("string", "integer", "boolean", "enum")
_TYPE_PY = {"string": str, "integer": int, "boolean": bool}
#: 表达式白名单函数（确定性算术；其余调用一律拒绝）
SAFE_FUNCS = {"min": min, "max": max, "abs": abs}


class RuleError(ValueError):
    """规则定义/执行违规（信息即给用户的失败原因）。"""


# ---------------------------------------------------------------------------
# §5 数据模型校验
# ---------------------------------------------------------------------------

def validate_rule(rule: dict, kb_ids: set[str], src_ids: set[str]) -> list[str]:
    """§5 全字段校验，返回错误清单（空 = 通过）。kb_ids/src_ids 为三层既有主键。"""
    errors: list[str] = []
    rule_id = rule.get("rule_id", "")
    if not RULE_ID_RE.match(rule_id):
        errors.append("rule_id 须为 RULE-<DOMAIN大写>-<4位序号>：" f"{rule_id!r}")
    for field in ("name", "body", "precondition", "determinism", "updated_at",
                  "updated_by"):
        if not rule.get(field):
            errors.append(f"缺必填字段 {field}")
    if rule.get("form") not in FORMS:
        errors.append(f"form 非法：{rule.get('form')!r}（{FORMS}）")
    if rule.get("determinism") not in (None, "strict"):
        errors.append("determinism 恒为 strict（§5.1）")
    if rule.get("status") not in STATUSES:
        errors.append(f"status 非法：{rule.get('status')!r}（{STATUSES}）")
    if not isinstance(rule.get("rule_version"), int):
        errors.append("rule_version 必须为整数修订号")
    for field in ("inputs", "outputs"):
        specs = rule.get(field)
        if not isinstance(specs, list) or not specs:
            errors.append(f"{field} 必须为非空参数表")
            continue
        for spec in specs:
            if spec.get("type") not in INPUT_TYPES and not \
                    (isinstance(spec.get("type"), str) and spec["type"].startswith("ref:")):
                errors.append(f"{field}.{spec.get('name')} 类型不封闭：{spec.get('type')!r}")
    kb_refs = rule.get("kb_refs")
    if not isinstance(kb_refs, list) or not kb_refs:
        errors.append("kb_refs 必须为非空数组（§6.2 规则→知识主链路）")
    else:
        for ref in kb_refs:
            if ref not in kb_ids:
                errors.append(f"kb_refs 悬空引用：{ref}（§6.3 不得悬空）")
    for ref in rule.get("source_refs") or []:
        if ref not in src_ids:
            errors.append(f"source_refs 悬空引用：{ref}（§6.3）")
    return errors


# ---------------------------------------------------------------------------
# ast 白名单求值（expr / formula 共用）
# ---------------------------------------------------------------------------

def _safe_eval(node: ast.AST, env: dict[str, Any]) -> Any:
    """ast 白名单求值：比较/逻辑/算术/条件/白名单函数；其余节点一律拒绝。"""
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body, env)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, bool, str)) or node.value is None:
            return node.value
        raise RuleError(f"表达式含非常量字面量：{node.value!r}")
    if isinstance(node, ast.Name):
        if node.id not in env:
            raise RuleError(f"表达式引用未声明输入：{node.id}")
        return env[node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult,
                                                            ast.Div, ast.FloorDiv, ast.Mod,
                                                            ast.Pow)):
        left = _safe_eval(node.left, env)
        right = _safe_eval(node.right, env)
        if isinstance(node.op, ast.Div) and right == 0:
            raise RuleError("除零（规则须自行用条件表达式防护）")
        op = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
              ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b,
              ast.FloorDiv: lambda a, b: a // b, ast.Mod: lambda a, b: a % b,
              ast.Pow: lambda a, b: a ** b}[type(node.op)]
        return op(left, right)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd, ast.Not)):
        value = _safe_eval(node.operand, env)
        return {ast.USub: -value, ast.UAdd: +value, ast.Not: not value}[type(node.op)]
    if isinstance(node, ast.BoolOp):
        values = [_safe_eval(v, env) for v in node.values]
        return all(values) if isinstance(node.op, ast.And) else any(values)
    if isinstance(node, ast.Compare):
        ops = {ast.Gt: lambda a, b: a > b, ast.GtE: lambda a, b: a >= b,
               ast.Lt: lambda a, b: a < b, ast.LtE: lambda a, b: a <= b,
               ast.Eq: lambda a, b: a == b, ast.NotEq: lambda a, b: a != b,
               ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b}
        left = _safe_eval(node.left, env)
        for op, comparator in zip(node.ops, node.comparators):
            if type(op) not in ops:
                raise RuleError(f"表达式含未放行比较符：{type(op).__name__}")
            right = _safe_eval(comparator, env)
            if not ops[type(op)](left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.IfExp):
        return (_safe_eval(node.body, env) if _safe_eval(node.test, env)
                else _safe_eval(node.orelse, env))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in SAFE_FUNCS:
            raise RuleError("表达式调用未放行函数（仅 min/max/abs）")
        return SAFE_FUNCS[node.func.id](*[_safe_eval(a, env) for a in node.args])
    raise RuleError(f"表达式含未放行语法：{type(node).__name__}")


def _assign_eval(body: str, env: dict[str, Any]) -> dict[str, Any]:
    """单赋值形态（`out_name = <expr>`）→ 输出集。"""
    text = (body or "").strip()
    if "=" in text and not text.startswith(("==", "!=", "<=", ">=")):
        name, _, expr = text.partition("=")
        name = name.strip()
        if not re.match(r"^[a-z_][a-z0-9_]*$", name):
            raise RuleError(f"赋值目标非法：{name!r}")
        return {name: _safe_eval(ast.parse(expr.strip(), mode="eval"), env)}
    raise RuleError("expr/formula 本体须为单赋值形态 `out_name = <表达式>`")


def _check_inputs(rule: dict, inputs: dict[str, Any]) -> None:
    """类型封闭校验（§5.1-2）：缺声明输入 / 多余输入 / 类型不符 → RuleError。"""
    declared = {spec["name"]: spec for spec in rule.get("inputs", [])}
    missing = [n for n in declared if n not in inputs]
    if missing:
        raise RuleError(f"缺声明输入：{missing}")
    extra = [n for n in inputs if n not in declared]
    if extra:
        raise RuleError(f"多余输入（不在声明参数表）：{extra}")
    for name, spec in declared.items():
        value = inputs[name]
        itype = spec["type"]
        if itype == "enum":
            allowed = spec.get("constraint") or []
            if value not in allowed:
                raise RuleError(f"输入 {name} 不在枚举约束 {allowed}：{value!r}")
        elif itype == "integer":
            if isinstance(value, bool) or not isinstance(value, int):
                raise RuleError(f"输入 {name} 须为 integer，收到 {value!r}")
        elif itype == "boolean":
            if not isinstance(value, bool):
                raise RuleError(f"输入 {name} 须为 boolean，收到 {value!r}")
        elif itype == "string":
            if not isinstance(value, str):
                raise RuleError(f"输入 {name} 须为 string，收到 {value!r}")


def _precondition_ok(rule: dict, inputs: dict[str, Any]) -> bool:
    """precondition 求值；空条件恒真。不满足 → 统一 not_applicable（§5.1-3）。"""
    text = (rule.get("precondition") or "").strip()
    if not text or text in ("-", "无条件", "always"):
        return True
    return bool(_safe_eval(ast.parse(text, mode="eval"), dict(inputs)))


def _resolve_sources(knowledge_base: dict | None, refs: list[str]) -> list[dict]:
    """回指原文依据：经 T2 trace_to_source 解析（kb 未给时返回引用键本身）。"""
    if knowledge_base is None:
        return [{"ref": ref} for ref in refs]
    from knowledge_migration import trace_to_source
    resolved = []
    for ref in refs:
        source = trace_to_source(knowledge_base, ref)
        resolved.append(source if source is not None else {"ref": ref, "missing": True})
    return resolved


def evaluate_rule(rule: dict, inputs: dict[str, Any],
                  knowledge_base: dict | None = None) -> dict:
    """可算执行（§5.1）：返回 {rule_id, status: ok|not_applicable, outputs,
    evidence}。只执行 active 且 form ∈ expr|table|formula。"""
    if rule.get("status") != "active":
        raise RuleError(f"规则 {rule.get('rule_id')!r} 状态为 {rule.get('status')!r}，"
                        "仅 active 规则可执行（draft/deprecated 不可算）")
    if rule["form"] not in EXECUTABLE_FORMS:
        raise RuleError(f"form=script 须沙箱评审后方可执行（§5.1），本接口不放行")
    _check_inputs(rule, inputs)
    kb_ids = {k["entry_id"] for k in (knowledge_base or {}).get("layers", {}).get("knowledge", [])}
    src_ids = {s["entry_id"] for s in (knowledge_base or {}).get("layers", {}).get("sources", [])}
    if rule.get("kb_refs") and knowledge_base is not None:
        dangling = [r for r in rule["kb_refs"] if r not in kb_ids]
        if dangling:
            raise RuleError(f"kb_refs 悬空引用：{dangling}（§6.3）")

    env = dict(inputs)
    if not _precondition_ok(rule, env):
        return {
            "rule_id": rule["rule_id"], "status": "not_applicable", "outputs": {},
            "evidence": {"kb_refs": list(rule.get("kb_refs", [])),
                         "source_refs": list(rule.get("source_refs", [])),
                         "sources": _resolve_sources(knowledge_base,
                                                     list(rule.get("source_refs", []))),
                         "note": "precondition 不满足 → 统一 not_applicable（§5.1-3）"},
        }
    body = rule["body"]
    if rule["form"] == "table":
        try:
            table = json_loads(body)
        except Exception as exc:  # noqa: BLE001
            raise RuleError(f"判定表本体须为 JSON：{exc}") from exc
        match_on = table.get("match_on")
        if match_on not in env:
            raise RuleError(f"判定表 match_on 未在声明输入中：{match_on!r}")
        outputs = None
        for row in table.get("rows", []):
            if env[match_on] == row.get("when"):
                outputs = dict(row.get("then", {}))
                break
        if outputs is None:
            return {
                "rule_id": rule["rule_id"], "status": "not_applicable", "outputs": {},
                "evidence": {"kb_refs": list(rule.get("kb_refs", [])),
                             "source_refs": list(rule.get("source_refs", [])),
                             "sources": _resolve_sources(knowledge_base,
                                                         list(rule.get("source_refs", []))),
                             "note": "判定表无匹配行 → 统一 not_applicable（§5.1-3）"},
            }
    else:  # expr / formula：单赋值
        outputs = _assign_eval(body, env)
    declared_out = {spec["name"] for spec in rule.get("outputs", [])}
    undeclared = sorted(set(outputs) - declared_out)
    if undeclared:
        raise RuleError(f"产出未在 outputs 参数表中声明：{undeclared}")
    return {
        "rule_id": rule["rule_id"], "status": "ok", "outputs": outputs,
        "evidence": {
            "kb_refs": list(rule.get("kb_refs", [])),
            "source_refs": list(rule.get("source_refs", [])),
            "sources": _resolve_sources(knowledge_base,
                                        list(rule.get("source_refs", [])
                                             or rule.get("kb_refs", []))),
            "note": "回指原文依据：source_refs 优先，缺省经 kb_refs 解析（T2 trace_to_source）",
        },
    }


def json_loads(text: str) -> Any:
    import json
    return json.loads(text)
