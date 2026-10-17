#!/usr/bin/env python3
"""上游变更汉化 diff 报告渲染器（PRD-029/T3）。

输入：T2 检测脚本（scripts/upstream-detect.py）输出的 JSON（stdin 或 --input）。
输出：markdown 格式的汉化 diff 报告（stdout 或 --output），四节固定格式
      （4.1 变更摘要矩阵 / 4.2 工作量估算 / 4.3 优先级建议 / 4.4 两层对照）。

工作量估算口径：
- 优先：compare API file 记录的 additions 字段（新增行数≈新增字符串数）。
- 回退：T2 JSON 的 files[] 无 additions 字段时，按敏感文件数估算
  （每文件按 50 字符串计），报告中明确标注口径。
- 系数：每 50 字符串 ≈ 0.5 人日（T1 粗估，T5 试运行后校准）。

纯标准库，无第三方依赖。

    python3 scripts/upstream-report.py --input detect.json --output report.md
    python3 scripts/upstream-detect.py --state docs/upstream/sync-state.json \\
        | python3 scripts/upstream-report.py
"""
import argparse
import json
import sys

ORDER = ["added", "modified", "removed"]
CN = {"added": "新增", "modified": "修改", "removed": "删除"}
L1_NAME = "andrewyng/openworker"
L2_NAME = "Lenovo202409/openworker-zh"
P0_PREFIX = "surfaces/gui/src/"
DOCS_PREFIX = "docs/"
PLANS_PREFIX = "docs/plans/"


def load_input(args):
    if args.input:
        with open(args.input, encoding="utf-8") as f:
            return json.load(f)
    return json.load(sys.stdin)


def is_p0(f):
    return f.get("change") in ("modified", "removed") \
        and f.get("path", "").startswith(P0_PREFIX)


def render_matrix(files):
    m = {}
    for f in files:
        key = (f.get("change"), bool(f.get("sensitive")))
        m[key] = m.get(key, 0) + 1
    lines = ["| 变更类型＼影响面 | 影响已汉化文件 | 未影响已汉化文件 |",
             "|---|---|---|"]
    for ch in ORDER:
        lines.append("| %s | %d | %d |"
                     % (CN[ch], m.get((ch, True), 0), m.get((ch, False), 0)))
    return "\n".join(lines)


def workload(files):
    sens = [f for f in files if f.get("sensitive")]
    if any("additions" in f for f in files):
        new_lines = sum(f.get("additions", 0) for f in sens)
        basis = "compare API 的 additions 字段（新增行数≈新增字符串数）"
    else:
        new_lines = len(sens) * 50
        basis = "回退口径：T2 JSON 无 additions 字段，按敏感文件数×50 字符串/文件估算"
    retranslate = sum(1 for f in sens if f.get("change") == "modified")
    person_days = round(new_lines / 50 * 0.5, 1)
    return new_lines, retranslate, person_days, basis


def priorities(files):
    paths = lambda pred: sorted({f["path"] for f in files if pred(f)})
    p0 = paths(is_p0)
    p1 = paths(lambda f: f.get("sensitive") and f.get("change") == "added"
               and not f["path"].startswith(DOCS_PREFIX))
    p2 = paths(lambda f: f["path"].startswith(DOCS_PREFIX)
               and not f["path"].startswith(PLANS_PREFIX))
    return p0, p1, p2


def fmt_list(items, max_n):
    if not items:
        return "（无）"
    shown = items[:max_n]
    tail = "" if len(items) <= max_n else "\n- 等 %d 个，详见检测 JSON" % (len(items) - max_n)
    return "\n".join("- `%s`" % p for p in shown) + tail


def main():
    ap = argparse.ArgumentParser(description="汉化 diff 报告渲染器（PRD-029/T3）")
    ap.add_argument("--input", help="T2 检测 JSON 文件（缺省读 stdin）")
    ap.add_argument("--output", help="输出 markdown 文件（缺省写 stdout）")
    ap.add_argument("--max-files", type=int, default=30,
                    help="每类优先级最多列出的文件数（缺省 30）")
    args = ap.parse_args()
    data = load_input(args)

    files = data.get("files", [])
    l1 = data.get("l1", {})
    l2 = data.get("l2", {})
    degraded = bool(l2.get("degraded"))
    warnings = list(data.get("warnings", []))
    if data.get("truncated"):
        warnings.append("compare API 返回截断（>300 文件），数字为下限，需人工分段比对")

    # ---- 数据窗口 ----
    rels = l1.get("releases", [])
    if not rels:
        window = "本轮无新增 release"
    elif len(rels) == 1:
        window = "新增 %s（%s），共 1 个 release" % (
            rels[0]["tag"], (rels[0].get("published_at") or "")[:10])
    else:
        window = "%s（%s）→ %s（%s），共 %d 个 release" % (
            rels[0]["tag"], (rels[0].get("published_at") or "")[:10],
            rels[-1]["tag"], (rels[-1].get("published_at") or "")[:10],
            len(rels))
    l2_line = ("已降级（最后推送 %s，距今 %s 天），本轮只看 L1"
               % (l2.get("pushed_at"), l2.get("stale_days"))) if degraded \
        else "正常（最后推送 %s）" % l2.get("pushed_at")

    new_lines, retranslate, person_days, basis = workload(files)
    p0, p1, p2 = priorities(files)

    out = []
    out.append("# 上游同步汉化 diff 报告")
    out.append("")
    out.append("> 数据窗口：L1 `%s` %s；生成时间 %s。"
               % (L1_NAME, window, data.get("generated_at", "")))
    out.append("> L2 `%s`：%s。" % (L2_NAME, l2_line))
    out.append("")
    out.append("## 4.1 变更摘要矩阵")
    out.append("")
    out.append("### L1（`%s`）" % L1_NAME)
    out.append("")
    out.append(render_matrix([f for f in files if f.get("layer", "L1") == "L1"]))
    out.append("")
    out.append("### L2（`%s`）" % L2_NAME)
    out.append("")
    if degraded:
        out.append("本轮已降级，只看 L1（L2 连续 %s 天无更新，按 T1 策略降级）。"
                   % l2.get("stale_days"))
    else:
        out.append(render_matrix([f for f in files if f.get("layer") == "L2"]))
    out.append("")
    out.append("## 4.2 工作量估算")
    out.append("")
    out.append("- 新增字符串数：约 %d（口径：%s）" % (new_lines, basis))
    out.append("- 需重翻段落数：%d（敏感区 modified 文件数）" % retranslate)
    out.append("- 粗估工作量：%s 人日（每 50 字符串 ≈ 0.5 人日；T5 试运行后校准系数）"
               % person_days)
    out.append("")
    out.append("## 4.3 优先级建议")
    out.append("")
    out.append("### P0：用户看得见的 UI 字符串被改/被删（%d 个，当天开 issue）"
               % len(p0))
    out.append(fmt_list(p0, args.max_files))
    out.append("")
    out.append("### P1：新增功能的 UI 字符串（%d 个，功能可用但显示英文）" % len(p1))
    out.append(fmt_list(p1, args.max_files))
    out.append("")
    out.append("### P2：文档类变更（%d 个）" % len(p2))
    out.append(fmt_list(p2, args.max_files))
    out.append("")
    out.append("## 4.4 两层对照")
    out.append("")
    out.append("### L1 releases")
    out.append("")
    if rels:
        out.append("| tag | 发布日期 | breaking change |")
        out.append("|---|---|---|")
        for r in rels:
            out.append("| %s | %s | %s |" % (
                r["tag"], (r.get("published_at") or "")[:10],
                "是" if r.get("breaking") else "否"))
    else:
        out.append("本轮无新增 release。")
    out.append("")
    out.append("### L2")
    out.append("")
    out.append("- 最后推送：%s；距今 %s 天；状态：%s"
               % (l2.get("pushed_at"), l2.get("stale_days"),
                  "已降级（只看 L1）" if degraded else "正常"))
    out.append("")
    out.append("**一句话结论**：%s" % data.get("verdict", "（无）"))
    if warnings:
        out.append("")
        out.append("---")
        out.append("**告警/备注**：")
        for w in warnings:
            out.append("- %s" % w)
    out.append("")
    text = "\n".join(out)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
