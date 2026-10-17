#!/usr/bin/env python3
"""上游变更检测（PRD-029/T2 草稿）。

对比 L1（andrewyng/openworker）releases 与 L2（Lenovo202409/openworker-zh）
commits，输出汉化 diff 的 JSON（T3 报告模板的输入）。

    export GITHUB_TOKEN=...   # 需要 repo 读取权限
    python3 scripts/upstream-detect.py --state docs/upstream/sync-state.json
    python3 scripts/upstream-detect.py --state docs/upstream/sync-state.json --update-state

默认干跑：只输出 JSON，不写回基线（书签）。确认有效后再加 --update-state
把 last_synced_tag / last_synced_sha 往后挪。

纯标准库，无第三方依赖。
"""
import argparse
import datetime
import json
import os
import sys
import urllib.request
import urllib.error

L1_OWNER_REPO = "andrewyng/openworker"
L2_OWNER_REPO = "Lenovo202409/openworker-zh"
API = "https://api.github.com"

# 汉化敏感区（owzh 实际结构，2026-10-17 已核对；T1 稿的 locales//i18n/ 写法作废）
SENSITIVE_PREFIXES = ("surfaces/gui/src/", "docs/", "website/")
SENSITIVE_EXCLUDE = ("docs/plans/",)  # 本项目工作稿，不计汉化工作量
P0_PREFIXES = ("surfaces/gui/src/",)  # 用户看得见的 UI 字符串
L2_STALE_DAYS = 90  # T1 修订：L2 连续 3 个月无更新则降级只看 L1
MONITOR_REVIEW_DAYS = 90  # PRD 风险：监控清单每季度复核


def gh_get(path, token):
    req = urllib.request.Request(API + path, method="GET")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "owzh-upstream-detect")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        raise SystemExit(f"GitHub API {e.code} on {path}: {body}")


def is_sensitive(path):
    if path.startswith(SENSITIVE_EXCLUDE):
        return False
    return path.startswith(SENSITIVE_PREFIXES)


def is_p0(change, path):
    return change in ("modified", "removed") and path.startswith(P0_PREFIXES)


def classify(files, layer):
    out = []
    for f in files:
        status = f.get("status", "")
        change = {"added": "added", "modified": "modified",
                  "removed": "removed"}.get(status, "modified")  # renamed 等按 modified
        path = f["filename"]
        out.append({"path": path, "change": change,
                    "sensitive": is_sensitive(path), "layer": layer})
    return out


def l1_new_releases(since_tag, token):
    """返回 since_tag 之后的新 releases（按发布时间升序）。

    since_tag 为 None（首次运行）时返回空列表：基线必须按文档 §1.3
    人工设定，不能默认"从第一个 release 开始"，否则会产出全量噪音。
    """
    if since_tag is None:
        return [], True
    releases = gh_get(f"/repos/{L1_OWNER_REPO}/releases?per_page=100", token)
    if isinstance(releases, dict):  # 错误体
        raise SystemExit(f"releases API 异常: {releases.get('message')}")
    releases = [r for r in releases if not r.get("draft")]  # 草稿不参与 tag 推进，避免干扰基线判断
    new, found = [], since_tag is None
    ordered = sorted(releases, key=lambda r: r.get("published_at") or "")
    for r in ordered:
        if found:
            new.append(r)
        elif r.get("tag_name") == since_tag:
            found = True
    if since_tag and not found:
        # 基线 tag 已不在列表里（如被删除）：保守起见视为全部是新的太吵，
        # 这里返回空并告警，人工介入重建基线
        return [], False
    return new, True


def compare_files(owner_repo, base, head, token):
    d = gh_get(f"/repos/{owner_repo}/compare/{base}...{head}", token)
    files = d.get("files", [])
    return files, d.get("total_commits"), len(files) >= 300


def main():
    ap = argparse.ArgumentParser(description="上游变更检测（PRD-029/T2 草稿）")
    ap.add_argument("--state", required=True, help="基线状态文件 docs/upstream/sync-state.json")
    ap.add_argument("--update-state", action="store_true", help="把基线书签往后挪（默认干跑不写）")
    ap.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    args = ap.parse_args()

    with open(args.state, encoding="utf-8") as f:
        state = json.load(f)

    now = datetime.datetime.now(datetime.timezone.utc)
    result = {"generated_at": now.isoformat(timespec="seconds"),
              "truncated": False, "warnings": []}

    # ---- L1 ----
    l1 = {"releases": [], "files": []}
    new_releases, baseline_ok = l1_new_releases(state.get("last_synced_tag"), args.token)
    if not baseline_ok:
        result["warnings"].append("last_synced_tag 在 L1 releases 中找不到，需人工重建基线")
    if state.get("last_synced_tag") is None:
        result["warnings"].append("首次运行：请按文档 §1.3 先设定 last_synced_tag / last_synced_sha 再跑")
    prev = state.get("last_synced_tag")
    for r in new_releases:
        tag = r["tag_name"]
        l1["releases"].append({"tag": tag,
                               "published_at": (r.get("published_at") or "")[:10],
                               "breaking": "breaking change" in (r.get("body") or "").lower(),
                               "name": r.get("name") or ""})
        if prev:
            files, _, trunc = compare_files(L1_OWNER_REPO, prev, tag, args.token)
            l1["files"].extend(classify(files, "L1"))
            result["truncated"] = result["truncated"] or trunc
        prev = tag
    # 加密档判断（T1）：两周内新增 release >= 2，或出现 breaking change
    two_weeks_ago = now - datetime.timedelta(days=14)
    recent = [r for r in new_releases
              if (r.get("published_at") or "") >= two_weeks_ago.isoformat()[:10]]
    l1["escalate"] = len(recent) >= 2 or any(r["breaking"] for r in l1["releases"])
    l1["new_tag"] = prev
    result["l1"] = l1

    # ---- L2 ----
    repo = gh_get(f"/repos/{L2_OWNER_REPO}", args.token)
    pushed = repo.get("pushed_at") or ""
    stale_days = (now - datetime.datetime.fromisoformat(pushed.replace("Z", "+00:00"))).days \
        if pushed else 9999
    l2 = {"pushed_at": pushed[:10], "stale_days": stale_days, "degraded": False,
          "files": [], "new_sha": state.get("last_synced_sha")}
    if stale_days > L2_STALE_DAYS:
        l2["degraded"] = True
        result["warnings"].append(
            f"L2 已 {stale_days} 天无更新（>{L2_STALE_DAYS} 天），按 T1 修订降级为只看 L1")
    elif state.get("last_synced_sha") is None:
        # 首次运行未设基线：告警并跳过 L2 diff（与 L1 的 fail-quiet 对齐），不直接调 compare
        result["warnings"].append("last_synced_sha 未设定：请按文档 §1.3 先设定基线再跑，已跳过 L2 diff")
    else:
        files, _, trunc = compare_files(
            L2_OWNER_REPO, state.get("last_synced_sha"), "main", args.token)
        l2["files"] = classify(files, "L2")
        head = gh_get(f"/repos/{L2_OWNER_REPO}/commits/main", args.token)
        l2["new_sha"] = head["sha"]
        result["truncated"] = result["truncated"] or trunc
    result["l2"] = l2

    # ---- 汇总（喂给 T3 报告模板） ----
    all_files = l1["files"] + l2["files"]
    seen = {}
    for f in all_files:  # 同一文件多次变更取最后一次
        seen[(f["layer"], f["path"])] = f
    files = list(seen.values())
    summary = {"added": 0, "modified": 0, "removed": 0, "sensitive_hits": 0}
    p0_files = []
    for f in files:
        summary[f["change"]] += 1
        if f["sensitive"]:
            summary["sensitive_hits"] += 1
        if is_p0(f["change"], f["path"]):
            p0_files.append(f["path"])
    result["files"] = files
    result["summary"] = summary
    result["p0_files"] = sorted(set(p0_files))
    layers = "L1" + ("" if l2["degraded"] else "+L2")
    result["verdict"] = (
        f"本轮检测到 {len(files)} 个文件变更（{layers}），"
        f"其中 {summary['sensitive_hits']} 个命中汉化敏感区，"
        f"P0（用户可见 UI 字符串被改/被删）{len(set(p0_files))} 个。"
        + (" L2 已降级，只看 L1。" if l2["degraded"] else ""))

    # ---- 季度复核提醒 ----
    reviewed = state.get("monitor_list_reviewed_at", "")
    try:
        rd = datetime.datetime.fromisoformat(reviewed).date()
        due = (now.date() - rd).days > MONITOR_REVIEW_DAYS
    except ValueError:
        due = True
    result["monitor_review_due"] = due
    if due:
        result["warnings"].append("监控清单超过 90 天未复核（PRD 风险要求每季度复核）")

    # ---- 写回基线（显式确认才做） ----
    if args.update_state:
        state["last_synced_tag"] = l1["new_tag"] or state.get("last_synced_tag")
        state["last_synced_sha"] = l2["new_sha"]
        state["l2_degraded"] = l2["degraded"]
        state["last_run"] = result["generated_at"]
        with open(args.state, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            f.write("\n")
        result["state_updated"] = True
    else:
        result["state_updated"] = False

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
