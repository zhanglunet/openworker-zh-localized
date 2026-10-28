#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD-285/T3（trend #1428）：中文技能包升级——升级后抽查记录正式化与落档。

T2（scripts/skillpack_snapshot.py）已给出 spot_check 抽样校验与内存态审计事件；
T3 把「抽查记录」正式化为一等存档对象（spotcheck-record-v1）并落到本地 JSONL
（audit.jsonl，append-only 机读，T1 设计 §3.4/§3.5）：

    write_spotcheck_record(result, snapshot_fp, at)
        抽查结果 → 正式记录：{schema, snapshot_fingerprint, checked, passed,
        failed, at} 六字段固定，无多余字段；
    append_record(record, audit_path)
        记录 append-only 追加进本地 JSONL 存档（目录不存在自动创建）；
    read_records(audit_path)
        全量读回（文件顺序保持，坏行逐行报错不静默跳过）；
    upgrade_flow_with_check(snapshot, restore_fn, check_fn, at, audit_path=None)
        升级→抽查→失败自动回滚 完整流程函数（抽查 failed>0 触发 restore_fn）。

纪律（T1 设计 §3.3 规则 4 / §3.4 / §3.5，PRD 验收「抽查记录字段齐全，有测试」）：
    * 记录字段固定六项，确定性优先：同输入必同记录（无自生成 uuid/时间戳），
      canonical JSON 落行——同内容必同字节，append-only 可对账；
    * checked == passed + failed 强制一致（fail-close：计数不一致拒绝入档）；
    * snapshot_fingerprint 必须是 `sha256:<hex64>` 形态（与 T2 目录清单指纹同形，
      按指纹可与快照、T2 审计事件机读串联）；
    * 存档 append-only：只追加不删改，同记录重复追加不去重（去重留给读取方）；
    * 自动回滚由调用方显式注入 restore_fn 才可能发生（决策权在调用方）——注入
      即「failed>0 自动回滚」拍板形态；check_fn/restore_fn 抛错不吞，绝不静默；
    * 本地处理零网络（PRD 第一红线）：仅 json/pathlib/datetime/typing 标准库，
      落档是本地文件追加，无任何网络调用面（T4 AST 断言在此之上钉死）；
    * 示例全中文虚构（zh-sales-lead-brief 为本仓 PRD-183 规划的虚构示例名）；
      无真实主机名、IP、账号、密钥。

划界：与 T2 模块松耦合（不 import）——result/快照按结构校验（duck type），
check_fn/restore_fn 由调用方注入（可用 T2 的 spot_check/restore 组合，测试给
端到端样例）；不做多版本历史、不碰用户偏好（skills-settings.json 不在写路径）。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

SPOTCHECK_RECORD_SCHEMA = "spotcheck-record-v1"

_RECORD_FIELDS = ("schema", "snapshot_fingerprint", "checked", "passed", "failed", "at")

_FP_PREFIX = "sha256:"
_FP_HEX_LEN = 64
_FP_HEX_CHARS = set("0123456789abcdef")


class SpotcheckArchiveError(ValueError):
    """抽查记录/存档违规——该次操作被拒绝（fail-close）。"""


def _normalize_at(at: Any) -> str:
    """时间戳归一：str 保原样（去首尾空白），datetime 取 isoformat；其余拒绝。"""
    if isinstance(at, datetime):
        return at.isoformat()
    if isinstance(at, str) and at.strip():
        return at.strip()
    raise SpotcheckArchiveError("at 必须为非空字符串或 datetime")


def _counter(result: dict[str, Any], key: str) -> int:
    value = result.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise SpotcheckArchiveError(f"抽查结果 {key} 必须为整数，得到 {value!r}")
    if value < 0:
        raise SpotcheckArchiveError(f"抽查结果 {key} 不得为负: {value}")
    return value


def write_spotcheck_record(result: Any, snapshot_fp: Any, at: Any) -> dict[str, Any]:
    """把 spot_check 抽查结果正式化为 spotcheck-record-v1 记录。

    result 为抽查结果 dict（如 skillpack_snapshot.spot_check 返回值，多余键忽略），
    须含整数 checked/passed/failed 且 checked == passed + failed；snapshot_fp 须为
    `sha256:<hex64>` 形态；at 为非空字符串或 datetime（后者取 isoformat）。
    返回固定六字段记录：{schema, snapshot_fingerprint, checked, passed, failed, at}。
    同输入必同记录（无自生成 id/时间戳）——确定性优先，append-only 可对账。
    """
    if not isinstance(result, dict):
        raise SpotcheckArchiveError("result 必须为抽查结果 dict（须含 checked/passed/failed）")
    checked = _counter(result, "checked")
    passed = _counter(result, "passed")
    failed = _counter(result, "failed")
    if checked != passed + failed:
        raise SpotcheckArchiveError(
            f"抽查结果计数不一致: checked={checked} != passed={passed} + failed={failed}，拒绝入档"
        )
    if not isinstance(snapshot_fp, str) or not snapshot_fp.startswith(_FP_PREFIX):
        raise SpotcheckArchiveError("snapshot_fingerprint 必须为 'sha256:<hex>' 形态字符串")
    hex_part = snapshot_fp[len(_FP_PREFIX):]
    if len(hex_part) != _FP_HEX_LEN or any(ch not in _FP_HEX_CHARS for ch in hex_part):
        raise SpotcheckArchiveError(f"snapshot_fingerprint 十六进制段非法: {snapshot_fp!r}")
    return {
        "schema": SPOTCHECK_RECORD_SCHEMA,
        "snapshot_fingerprint": snapshot_fp,
        "checked": checked,
        "passed": passed,
        "failed": failed,
        "at": _normalize_at(at),
    }


def _canonical_line(record: dict[str, Any]) -> str:
    """canonical JSON 行：键排序、紧凑分隔符、保 UTF-8——同内容必同字节。"""
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def append_record(record: Any, audit_path: Any) -> dict[str, Any]:
    """把记录 append-only 追加进本地 JSONL 存档（audit.jsonl）。

    record 须为含 schema=spotcheck-record-v1 与全部六字段的 dict（可 JSON 序列化）；
    audit_path 的父目录不存在自动创建，文件不存在创建，已存在则追加不覆盖。
    返回被追加的记录（原对象）。
    """
    if not isinstance(record, dict):
        raise SpotcheckArchiveError("record 必须为 dict")
    if record.get("schema") != SPOTCHECK_RECORD_SCHEMA:
        raise SpotcheckArchiveError(
            f"record schema 必须为 {SPOTCHECK_RECORD_SCHEMA}，得到 {record.get('schema')!r}"
        )
    missing = [field for field in _RECORD_FIELDS if field not in record]
    if missing:
        raise SpotcheckArchiveError(f"record 缺字段: {missing}")
    try:
        line = _canonical_line(record)
    except (TypeError, ValueError) as exc:
        raise SpotcheckArchiveError(f"record 不可 JSON 序列化: {exc}") from exc
    path = Path(audit_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return record


def read_records(audit_path: Any) -> list[dict[str, Any]]:
    """全量读回存档（文件顺序保持；append-only 流可混多种记录，不做 schema 过滤）。

    文件不存在或为空返回空列表；坏行（非 JSON / 非 JSON 对象）逐行报错并带行号，
    拒绝静默跳过（存档可信优先）。
    """
    path = Path(audit_path)
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError as exc:
            raise SpotcheckArchiveError(f"{path}:{lineno} 非 JSON 行，拒绝静默跳过: {exc}") from exc
        if not isinstance(record, dict):
            raise SpotcheckArchiveError(f"{path}:{lineno} 非 JSON 对象行，拒绝静默跳过")
        records.append(record)
    return records


def upgrade_flow_with_check(
    snapshot: Any,
    restore_fn: Any,
    check_fn: Any,
    at: Any,
    *,
    audit_path: Any | None = None,
) -> dict[str, Any]:
    """升级→抽查→失败自动回滚 的完整流程函数（抽查 failed>0 触发 restore_fn）。

    snapshot：升级前快照 dict（须含字符串 fingerprint，如 T2 take_snapshot 产物）；
    check_fn(snapshot) -> 抽查结果 dict（如 T2 spot_check，抽的是升级后的包面状态）；
    restore_fn() -> 回滚动作，仅当抽查 failed>0 时调用一次，返回值原样透传；
    at：抽查记录时间戳；audit_path：给出时抽查记录一并落档（落档在回滚成功之后）。

    返回 `{"record": spotcheck-record-v1, "rolled_back": bool, "restored": 回滚返回值|None}`。
    抽查抛错/回滚抛错原样上抛不吞（绝不静默）；回滚能力由调用方显式注入——
    不注入 restore_fn 之外的回滚通道，本函数不做任何包目录写操作。
    """
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("fingerprint"), str):
        raise SpotcheckArchiveError("snapshot 必须为含字符串 fingerprint 的快照 dict")
    if not callable(check_fn):
        raise SpotcheckArchiveError("check_fn 必须可调用")
    if not callable(restore_fn):
        raise SpotcheckArchiveError("restore_fn 必须可调用")

    result = check_fn(snapshot)
    record = write_spotcheck_record(result, snapshot["fingerprint"], at)

    rolled_back = False
    restored: Any = None
    if record["failed"] > 0:
        restored = restore_fn()
        rolled_back = True
    if audit_path is not None:
        append_record(record, audit_path)
    return {"record": record, "rolled_back": rolled_back, "restored": restored}
