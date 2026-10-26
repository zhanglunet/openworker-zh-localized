#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRD-183/T3：中文职业角色包发行门（trend #917，纯标准库）

判据（T1 §6，docs/plans/2026-10-25-zh-role-skill-pack.md）：
  1. scripts/quality-gate.py 自测通过（--self-test 同口径，证明门本身没坏）；
  2. role-packs/**/*.md 全量术语一致性检查（基表 TERMS + role-packs/terms.txt 合并）零失败。
任一不满足 → 退出码 1：**未过不可发行**。

合并语义（T1 §5.3）：terms.txt 只追加、不覆盖——
  - 词条键与基表 TERMS 重复且译法不同 → 直接失败（语境分叉走备注区，不改基表）；
  - 重复且译法相同 → 警告（冗余，不阻断）；
  - terms.txt 内部同键出现两次 → 失败（数据错误）。

豁免留痕区（PRD-183 风险「误杀可豁免但留痕」，T1 §5.3）：terms.txt 注释行，格式
    # exempt: <相对路径（仓库根）> :: <英文术语> :: <理由> :: YYYY-MM-DD
命中（该路径 × 该术语）的失败逐条放行，并在 stdout 打印放行明细留痕；豁免条目必须
同时写进当次 PR 描述（文件内 + PR 双重留痕）。豁免行残缺、日期非法、术语不在合并
表内 → 一律失败（fail-closed）。

CI 接线说明：role-packs/** 的常态把关由 tests/test_release_gate_role_packs.py 随
ci.yml 的 pytest 执行（失败阻断合并）；workflows/quality-gate.yml 触发路径扩到
role-packs/** 为后续一行接入（避开在途 workflow 改动，见 PRD-183/T3 PR 描述）。

CLI:
  --role-packs DIR     角色包根目录（默认 <仓库根>/role-packs）
  --quality-gate PATH  quality-gate.py 路径（默认 <仓库根>/scripts/quality-gate.py）
退出码：0 全过可发行；1 有失败（未过不可发行）；2 用法/环境错误。
"""

import argparse
import contextlib
import importlib.util
import os
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_ROLE_PACKS = REPO / "role-packs"
DEFAULT_QUALITY_GATE = REPO / "scripts" / "quality-gate.py"

EXEMPT_KEYWORD = "exempt:"


def load_quality_gate(path):
    """quality-gate.py 文件名带连字符不能直接 import，按路径加载（同 CI workflow 做法）。"""
    spec = importlib.util.spec_from_file_location("quality_gate", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rel_key(path, root=REPO):
    """文件在失败明细与豁免行里的路径口径：相对仓库根的 posix 路径；
    不在仓库根下时（如测试临时目录）退化为绝对 posix 路径，口径仍稳定。"""
    p, r = Path(path).resolve(), Path(root).resolve()
    try:
        return p.relative_to(r).as_posix()
    except ValueError:
        return p.as_posix()


# ---------------------------------------------------------------------------
# terms.txt 解析：词条 + 豁免留痕区（fail-closed）
# ---------------------------------------------------------------------------
def parse_terms_file(text):
    """返回 (entries, exempt, errors)。
    entries: [(行号, 英文键, 中文)]；exempt: [{"path","term","reason","date","line"}]。"""
    entries, exempt, errors = [], [], []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            body = line.lstrip("#").strip()
            if body.startswith(EXEMPT_KEYWORD):
                parts = [p.strip() for p in body[len(EXEMPT_KEYWORD):].split("::")]
                if len(parts) != 4 or not all(parts):
                    errors.append(
                        "terms.txt:%d 豁免行残缺（须为 # exempt: 路径 :: 术语 :: 理由 :: YYYY-MM-DD）"
                        % lineno)
                    continue
                path_s, term, reason, date_s = parts
                try:
                    date.fromisoformat(date_s)
                except ValueError:
                    errors.append("terms.txt:%d 豁免行日期非法：%r" % (lineno, date_s))
                    continue
                exempt.append({"path": path_s, "term": term, "reason": reason,
                               "date": date_s, "line": lineno})
            continue
        if "=" not in line:
            errors.append("terms.txt:%d 非注释行缺 `=`：%r" % (lineno, line))
            continue
        en, zh = (p.strip() for p in line.split("=", 1))
        if not en or not zh:
            errors.append("terms.txt:%d 词条残缺（英文=中文）：%r" % (lineno, line))
            continue
        entries.append((lineno, en, zh))
    seen = {}
    for lineno, en, _zh in entries:
        if en in seen:
            errors.append("terms.txt:%d 词条 %r 与第 %d 行重复" % (lineno, en, seen[en]))
        seen[en] = lineno
    return entries, exempt, errors


def _same_term(pattern, name):
    """键名是否落在基表术语口径内（含复数容差）：判定「与基表重复」。"""
    return bool(re.fullmatch(pattern + "s?", name, re.IGNORECASE))


def merge_terms(base_terms, entries):
    """基表 + terms.txt 词条合并（只追加、不覆盖）。
    返回 (merged, errors, warnings)。"""
    merged = [dict(t) for t in base_terms]
    errors, warnings = [], []
    for lineno, en, zh in entries:
        dup = next((t for t in base_terms
                    if t["en"] == re.escape(en) or _same_term(t["en"], en)), None)
        if dup is not None:
            if dup["zh"] != zh:
                errors.append(
                    "terms.txt:%d 词条 %r 与基表重复且译法不同（基表=%r，本表=%r）——"
                    "只追加、不覆盖，语境分叉走备注区（T1 §5.3）"
                    % (lineno, en, dup["zh"], zh))
            else:
                warnings.append(
                    "terms.txt:%d 词条 %r 与基表译法相同，属冗余（不阻断）" % (lineno, en))
            continue
        merged.append({"en": re.escape(en), "zh": zh, "wrongs": []})
    return merged, errors, warnings


def resolve_term(terms, name):
    """豁免行里的英文术语 → 术语记录（按基表正则含复数容差，或中文译法精确匹配）。"""
    for t in terms:
        if _same_term(t["en"], name) or t["zh"] == name:
            return t
    return None


# ---------------------------------------------------------------------------
# 豁免放行
# ---------------------------------------------------------------------------
def apply_exemptions(failures, resolved):
    """resolved: [(豁免条目, 术语记录)]。返回 (保留的失败, 放行的 (失败, 依据) 列表)。"""
    kept, released = [], []
    for f in failures:
        hit = next(((e, t) for e, t in resolved
                    if f["file"] == e["path"] and f.get("expected") == t["zh"]), None)
        if hit is None:
            kept.append(f)
        else:
            released.append((f, hit))
    return kept, released


# ---------------------------------------------------------------------------
# 扫描与判据
# ---------------------------------------------------------------------------
def collect_pack_files(role_packs):
    """role-packs/**/*.md 全量（T1 §6 判据口径：不筛变更文件）。返回 {仓库根相对路径: 全文}。"""
    files = {}
    for path in sorted(Path(role_packs).rglob("*.md")):
        try:
            with open(path, encoding="utf-8") as f:
                files[rel_key(path)] = f.read()
        except (OSError, UnicodeDecodeError):
            continue
    return files


def run_gate(role_packs=DEFAULT_ROLE_PACKS, quality_gate=DEFAULT_QUALITY_GATE,
             out=sys.stdout):
    """执行发行门，返回退出码（0 可发行 / 1 未过不可发行 / 2 环境错误）。"""
    role_packs, quality_gate = Path(role_packs), Path(quality_gate)
    if not role_packs.is_dir():
        print("环境错误：角色包目录不存在：%s" % role_packs, file=sys.stderr)
        return 2
    if not quality_gate.is_file():
        print("环境错误：quality-gate.py 不存在：%s" % quality_gate, file=sys.stderr)
        return 2

    def say(*a):
        print(*a, file=out)

    qg = load_quality_gate(quality_gate)
    errors = []

    # 判据 1：门自测（逐例输出随发行门报告走同一个 out，报告自成一体）
    say("== 判据 1/2：quality-gate 自测 ==")
    with contextlib.redirect_stdout(out):
        self_test_failed = qg.run_self_test()
    if self_test_failed:
        errors.append("quality-gate 自测未过：%s" % ", ".join(self_test_failed))

    # terms.txt 解析 + 合并语义
    terms_path = role_packs / "terms.txt"
    if not terms_path.is_file():
        print("环境错误：terms.txt 不存在：%s" % terms_path, file=sys.stderr)
        return 2
    entries, exempt, parse_errors = parse_terms_file(
        terms_path.read_text(encoding="utf-8"))
    errors += parse_errors
    merged, merge_errors, warnings = merge_terms(qg.TERMS, entries)
    errors += merge_errors

    # 豁免条目必须能落到合并表内的术语（fail-closed）
    resolved = []
    for e in exempt:
        t = resolve_term(merged, e["term"])
        if t is None:
            errors.append("terms.txt:%d 豁免术语 %r 不在基表+追加表内，拒绝放行"
                          % (e["line"], e["term"]))
        else:
            resolved.append((e, t))

    # 判据 2：全量术语一致性
    say("")
    say("== 判据 2/2：role-packs/**/*.md 全量术语一致性（基表 %d 条 + terms.txt 追加 %d 条）=="
        % (len(qg.TERMS), len(entries)))
    files = collect_pack_files(role_packs)
    say("扫描文件 %d 个" % len(files))
    failures = qg.check_terms(files, merged)
    kept, released = apply_exemptions(failures, resolved)

    for f in kept:
        say("失败：[%s] %s:%s（期望：%s）%s"
            % (f["check"], f["file"], f.get("line"), f["expected"], f["detail"]))
    for f, (e, _t) in released:
        say("放行（豁免留痕）：%s:%s 期望 %r —— 依据 terms.txt:%d（# exempt: %s :: %s :: %s :: %s）"
            % (f["file"], f.get("line"), f.get("expected"), e["line"],
               e["path"], e["term"], e["reason"], e["date"]))
    for w in warnings:
        say("警告：%s" % w)
    for err in errors:
        say("错误：%s" % err)

    say("")
    say("发行门：自测%s；术语失败 %d（放行 %d）；错误 %d；警告 %d"
        % ("通过" if not self_test_failed else "未过",
           len(kept), len(released), len(errors), len(warnings)))
    if errors or kept or self_test_failed:
        say("结论：未过不可发行（PRD-183：未过质量门不可发行）")
        return 1
    say("结论：可发行")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="PRD-183/T3 中文职业角色包发行门（纯标准库）")
    ap.add_argument("--role-packs", default=str(DEFAULT_ROLE_PACKS),
                    help="角色包根目录（默认 <仓库根>/role-packs）")
    ap.add_argument("--quality-gate", default=str(DEFAULT_QUALITY_GATE),
                    help="quality-gate.py 路径")
    args = ap.parse_args(argv)
    return run_gate(args.role_packs, args.quality_gate)


if __name__ == "__main__":
    sys.exit(main())
