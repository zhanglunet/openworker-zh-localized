# -*- coding: utf-8 -*-
"""PRD-452/T2（trend issue #2156 的 T2 环节）：翻译监督台最小实现。

按 T1 设计（docs/plans/2026-11-15-prd-452-translation-supervision-bench-design.md）
§3/§4 落地三件套与关口：
  - 进度：按原文段的译稿状态机 出稿中 → 待人审 → 已点头/已发回/已关闭；
    每次发回回来版本号 +1，版本并列可查，旧批注带到新版对照；
  - 批注：锚定（原文段/译文行/术语词条）+ 类型（换术语/重译/疑问/通过）+
    状态（待处理/已采纳/已驳回）；agent 改完回来旧批注逐条标记 已处理/未处理，
    未处理的继续挂在新版本上（R3 版本链不丢批注）；
  - 发回反馈：多条批注打包成一条反馈（发回指令：换术语/重译整段/只改指定处），
    agent 回来后新版本号挂在反馈上闭环；
  - 关口（写死）：未点头的译稿不进人工拍板收件箱（R1）；点头动作本身是
    一条落账记录（谁/何时/哪段/哪版本）；
  - TranslationSupervisionLedger：三件套 JSONL append-only（路径注入）。
零 LLM 零网络零子进程；示例全虚构占位。
测试：tests/test_prd452_t2_translation_supervision_bench.py
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

BENCH_SCHEMA = "translation-supervision-bench/v1"
DRAFT_STATUS = ("出稿中", "待人审", "已点头", "已发回", "已关闭")
ANNOTATION_TYPES = ("换术语", "重译", "疑问", "通过")
ANNOTATION_STATUS = ("待处理", "已采纳", "已驳回")
SEND_BACK_ORDERS = ("换术语", "重译整段", "只改指定处")
ERROR_CODES = ("SUPERVISION_INCOMPLETE", "SUPERVISION_STATE_CONFLICT")


class SupervisionError(ValueError):
    """监督台违规——显形拒绝。"""


def _require(ok: bool, code: str, detail: str) -> None:
    if not ok:
        raise SupervisionError(f"{code}：{detail}")


def _actor_at(actor: Any, at: Any) -> tuple[str, str]:
    _require(bool(actor) and bool(at), "SUPERVISION_INCOMPLETE",
             "作者与时间缺一不可（留痕红线）")
    return str(actor), str(at)


class TranslationSupervisionBench:
    """一段原文的译稿监督（三件套用译稿版本号串联）。"""

    def __init__(self, *, source_seq: str, translator: str,
                 created_at: str, source_text: str) -> None:
        actor, ts = _actor_at(translator, created_at)
        _require(bool(source_text), "SUPERVISION_INCOMPLETE", "原文不能为空")
        self.source_seq = str(source_seq)
        self.source_text = str(source_text)
        self.translator = actor
        self.created_at = ts
        self.status = "出稿中"
        self.versions: list[dict[str, Any]] = []
        self.annotations: list[dict[str, Any]] = []
        self.feedbacks: list[dict[str, Any]] = []
        self.decisions: list[dict[str, Any]] = []

    # ---- 接入点 1/2：出稿开始与交稿（§4.1）------------------------------------
    def submit_draft(self, *, version: str, text: str,
                     term_choices: dict[str, str] | None = None) -> dict[str, Any]:
        _require(self.status == "出稿中", "SUPERVISION_STATE_CONFLICT",
                 f"当前 {self.status!r} 不可交稿")
        _require(bool(text), "SUPERVISION_INCOMPLETE", "译文不能为空")
        _require(all(v["version"] != version for v in self.versions),
                 "SUPERVISION_STATE_CONFLICT", f"版本 {version!r} 重复")
        v = {"version": version, "text": str(text),
             "term_choices": dict(term_choices or {})}
        self.versions.append(v)
        self.status = "待人审"
        return copy.deepcopy(v)

    # ---- 批注（锚定+类型）------------------------------------------------------
    def annotate(self, *, author: str, at: str, anchor: str, atype: str,
                 text: str, version: str) -> dict[str, Any]:
        actor, ts = _actor_at(author, at)
        _require(atype in ANNOTATION_TYPES, "SUPERVISION_STATE_CONFLICT",
                 f"批注类型 {atype!r} 词表外")
        _require(bool(text) and bool(anchor), "SUPERVISION_INCOMPLETE",
                 "批注文本/锚点缺一")
        _require(any(v["version"] == version for v in self.versions),
                 "SUPERVISION_STATE_CONFLICT", f"批注挂版本 {version!r} 不存在")
        a = {"seq": len(self.annotations) + 1, "author": actor, "at": ts,
             "anchor": str(anchor), "type": atype, "text": str(text),
             "version": str(version), "status": "待处理",
             "carried_to": None}
        self.annotations.append(a)
        return copy.deepcopy(a)

    def resolve_annotation(self, *, seq: int, status: str) -> dict[str, Any]:
        """批注处理：已采纳/已驳回（通过类批注处理后才可点头）。"""
        _require(status in ("已采纳", "已驳回"), "SUPERVISION_STATE_CONFLICT",
                 f"批注处理状态 {status!r} 词表外")
        a = next((x for x in self.annotations if x["seq"] == seq), None)
        _require(a is not None, "SUPERVISION_STATE_CONFLICT",
                 f"批注 {seq} 不存在")
        _require(a["status"] == "待处理", "SUPERVISION_STATE_CONFLICT",
                 f"批注 {seq} 已是 {a['status']!r}")
        a["status"] = status
        return copy.deepcopy(a)

    # ---- 一键发回：批注打包成反馈（§4.2）---------------------------------------
    def send_back(self, *, author: str, at: str, annotation_seqs: list[int],
                  order: str, note: str = "") -> dict[str, Any]:
        actor, ts = _actor_at(author, at)
        _require(order in SEND_BACK_ORDERS, "SUPERVISION_STATE_CONFLICT",
                 f"发回指令 {order!r} 词表外")
        _require(self.status == "待人审", "SUPERVISION_STATE_CONFLICT",
                 f"当前 {self.status!r} 不可发回")
        _require(bool(annotation_seqs), "SUPERVISION_INCOMPLETE",
                 "发回须至少带一条批注")
        linked = []
        for seq in annotation_seqs:
            a = next((x for x in self.annotations if x["seq"] == seq), None)
            _require(a is not None, "SUPERVISION_STATE_CONFLICT",
                     f"批注 {seq} 不存在")
            _require(a["status"] == "待处理", "SUPERVISION_STATE_CONFLICT",
                     f"批注 {seq} 已处理过")
            linked.append(seq)
        fb = {"seq": len(self.feedbacks) + 1, "author": actor, "at": ts,
              "annotations": list(linked), "order": order,
              "note": str(note), "returned_version": None, "status": "待处理"}
        self.feedbacks.append(fb)
        self.status = "已发回"
        return copy.deepcopy(fb)

    # ---- 接入点 3：改完回来（版本 +1，旧批注逐条对照，未处理继续挂新版）---------
    def return_draft(self, *, version: str, text: str,
                     handled_annotation_seqs: list[int],
                     term_choices: dict[str, str] | None = None) -> dict[str, Any]:
        _require(self.status == "已发回", "SUPERVISION_STATE_CONFLICT",
                 f"当前 {self.status!r} 无在途回炉")
        _require(all(v["version"] != version for v in self.versions),
                 "SUPERVISION_STATE_CONFLICT", f"版本 {version!r} 重复")
        open_fb = next((f for f in self.feedbacks if f["status"] == "待处理"),
                       None)
        _require(open_fb is not None, "SUPERVISION_STATE_CONFLICT",
                 "无待处理反馈单——回炉无依据")
        pending = [a for a in self.annotations
                   if a["status"] == "待处理"]
        _require(set(handled_annotation_seqs) <= {a["seq"] for a in pending},
                 "SUPERVISION_STATE_CONFLICT",
                 "已处理清单含不存在或非待处理的批注")
        for a in self.annotations:
            if a["seq"] in set(handled_annotation_seqs):
                a["status"] = "已处理"
                a["carried_to"] = None
            elif a["status"] == "待处理":
                a["carried_to"] = version      # 未处理的继续挂在新版本上
        v = {"version": version, "text": str(text),
             "term_choices": dict(term_choices or {})}
        self.versions.append(v)
        self.status = "待人审"
        open_fb["status"] = "已回炉"
        open_fb["returned_version"] = version
        return copy.deepcopy(v)

    # ---- 裁决：点头/关闭（点头动作本身是落账记录）-------------------------------
    def approve(self, *, approver: str, at: str, version: str) -> dict[str, Any]:
        actor, ts = _actor_at(approver, at)
        _require(self.status == "待人审", "SUPERVISION_STATE_CONFLICT",
                 f"当前 {self.status!r} 不可点头")
        latest = self.versions[-1]
        _require(latest["version"] == version, "SUPERVISION_STATE_CONFLICT",
                 f"只能点头最新版本 {latest['version']!r}，不是 {version!r}")
        unhandled = [a for a in self.annotations
                     if a["status"] == "待处理"]
        _require(not unhandled, "SUPERVISION_STATE_CONFLICT",
                 f"{len(unhandled)} 条批注未处理——先处理或发回再点头")
        self.status = "已点头"
        d = {"approver": actor, "at": ts, "source_seq": self.source_seq,
             "version": version, "verdict": "点头"}
        self.decisions.append(d)
        return copy.deepcopy(d)

    def close(self, *, approver: str, at: str) -> dict[str, Any]:
        actor, ts = _actor_at(approver, at)
        _require(self.status in ("已点头", "已发回"),
                 "SUPERVISION_STATE_CONFLICT",
                 f"当前 {self.status!r} 不可关闭")
        self.status = "已关闭"
        return {"closed_at": ts, "by": actor}

    # ---- 出口：人工拍板收件箱（R1 关口）----------------------------------------
    def outlet(self) -> dict[str, Any]:
        if self.status == "已点头":
            return {"schema": BENCH_SCHEMA, "passed": [{
                "source_seq": self.source_seq,
                "version": self.versions[-1]["version"],
                "text": self.versions[-1]["text"]}],
                "blocked": [], "blocked_count": 0}
        return {"schema": BENCH_SCHEMA, "passed": [],
                "blocked": [{"source_seq": self.source_seq,
                             "status": self.status}],
                "blocked_count": 1}


class TranslationSupervisionLedger:
    """三件套 JSONL append-only（进度/批注/反馈，路径注入）。"""

    _KINDS = ("progress", "annotation", "feedback", "decision")

    def __init__(self, path: str | Path | None = None) -> None:
        self._entries: list[dict[str, Any]] = []
        self._path = Path(path) if path else None

    def record(self, *, kind: str, source_seq: str, at: str,
               payload: dict[str, Any]) -> dict[str, Any]:
        _require(kind in self._KINDS, "SUPERVISION_INCOMPLETE",
                 f"kind {kind!r} 词表外")
        _require(bool(source_seq) and bool(at), "SUPERVISION_INCOMPLETE",
                 "段号/时间缺一")
        entry = {"schema": BENCH_SCHEMA, "kind": kind,
                 "source_seq": str(source_seq), "at": str(at),
                 "payload": copy.deepcopy(payload)}
        self._entries.append(entry)
        if self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False,
                                    sort_keys=True) + "\n")
        return dict(entry)

    def entries(self) -> list[dict[str, Any]]:
        return [dict(e) for e in self._entries]
