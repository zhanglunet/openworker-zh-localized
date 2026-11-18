"""技能评估最小实现：质量门 + 重叠检测（PRD-488/T2）。

按 livead 的 T1 设计稿（docs/plans/2026-11-17-prd-488-owzh-skill-evaluation-design.md）实现 T2 范围：
质量门（设计稿 §一）+ 重叠检测（设计稿 §二），产出首份评估报告落账。
合成评测集与实测（设计稿 §三/§四）不在 T2 范围，留待后续任务。

方法说明（诚实口径）：
- 重叠检测的文本相似度用词元集合 Jaccard：ASCII 词 + 中文字符 bigram；
  它是设计稿“嵌入向量余弦”的最小可用代理——T2 不引入外部 embedding 服务，
  阈值仍按设计稿取 0.8（≥0.8 记“疑似重叠”，只进待核查清单，不自动合并，
  行为层确认留待人工复核）。
- 质量门只按评估清单（inventory.json）里的对照跑分判；尚无跑分时样本量为 0，
  按设计稿判“证据不足”，不判通过也不判失效，不编造跑分数据。
- 评估结论只进整改清单/待核查清单；技能下线另走审批，绝不直接删技能。

纯标准库，零网络依赖。可直接运行：
    python3 skill_evaluation.py --inventory skill-eval/inventory.json \\
        --report skill-eval/reports/2026-11-17-evaluation.md
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

VERDICT_PASS = "通过"
VERDICT_REMEDIATE = "整改"
VERDICT_INSUFFICIENT = "证据不足"

_CJK_RUN = re.compile(r"[\u4e00-\u9fff]+")
_WORD = re.compile(r"[a-z0-9]{2,}")


def tokenize(text: str) -> set[str]:
    """词元集合：ASCII 词（小写）+ 中文字符 bigram。"""
    tokens: set[str] = set()
    for word in _WORD.findall(text.lower()):
        tokens.add("w:" + word)
    for run in _CJK_RUN.findall(text):
        for i in range(len(run) - 1):
            tokens.add("c:" + run[i : i + 2])
    return tokens


def jaccard(left: set[str], right: set[str]) -> float:
    """Jaccard 相似度；两空集记 1.0，一空一非空记 0.0。"""
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def strip_frontmatter(text: str) -> str:
    """去 SKILL.md 的 YAML frontmatter，但保留 description 行正文。"""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    description = ""
    for line in text[3:end].splitlines():
        if line.strip().startswith("description:"):
            description = line.split(":", 1)[1].strip().strip("\"").strip("'")
            break
    return description + "\n" + text[end + 4 :]


def overlap_pairs(skills: list[dict], threshold: float) -> list[dict]:
    """全量两两比对。返回按相似度倒序的全部配对；similarity ≥ threshold 为疑似重叠。"""
    token_sets = {skill["id"]: tokenize(skill["text"]) for skill in skills}
    pairs: list[dict] = []
    ids = [skill["id"] for skill in skills]
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            sim = jaccard(token_sets[ids[i]], token_sets[ids[j]])
            pairs.append(
                {"a": ids[i], "b": ids[j], "similarity": round(sim, 3),
                 "suspected": sim >= threshold}
            )
    pairs.sort(key=lambda p: (-p["similarity"], p["a"], p["b"]))
    return pairs


def _error_rate(metrics: dict) -> tuple[float | None, float | None]:
    """483/484 的错误率字段名与 479/480 不同（error_rate / false_signal_rate），都认。"""
    error = metrics.get("error_rate", metrics.get("false_signal_rate"))
    control = metrics.get("control_error_rate", metrics.get("control_false_signal_rate"))
    return error, control


def gate_error_rate(metrics: dict, thresholds: dict) -> tuple[str, str]:
    """479/480 口径：错误率相对下降 ≥ 阈值且新增错误类型为 0；样本不足判证据不足。"""
    min_sample = thresholds["min_sample_tasks"]
    sample = metrics.get("sample_tasks")
    if sample is None or sample < min_sample:
        return VERDICT_INSUFFICIENT, f"样本量 {sample} < {min_sample}，不判通过"
    with_rate = metrics.get("error_rate_with_skill")
    without_rate = metrics.get("error_rate_without_skill")
    new_types = metrics.get("new_error_types")
    if with_rate is None or without_rate is None or new_types is None:
        return VERDICT_INSUFFICIENT, "缺少对照跑分（错误率/新增错误类型未记录）"
    if without_rate <= 0:
        return VERDICT_INSUFFICIENT, "对照组错误率为 0，无可比下降空间"
    drop = (without_rate - with_rate) / without_rate
    min_drop = thresholds["min_relative_error_drop"]
    max_new = thresholds["max_new_error_types"]
    if drop >= min_drop and new_types <= max_new:
        return VERDICT_PASS, f"错误率相对下降 {drop:.0%}（要求 ≥{min_drop:.0%}），新增错误类型 {new_types}"
    return VERDICT_REMEDIATE, (
        f"错误率相对下降 {drop:.0%}（要求 ≥{min_drop:.0%}），新增错误类型 {new_types}（要求 ≤{max_new}）"
    )


def gate_rate_trio(metrics: dict, thresholds: dict) -> tuple[str, str]:
    """483/484 口径：错误率/行为改变率/采纳率三项硬指标；任一不达标即未过关；样本不足判证据不足。"""
    min_sample = thresholds["min_sample_tasks"]
    sample = metrics.get("sample_tasks")
    if sample is None or sample < min_sample:
        return VERDICT_INSUFFICIENT, f"样本量 {sample} < {min_sample}，不判通过"
    error, control = _error_rate(metrics)
    behavior = metrics.get("behavior_change_rate")
    adoption = metrics.get("adoption_rate")
    if error is None or control is None or behavior is None or adoption is None:
        return VERDICT_INSUFFICIENT, "缺少对照跑分（错误率/行为改变率/采纳率未记录）"
    label = thresholds.get("error_label", "错误率")
    reasons: list[str] = []
    max_error = thresholds["max_error_rate"]
    if error > max_error:
        reasons.append(f"{label} {error:.0%} > 上限 {max_error:.0%}")
    if error > control * thresholds["max_error_vs_control_ratio"]:
        reasons.append(f"{label} {error:.0%} 高于对照组 {control:.0%} 的一半")
    min_behavior = thresholds["min_behavior_change_rate"]
    if behavior < min_behavior:
        reasons.append(f"行为改变率 {behavior:.0%} < {min_behavior:.0%}")
    min_adoption = thresholds["min_adoption_rate"]
    if adoption < min_adoption:
        reasons.append(f"采纳率 {adoption:.0%} < {min_adoption:.0%}")
    if reasons:
        return VERDICT_REMEDIATE, "；".join(reasons)
    return VERDICT_PASS, (
        f"{label} {error:.0%}、行为改变率 {behavior:.0%}、采纳率 {adoption:.0%} 均达标"
    )


_GATES = {"error-rate": gate_error_rate, "rate-trio": gate_rate_trio}


def evaluate(inventory: dict) -> dict:
    """对一份评估清单跑质量门 + 重叠检测，返回报告 dict（JSON 可序列化）。"""
    thresholds = inventory["thresholds"]
    gate = _GATES[inventory["gate"]]
    verdicts = []
    for skill in inventory["skills"]:
        verdict, reason = gate(skill["metrics"], thresholds)
        verdicts.append({"id": skill["id"], "verdict": verdict, "reason": reason})
    pairs = overlap_pairs(inventory["skills"], thresholds["overlap_similarity"])
    suspected = [p for p in pairs if p["suspected"]]
    return {
        "prd": inventory["prd"],
        "repo": inventory["repo"],
        "date": inventory["generated_at"],
        "design_ref": inventory["design_ref"],
        "inventory_version": inventory["version"],
        "thresholds": thresholds,
        "skill_count": len(inventory["skills"]),
        "pair_count": len(pairs),
        "verdicts": verdicts,
        "pairs": pairs,
        "suspected": suspected,
        "remediation_candidates": [v for v in verdicts if v["verdict"] == VERDICT_REMEDIATE],
    }


def render_report(report: dict) -> str:
    """报告 dict → 落账用的 Markdown（append-only：每次评估新起一份带日期的文件）。"""
    lines = [
        f"# 技能评估报告（首份，{report['date']}）",
        "",
        f"- PRD：PRD-{report['prd']}（{report['repo']}）",
        f"- 设计依据：{report['design_ref']}",
        f"- 评估清单版本：v{report['inventory_version']}，技能 {report['skill_count']} 个",
        f"- 阈值：`{json.dumps(report['thresholds'], ensure_ascii=False)}`（设计稿草稿阈值，待评审定稿、实测后复核）",
        "",
        "## 一、质量门",
        "",
        "| 技能 | 结论 | 原因 |",
        "|---|---|---|",
    ]
    for v in report["verdicts"]:
        lines.append(f"| {v['id']} | {v['verdict']} | {v['reason']} |")
    lines += [
        "",
        "## 二、重叠检测",
        "",
        f"全量两两比对 {report['pair_count']} 对；疑似重叠（相似度 ≥ 阈值）{len(report['suspected'])} 对。",
        "相似度为词元集合 Jaccard（设计稿嵌入余弦的最小可用代理，T2 不引入外部 embedding 服务）。",
        "",
        "| 技能 A | 技能 B | 相似度 | 疑似重叠 |",
        "|---|---|---|---|",
    ]
    for p in report["pairs"]:
        lines.append(
            f"| {p['a']} | {p['b']} | {p['similarity']:.3f} | {'是' if p['suspected'] else '否'} |"
        )
    lines += [
        "",
        "## 三、待核查清单（疑似重叠）",
        "",
    ]
    if report["suspected"]:
        for p in report["suspected"]:
            lines.append(
                f"- {p['a']} ↔ {p['b']}（相似度 {p['similarity']:.3f}）：只进待核查清单，"
                "不自动合并；行为层确认与合并/拆分/保留分工由人决定。"
            )
    else:
        lines.append("无。")
    lines += [
        "",
        "## 四、整改清单候选（质量门未过关）",
        "",
    ]
    if report["remediation_candidates"]:
        for v in report["remediation_candidates"]:
            lines.append(f"- {v['id']}：{v['reason']}")
    else:
        lines.append("无。质量门结论为“证据不足”的技能不在此列——证据不足不是失效，待对照跑分补测。")
    lines += [
        "",
        "## 五、方法与诚实声明",
        "",
        "- 本报告由评估脚本按评估清单自动生成；清单里的技能文本取自仓库 main 上的真实技能文件（路径见清单）。",
        "- 质量门样本量为 0 的技能判“证据不足”：T2 只跑门逻辑与重叠检测，真实对照跑分（A/B）在后续实测试运行；不编造跑分数据。",
        "- 评估结论只进整改清单/待核查清单；技能下线另走审批，绝不因评估未过关直接删技能。",
        "",
    ]
    return "\n".join(lines)


def load_inventory(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="技能评估最小实现：质量门 + 重叠检测")
    parser.add_argument("--inventory", required=True, help="评估清单 JSON 路径")
    parser.add_argument("--report", required=True, help="输出评估报告 Markdown 路径")
    args = parser.parse_args(argv)
    report = evaluate(load_inventory(args.inventory))
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_report(report), encoding="utf-8")
    summary = {
        "skill_count": report["skill_count"],
        "pair_count": report["pair_count"],
        "suspected": len(report["suspected"]),
        "verdicts": {v["verdict"]: sum(1 for x in report["verdicts"] if x["verdict"] == v["verdict"])
                     for v in report["verdicts"]},
        "report": str(out),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
