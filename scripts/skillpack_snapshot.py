#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD-285/T2（trend #1427）：中文技能包升级——快照存储与回滚最小实现。

按 PRD-285/T1 设计（docs/plans/2026-10-29-prd-285-skillpack-upgrade-snapshot.md）
实现 T2 范围：升级确认动作前强制出一张升级前快照（包目录 + 清单指纹 + taken_at）；
升级后抽查（spot_check）失败时按快照一键还原旧包；升级 / 回滚 / 抽查记录
append-only 机读存档。本模块是 T2 最小实现（单槽、纯内存形态）：

    take_snapshot(pack_dir, taken_at)            快照（单槽，升级前调用）
    restore(snapshot=None)                       指纹校验 + 目录还原
    spot_check(snapshot, sample_paths, max_n)    抽样校验（≤5 全查、>5 字典序抽 3）
    current_snapshot() / clear_slot()            单槽查看/清空
    audit_append(events, event) / export_audit(events)   审计事件（upgraded /
                                                 rolled_back / spot_checked）追加与导出

纪律（T1 §3/§4）：
    * 单槽"上一版"：不做多版本历史（PRD 非目标）——每个槽只有一张可回滚快照，
      新快照顶替旧快照（旧快照由调用方转入 archive 只读留档，不在本模块范围）；
    * 清单指纹：包内全部文件按相对路径排序，取 `[{path, sha256, bytes}]` 清单的
      canonical JSON sha256（`sha256:<hex>` 形态）——还原前重算必须与记录一致，
      任一不符即 FingerprintMismatch，绝不静默半还原；
    * 目录还原：restore 返回 `{rel: content}` 的旧包内容（与 take_snapshot 的
      pack_dir 同形，调用方写回技能文件夹即目录级覆盖，folder-is-truth，
      加载器零改动）；还原不顶替单槽——回滚可再回滚；
    * 抽查：样本 ≤5 个全查；>5 个按字典序取前 max_n（默认 3，确定性抽样，
      不引入随机性）；逐文件重算 sha256 与记录比对，缺失/不符计入 failed，
      返回 `{checked, passed, failed, ...}`；
    * 审计事件：append-only 列表，change_type ∈ {upgraded, rolled_back,
      spot_checked}，同 event id 不可重放，导出可 json.dumps（机读）；
    * 全链零网络（PRD 第一红线）：只依赖 copy/hashlib/json/uuid/datetime，
      纯内存对象，无任何 I/O 与网络调用面（T4 AST 断言在此最小形态上钉死）；
    * 示例全中文虚构（zh-sales-lead-brief 等为本仓 PRD-183 规划的虚构示例名）；
      不含真实主机名、IP、账号、密钥。

划界：不自动生成技能（PRD-267 领域）；不碰用户偏好（skills-settings.json 不在
快照与还原范围）；183 明确 manifest 无版本字段 → 包身份以指纹承载，不自造版本。
"""

from __future__ import annotations

import copy
import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

SNAPSHOT_SCHEMA = "skillpack-snapshot-v1"

#: 抽样策略（T1 §3.4）：样本 ≤5 全查；>5 按字典序取前 max_n（默认 3）。
SPOT_CHECK_ALL_MAX = 5
SPOT_CHECK_DEFAULT_N = 3

#: 审计事件 change_type（T2 范围：升级 / 回滚 / 抽查记录一并存档）。
CHANGE_TYPES = ("upgraded", "rolled_back", "spot_checked")

#: 审计 actor 只记角色不记个人身份。
ACTOR_ROLES = ("operator", "admin", "system")

_EVENT_ID_PREFIX = "spe-"

# 单槽：当前可回滚的"上一版"升级前快照。新快照顶替旧快照（T1 §3.3 规则 1/3）。
_SLOT: dict[str, Any] | None = None


class SkillpackSnapshotError(ValueError):
    """快照/还原/抽查/审计违规——该次操作被拒绝（fail-close）。"""


class FingerprintMismatch(SkillpackSnapshotError):
    """还原前重算指纹与快照记录不一致——快照被篡改或结构缺损，拒绝还原。"""


class AuditEventError(SkillpackSnapshotError):
    """审计事件缺字段/类型未知/同 id 重放——该行被拒绝追加。"""


def _canonical_json(obj: Any) -> str:
    """canonical JSON：键排序、紧凑分隔符、保 UTF-8——同内容必同串。"""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _normalize_taken_at(taken_at: Any) -> str:
    if isinstance(taken_at, datetime):
        return taken_at.isoformat()
    if isinstance(taken_at, str) and taken_at.strip():
        return taken_at.strip()
    raise SkillpackSnapshotError("taken_at 必须为非空字符串或 datetime")


def _file_record(content: Any) -> dict[str, Any]:
    """单文件记录：{content, sha256, bytes}（T1 §3.2 目录清单的最小单元）。"""
    if not isinstance(content, str):
        raise SkillpackSnapshotError("文件内容必须为 str（UTF-8 文本）")
    payload = content.encode("utf-8")
    return {
        "content": content,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }


def dir_fingerprint(files: dict[str, dict[str, Any]]) -> str:
    """目录清单指纹：全部文件按相对路径排序，取 `[{path, sha256, bytes}]`
    canonical JSON 的 `sha256:<hex>`（T1 §3.2 dir_fingerprint 定义）。"""
    manifest = [
        {"path": rel, "sha256": rec["sha256"], "bytes": rec["bytes"]}
        for rel, rec in sorted(files.items())
    ]
    try:
        payload = _canonical_json(manifest).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SkillpackSnapshotError(f"快照内容不可 JSON 序列化: {exc}") from exc
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def take_snapshot(pack_dir: dict[str, str], taken_at: Any) -> dict[str, Any]:
    """升级确认动作前强制调用：出一张升级前快照并写入单槽（fail-close）。

    pack_dir 为 `{相对路径: 文件内容}` 的包目录（folder-is-truth 的内存形态）；
    返回 `{schema, taken_at, files, fingerprint}`——files 存深拷贝的
    `{rel: {content, sha256, bytes}}`，fingerprint 为目录清单指纹。
    单槽语义：新快照顶替旧快照，restore() 只回最近一张（T1 §3.3 规则 1）。
    """
    if not isinstance(pack_dir, dict):
        raise SkillpackSnapshotError("pack_dir 必须为 {相对路径: 文件内容} 的 dict")
    at = _normalize_taken_at(taken_at)

    files: dict[str, dict[str, Any]] = {}
    for rel, content in pack_dir.items():
        if not isinstance(rel, str) or not rel.strip():
            raise SkillpackSnapshotError("相对路径必须为非空字符串")
        files[rel] = _file_record(content)

    snapshot: dict[str, Any] = {
        "schema": SNAPSHOT_SCHEMA,
        "taken_at": at,
        "files": files,
        "fingerprint": dir_fingerprint(files),
    }

    global _SLOT
    _SLOT = copy.deepcopy(snapshot)
    return snapshot


def restore(snapshot: dict[str, Any] | None = None) -> dict[str, str]:
    """按快照还原旧包：指纹校验通过后返回 `{rel: content}`（与 pack_dir 同形，
    调用方写回技能文件夹即目录级还原）。

    snapshot 为 None 时还原单槽当前快照（只回上一版）；显式传入快照时校验
    该快照自身指纹（审计追溯通道）。指纹不符即 FingerprintMismatch，
    绝不静默半还原（T1 §3.3 规则 2）。还原不顶替单槽——回滚可再回滚（规则 5）。
    """
    snap = _SLOT if snapshot is None else snapshot
    if snap is None:
        raise SkillpackSnapshotError("无可用快照：单槽为空，先 take_snapshot")
    if not isinstance(snap, dict) or snap.get("schema") != SNAPSHOT_SCHEMA:
        raise SkillpackSnapshotError(f"快照 schema 必须为 {SNAPSHOT_SCHEMA}")
    files = snap.get("files")
    if not isinstance(files, dict):
        raise FingerprintMismatch("快照 files 结构缺损，拒绝还原")

    recomputed = dir_fingerprint(files)
    if recomputed != snap.get("fingerprint"):
        raise FingerprintMismatch(
            f"指纹校验失败：重算 {recomputed} != 记录 {snap.get('fingerprint')}，拒绝还原"
        )
    # 逐文件内容校验：content 重算 sha256/bytes 必须与清单记录一致——
    # 清单指纹一致但内容被篡改（记录未同步）同样拒绝还原，绝不静默半还原。
    for rel, record in files.items():
        try:
            recomputed_record = _file_record(record.get("content"))
        except SkillpackSnapshotError as exc:
            raise FingerprintMismatch(f"文件 {rel} 内容非法: {exc}") from exc
        if (recomputed_record["sha256"] != record.get("sha256")
                or recomputed_record["bytes"] != record.get("bytes")):
            raise FingerprintMismatch(f"文件 {rel} 内容与清单记录不符，拒绝还原")

    return {rel: rec["content"] for rel, rec in sorted(files.items())}


def spot_check(
    snapshot: dict[str, Any],
    sample_paths: list[str] | None = None,
    max_n: int = SPOT_CHECK_DEFAULT_N,
) -> dict[str, Any]:
    """升级后抽样校验（T1 §3.4 抽样策略的最小形态）。

    样本路径 ≤5 个全查；>5 个且未显式给 sample_paths 时按字典序取前 max_n
    （确定性抽样，不引入随机性）。逐文件重算 sha256/bytes 与快照记录比对：
    样本路径缺失或内容与记录不符计入 failed。返回
    `{checked, passed, failed, failed_paths, sample_paths}`。
    抽查失败只计入结果不抛异常——是否回滚由调用方按 T1 §3.3 规则 4 决定
    （v1 不自动回滚）。
    """
    if not isinstance(snapshot, dict) or snapshot.get("schema") != SNAPSHOT_SCHEMA:
        raise SkillpackSnapshotError(f"快照 schema 必须为 {SNAPSHOT_SCHEMA}")
    files = snapshot.get("files")
    if not isinstance(files, dict):
        raise FingerprintMismatch("快照 files 结构缺损，无法抽查")
    if not isinstance(max_n, int) or max_n < 1:
        raise SkillpackSnapshotError("max_n 必须为 >=1 的整数")

    all_paths = sorted(files)
    if sample_paths is not None:
        samples = list(sample_paths)
    elif len(all_paths) <= SPOT_CHECK_ALL_MAX:
        samples = all_paths  # ≤5 全查
    else:
        samples = all_paths[:max_n]  # >5 字典序抽 max_n

    failed_paths: list[str] = []
    for path in samples:
        record = files.get(path)
        if not isinstance(record, dict):
            failed_paths.append(path)  # 样本路径不在快照内（缺失）
            continue
        try:
            record_now = _file_record(record.get("content"))
        except SkillpackSnapshotError:
            failed_paths.append(path)
            continue
        if record_now["sha256"] != record.get("sha256") or record_now["bytes"] != record.get("bytes"):
            failed_paths.append(path)  # 内容与记录不符（损坏/被覆盖）

    passed = len(samples) - len(failed_paths)
    return {
        "checked": len(samples),
        "passed": passed,
        "failed": len(failed_paths),
        "failed_paths": failed_paths,
        "sample_paths": list(samples),
    }


def current_snapshot() -> dict[str, Any] | None:
    """单槽当前快照的深拷贝；空槽返回 None。"""
    return copy.deepcopy(_SLOT) if _SLOT is not None else None


def clear_slot() -> None:
    """清空单槽（测试/运维辅助；生产回滚路径不经过此函数）。"""
    global _SLOT
    _SLOT = None


def audit_append(events: list[dict[str, Any]], event: dict[str, Any]) -> dict[str, Any]:
    """追加一条升级/回滚/抽查审计事件（append-only 存档流）。

    事件字段：`event`（事件 id，缺省自动生成 `spe-<uuid>`）、`change_type`
    （须在 CHANGE_TYPES 内：upgraded / rolled_back / spot_checked）、`at`
    （时间戳）、`actor`（角色）、`summary`（一句话摘要，中文）。
    同 event id 重复追加即拒绝（append-only：错记冲正不删行，但同 id 不可重放）。
    成功返回被追加的事件（events 原对象上追加）。
    """
    if not isinstance(events, list):
        raise AuditEventError("events 必须为 append-only 列表")
    if not isinstance(event, dict):
        raise AuditEventError("event 必须为 dict")

    record = dict(event)
    event_id = str(record.get("event") or "").strip()
    if not event_id:
        event_id = _EVENT_ID_PREFIX + uuid.uuid4().hex[:12]
    record["event"] = event_id

    change_type = record.get("change_type")
    if change_type not in CHANGE_TYPES:
        raise AuditEventError(f"未知 change_type: {change_type!r}（合法值 {list(CHANGE_TYPES)}）")
    try:
        record["at"] = _normalize_taken_at(record.get("at"))
    except SkillpackSnapshotError as exc:
        raise AuditEventError(f"at 缺失或非法: {exc}") from exc
    actor = record.get("actor")
    if actor not in ACTOR_ROLES:
        raise AuditEventError(f"actor 须为角色 {list(ACTOR_ROLES)}，不记个人身份: {actor!r}")
    summary = record.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise AuditEventError("summary 必填（一句话摘要）")

    if any(existing.get("event") == event_id for existing in events):
        raise AuditEventError(f"event id 重复: {event_id}（append-only，同 id 不可重放）")

    events.append(record)
    return record


def export_audit(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """导出审计事件流：append-only 顺序不变的深拷贝，可 json.dumps（机读）。"""
    if not isinstance(events, list):
        raise AuditEventError("events 必须为列表")
    exported = copy.deepcopy(events)
    try:
        json.dumps(exported, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise AuditEventError(f"审计事件流不可序列化: {exc}") from exc
    return exported
