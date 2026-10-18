#!/usr/bin/env python3
"""上游 diff 哨兵（PRD-068/T2）。

commit 级轻量监控：拉取 L1（andrewyng/openworker）/ L2（Lenovo202409/openworker-zh）
默认分支的新增 commit，按汉化敏感区做影响面分析，输出 JSON（T3 周报模板的输入）。

    export GITHUB_TOKEN=...   # 读公仓 commit 足够
    python3 scripts/upstream-weekly.py --state docs/upstream/watch-state.json
    python3 scripts/upstream-weekly.py --state docs/upstream/watch-state.json --update-state

默认干跑：只输出 JSON，不写回水位。确认有效后再加 --update-state。

打个比方：PRD-029 是"每月大扫除"，这个脚本是门口的"门铃"——
有动静就响一声告诉你要不要看，真正动手跟进翻译仍走 029 的流程。

敏感区口径走 scripts/upstream_common.py（唯一源头），不自立口径。
纯标准库，无第三方依赖。
"""
import argparse
import datetime
import json
import os
import sys
import time
import urllib.request
import urllib.error

from upstream_common import is_sensitive

L1_OWNER_REPO = "andrewyng/openworker"
L2_OWNER_REPO = "Lenovo202409/openworker-zh"
API = "https://api.github.com"

# 影响面四类（T2 口径）
CAT_NEW = "新增文件"            # added 且命中敏感区 → 需跟进翻译
CAT_MOD_TRANSLATED = "修改已汉化文件"  # modified/renamed/removed 且命中敏感区 → 需跟进
CAT_MOD_UNTRANSLATED = "修改未汉化文件"  # modified/renamed 且未命中敏感区
CAT_NON_SENSITIVE = "非敏感区变更"    # 其余（新增的非敏感文件、不敏感的删除等）


class NotFound(Exception):
    """404：资源不在上游历史里（水位 SHA 失效时用，见 detect_new_commits）"""


def _fetch(path, token):
    req = urllib.request.Request(API + path, method="GET")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "owzh-upstream-weekly")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def gh_get(path, token):
    """GET 并解析 JSON。5xx/429/网络错误按 1s→4s→16s 退避重试 3 次（T1 §2.3）；
    仍失败则非零退出（水位不写回，下次窗口自动拉长补上）；404 抛 NotFound。"""
    last = None
    for wait in (0, 1, 4, 16):
        if wait:
            time.sleep(wait)
        try:
            return _fetch(path, token)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise NotFound(path)
            if e.code == 429 or 500 <= e.code < 600:
                last = f"HTTP {e.code}"
                continue
            raise SystemExit(
                f"GitHub API {e.code} on {path}: {e.read().decode('utf-8', 'replace')[:200]}")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = repr(e)[:120]
            continue
    raise SystemExit(f"GitHub API {path} 重试 3 次仍失败（{last}），水位未写回")


def get_default_branch(owner_repo, token):
    """T1 §2.1：先调 API 取 default_branch，不硬编码 main。"""
    repo = gh_get(f"/repos/{owner_repo}", token)
    return repo.get("default_branch") or "main"


def detect_new_commits(owner_repo, entry, token):
    """返回 (commits, new_tip_sha, warnings)。

    entry: 水位 {"sha": ..., "checked_at": ...}，可为空（首次运行）。
    commits: [{"sha","date","message","author"}]，按时间升序（老的在前）。
    """
    warnings = []
    branch = get_default_branch(owner_repo, token)
    tip_sha = gh_get(f"/repos/{owner_repo}/commits/{branch}", token)["sha"]
    base_sha = (entry or {}).get("sha")
    if not base_sha:
        # T1 §2.2：首次运行只建基线，不把整部历史当新增刷屏
        warnings.append("哨兵已上线，基线已建立（本次只记录水位，不产出新增）")
        return [], tip_sha, warnings
    try:
        # 正常路径：水位还在历史里，compare 取精确增量，无遗漏无重复
        commits = gh_get(f"/repos/{owner_repo}/compare/{base_sha}...{tip_sha}", token).get("commits", [])
    except NotFound:
        # force-push 路径：水位 SHA 已不在祖先链里，按时间回退补拉
        since = (entry or {}).get("checked_at") or ""
        warnings.append("水位 SHA 失效（疑似上游 force-push），已按时间回退补拉，请人工核对有无遗漏/重复")
        commits = gh_get(
            f"/repos/{owner_repo}/commits?sha={branch}&since={since}&per_page=100", token)
        commits = [c for c in commits if c["sha"] != base_sha]  # 时间窗口会带回水位时刻的 commit
    out = []
    for c in commits:
        cm = c.get("commit", {})
        out.append({
            "sha": c["sha"],
            "date": (cm.get("author", {}).get("date") or "")[:10],
            "message": (cm.get("message") or "").split("\n")[0][:120],
            "author": ((c.get("author") or {}).get("login")
                       or cm.get("author", {}).get("name") or ""),
        })
    out.sort(key=lambda c: c["date"])
    return out, tip_sha, warnings


def classify_impact(files):
    """单个 commit 的改动文件 × 敏感区清单 → 四类 + 跟进清单。

    files: commit 的 files[]（commit API 的 file 记录，含 filename/status）。
    返回 {"categories": {四类: [path]}, "needs_translation": [path],
            "removed_sensitive": [path], "impacts_zh": bool}。

    说明：removed 且命中敏感区的，归入"修改已汉化文件"
    （该文件汉化版在维护，上游删了它 → 按 PRD-029/T4 三级冲突处理），
    原始 status 保留在 per-file 记录里，另在 removed_sensitive 单列提醒。
    """
    categories = {CAT_NEW: [], CAT_MOD_TRANSLATED: [],
                  CAT_MOD_UNTRANSLATED: [], CAT_NON_SENSITIVE: []}
    per_file = []
    for f in files:
        path = f["filename"]
        status = f.get("status", "")
        sensitive = is_sensitive(path)
        if status == "added":
            cat = CAT_NEW if sensitive else CAT_NON_SENSITIVE
        elif status == "removed":
            cat = CAT_MOD_TRANSLATED if sensitive else CAT_NON_SENSITIVE
        else:  # modified / renamed 等按 modified
            cat = CAT_MOD_TRANSLATED if sensitive else CAT_MOD_UNTRANSLATED
        categories[cat].append(path)
        per_file.append({"path": path, "status": status,
                         "category": cat, "sensitive": sensitive})
    needs = sorted({p["path"] for p in per_file
                    if p["category"] in (CAT_NEW, CAT_MOD_TRANSLATED)})
    removed_sensitive = sorted({p["path"] for p in per_file
                                if p["status"] == "removed" and p["sensitive"]})
    return {"categories": categories,
            "files": per_file,
            "needs_translation": needs,
            "removed_sensitive": removed_sensitive,
            "impacts_zh": any(p["sensitive"] for p in per_file)}


def analyze_commit(owner_repo, sha, token):
    """取单个 commit 的文件列表并做影响面分类。"""
    detail = gh_get(f"/repos/{owner_repo}/commits/{sha}", token)
    cm = detail.get("commit", {})
    rec = {"sha": sha,
           "date": (cm.get("author", {}).get("date") or "")[:10],
           "message": (cm.get("message") or "").split("\n")[0][:120],
           "author": ((detail.get("author") or {}).get("login")
                      or cm.get("author", {}).get("name") or "")}
    impact = classify_impact(detail.get("files", []))
    rec.update(impact)
    return rec


def load_watch_state(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_watch_state(path, state):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")


def run(state_path, token, update_state=False, now=None):
    """一轮哨兵：检测 → 影响面分析 →（可选）写回水位。返回输出 JSON dict。"""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    now_iso = now.isoformat(timespec="seconds")
    state = load_watch_state(state_path)
    result = {"generated_at": now_iso, "warnings": []}
    for key, owner_repo in (("l1", L1_OWNER_REPO), ("l2", L2_OWNER_REPO)):
        commits, tip_sha, warnings = detect_new_commits(owner_repo, state.get(key, {}), token)
        analyzed = [analyze_commit(owner_repo, c["sha"], token) for c in commits]
        result[key] = {"new_commits": analyzed,
                       "impacting_commits": sum(1 for c in analyzed if c["impacts_zh"])}
        result["warnings"].extend(f"[{key}] {w}" for w in warnings)
        state[key] = {"sha": tip_sha, "checked_at": now_iso}
    # T1 §4.2：影响中文版的 commit 数为 0 → quiet_weeks +1，否则清零
    total = result["l1"]["impacting_commits"] + result["l2"]["impacting_commits"]
    state["quiet_weeks"] = (state.get("quiet_weeks") or 0) + 1 if total == 0 else 0
    state["last_run"] = now_iso
    if update_state:
        save_watch_state(state_path, state)
        result["state_updated"] = True
    else:
        result["state_updated"] = False
    return result


def _check(files, exp_categories, exp_needs, exp_impacts):
    got = classify_impact(files)
    assert got["categories"] == exp_categories, f"categories 不对：{got['categories']}"
    assert got["needs_translation"] == exp_needs, f"needs 不对：{got['needs_translation']}"
    assert got["impacts_zh"] is exp_impacts, "impacts_zh 不对"


def _selftest():
    # 四类文件 + 边界：测试文件排除、src-tauri 前缀陷阱、docs/plans 排除、删除敏感文件
    files = [
        {"filename": "surfaces/gui/src/components/NewView.tsx", "status": "added"},
        {"filename": "surfaces/gui/src/App.tsx", "status": "modified"},
        {"filename": "surfaces/gui/src-tauri/src/main.rs", "status": "modified"},
        {"filename": "README.md", "status": "modified"},
        {"filename": "surfaces/gui/src/components/SettingsView.test.tsx", "status": "modified"},
        {"filename": "surfaces/gui/src/components/Legacy.tsx", "status": "removed"},
        {"filename": "docs/plans/notes.md", "status": "added"},
    ]
    _check(files,
           {CAT_NEW: ["surfaces/gui/src/components/NewView.tsx"],
            CAT_MOD_TRANSLATED: ["surfaces/gui/src/App.tsx",
                                 "surfaces/gui/src/components/Legacy.tsx"],
            CAT_MOD_UNTRANSLATED: ["surfaces/gui/src-tauri/src/main.rs",
                                   "README.md",
                                   "surfaces/gui/src/components/SettingsView.test.tsx"],
            CAT_NON_SENSITIVE: ["docs/plans/notes.md"]},
           ["surfaces/gui/src/App.tsx",
            "surfaces/gui/src/components/Legacy.tsx",
            "surfaces/gui/src/components/NewView.tsx"],
           True)
    # 全非敏感 commit → 不影响中文版、无需跟进
    _check([{"filename": ".github/workflows/ci.yml", "status": "modified"}],
           {CAT_NEW: [], CAT_MOD_TRANSLATED: [],
            CAT_MOD_UNTRANSLATED: [".github/workflows/ci.yml"], CAT_NON_SENSITIVE: []},
           [], False)
    # renamed 按 modified 走
    _check([{"filename": "surfaces/gui/src/Renamed.tsx", "status": "renamed"}],
           {CAT_NEW: [], CAT_MOD_TRANSLATED: ["surfaces/gui/src/Renamed.tsx"],
            CAT_MOD_UNTRANSLATED: [], CAT_NON_SENSITIVE: []},
           ["surfaces/gui/src/Renamed.tsx"], True)
    # "测试能 fail"验证：故意写错期望，必须抛 AssertionError，否则自测是摆设
    try:
        _check([{"filename": "surfaces/gui/src/App.tsx", "status": "modified"}],
               {CAT_NEW: ["surfaces/gui/src/App.tsx"], CAT_MOD_TRANSLATED: [],
                CAT_MOD_UNTRANSLATED: [], CAT_NON_SENSITIVE: []},
               [], False)
    except AssertionError:
        pass
    else:
        raise SystemExit("selftest 是摆设：错误期望竟然通过了")
    print("selftest: 全部断言通过（含 fail 能力验证）")


def main():
    ap = argparse.ArgumentParser(description="上游 diff 哨兵（PRD-068/T2）")
    ap.add_argument("--state", required=True, help="水位文件 docs/upstream/watch-state.json")
    ap.add_argument("--update-state", action="store_true", help="写回水位（默认干跑不写）")
    ap.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    ap.add_argument("--selftest", action="store_true", help="只跑内置自测，不调 API")
    args = ap.parse_args()
    if args.selftest:
        _selftest()
        return
    result = run(args.state, args.token, update_state=args.update_state)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
