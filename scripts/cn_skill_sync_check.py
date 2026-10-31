# -*- coding: utf-8 -*-
"""PRD-212/T2 中文角色包跨工具同步检查脚本（trend #1061）。

按 docs/plans/2026-10-26-cn-skill-sync-checklist-design.md（T1 设计）实现：
  - CN-SYNC-01~03 安装类（装了没）：目录存在 / SKILL.md 元数据 / 附属资源齐全
  - CN-SYNC-04~06 版本类（对不对）：版本可读 / 版本号一致 / 内容指纹一致
  - CN-SYNC-07~09 残留类（旧版清没清）：旧版目录 / 孤儿文件 / 索引缓存（名单待实测，恒记 SKIP）
  - CN-SYNC-10~12 触发词类属 T3，本脚本统一记 NOT_TESTED，不阻断结论
  - 短路规则与结论聚合按 T1 §5.2/§6；输出 skill × 工具状态表（markdown / json）

manifest 为唯一真源（T1 §1）：manifests/<发布批次>.json，可先用 generate-manifest
子命令从 role-packs 现状生成基准。

用法：
  python3 scripts/cn_skill_sync_check.py generate-manifest --batch <批次名> \
      [--skills-root role-packs] [--out manifests/<批次名>.json]
  python3 scripts/cn_skill_sync_check.py check --manifest manifests/<批次名>.json \
      [--tools claude-code,cursor,codex,pi] [--home <主目录覆盖，测试用>] [--format md|json]

零网络；不安装、不卸载、不写任何工具目录（只读检查）。
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# T1 §2：四工具用户级 skills 根目录（占位约定；项目级路径待实测，暂不启用）
TOOL_ROOTS = {
    "claude-code": ".claude/skills",
    "cursor": ".cursor/skills",
    "codex": ".codex/skills",
    "pi": ".pi/agent/skills",
}

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
TRIGGER_QUOTE_RE = re.compile(r"「([^」]{2,30})」")
RESIDUE_PATTERNS = ("@", "-v")  # <skill-id>@* 与 <skill-id>-v* 视为旧版目录

P0_FAIL, P1_FAIL, P2_WARN, P3_WARN = "P0", "P1", "P2", "P3"


class ManifestError(ValueError):
    """manifest 缺字段或格式不合法。"""


# ---------------------------------------------------------------------------
# manifest 加载与生成（T1 §1：唯一真源）
# ---------------------------------------------------------------------------
def load_manifest_dict(data):
    entries = data.get("skills")
    if not isinstance(entries, list) or not entries:
        raise ManifestError("manifest 缺少非空 skills[] 数组")
    for e in entries:
        for key in ("skill_id", "expected_version", "files"):
            if key not in e:
                raise ManifestError("manifest 条目缺字段 %r：%s" % (key, e.get("skill_id")))
        for f in e["files"]:
            if "path" not in f or "sha256" not in f:
                raise ManifestError("files[] 条目需含 path+sha256：%r" % f)
    return data


def load_manifest(path):
    return load_manifest_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def parse_frontmatter(text):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fields = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fields[key.strip()] = val.strip()
    return fields


def _sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_manifest(skills_root, batch, version_default="0.1.0"):
    """从仓库 role-packs 现状生成 manifest（files 含 SHA-256 指纹）。"""
    root = Path(skills_root)
    skills = []
    for skill_md in sorted(root.glob("*/skills/*/SKILL.md")):
        skill_dir = skill_md.parent
        fields = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        version_file = skill_dir / "VERSION"
        version = fields.get("version") or (
            version_file.read_text(encoding="utf-8").strip() if version_file.exists() else ""
        )
        if not VERSION_RE.match(version):
            version = version_default
        files = [
            {"path": p.relative_to(skill_dir).as_posix(), "sha256": _sha256_file(p)}
            for p in sorted(skill_dir.rglob("*"))
            if p.is_file()
        ]
        desc = fields.get("description", "")
        skills.append({
            "skill_id": fields.get("name") or skill_dir.name,
            "skill_name": fields.get("name") or skill_dir.name,
            "expected_version": version,
            "files": files,
            "history": [],
            "triggers": {"standard": TRIGGER_QUOTE_RE.findall(desc)[:3]},
        })
    return {
        "batch": batch,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "skills": skills,
    }


# ---------------------------------------------------------------------------
# 已装版本读取（T1 §1 优先级：frontmatter version: → VERSION 文件 → UNKNOWN）
# ---------------------------------------------------------------------------
def read_installed_version(skill_dir):
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        fields = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        if VERSION_RE.match(fields.get("version", "")):
            return fields["version"]
    version_file = skill_dir / "VERSION"
    if version_file.exists():
        candidate = version_file.read_text(encoding="utf-8").strip()
        if VERSION_RE.match(candidate):
            return candidate
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# CN-SYNC-01~09 检查实现（T1 §3、§6 短路规则）
# ---------------------------------------------------------------------------
def check_skill_tool(entry, tool, tool_root):
    """对单个 skill × 工具执行 CN-SYNC-01~09，返回 §5.1 状态行。"""
    skill_id = entry["skill_id"]
    row = {
        "skill_id": skill_id,
        "skill_name": entry.get("skill_name", skill_id),
        "tool": tool,
        "install_status": "MISSING",
        "installed_version": "UNKNOWN",
        "expected_version": entry["expected_version"],
        "version_drift": "SKIP",
        "residue": "NONE",
        "trigger_result": "NOT_TESTED",
        "trigger_detail": "待抽查",
        "conclusion": "SKIP",
        "blocking_items": [],
    }
    skill_dir = tool_root / skill_id
    fails = {}  # 检查项 ID -> 严重程度

    # CN-SYNC-01 目录存在（失败即短路，02/03 及后续全部记 SKIP）
    if not (skill_dir.is_dir()):
        row["blocking_items"] = ["CN-SYNC-01"]
        row["checked_at"] = _now()
        return row
    row["version_drift"] = "NONE"

    # CN-SYNC-02 SKILL.md 元数据完整（缺文件 P0；字段不一致 P1）
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        fails["CN-SYNC-02"] = P0_FAIL
    else:
        fields = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        if not all(k in fields and fields[k] for k in ("name", "description", "version")):
            fails["CN-SYNC-02"] = P1_FAIL
        elif fields["name"] != skill_id:
            fails["CN-SYNC-02"] = P1_FAIL

    # CN-SYNC-03 附属资源齐全（对照 manifest files[]：存在且非空）
    for f in entry["files"]:
        target = skill_dir / f["path"]
        if not target.exists() or target.stat().st_size == 0:
            fails["CN-SYNC-03"] = P1_FAIL

    row["install_status"] = "PARTIAL" if fails else "INSTALLED"

    # CN-SYNC-04~06 版本类（06 不受 04 影响；04 失败则 05 记 SKIP）
    installed = read_installed_version(skill_dir)
    row["installed_version"] = installed
    if installed == "UNKNOWN":
        fails["CN-SYNC-04"] = P1_FAIL
        row["version_drift"] = "UNREADABLE"
    else:
        if installed != entry["expected_version"]:
            fails["CN-SYNC-05"] = P1_FAIL
            row["version_drift"] = "VERSION_DRIFT"
    for f in entry["files"]:
        target = skill_dir / f["path"]
        if target.exists() and target.stat().st_size > 0 \
                and _sha256_file(target) != f["sha256"]:
            fails["CN-SYNC-06"] = P1_FAIL
            row["version_drift"] = "CONTENT_DRIFT"  # 内容漂移优先于版本漂移呈现

    # CN-SYNC-07~09 残留类
    patterns = [entry.get("history", []),
                [skill_id + s for s in RESIDUE_PATTERNS]]
    found_old = [d.name for d in tool_root.iterdir()
                 if d.is_dir() and d.name != skill_id and (
                     d.name in patterns[0]
                     or any(d.name.startswith(skill_id + s) for s in RESIDUE_PATTERNS))]
    if found_old:
        fails["CN-SYNC-07"] = P2_WARN
        row["residue"] = "OLD_DIR"
    manifest_paths = {f["path"] for f in entry["files"]}
    actual_paths = {p.relative_to(skill_dir).as_posix()
                    for p in skill_dir.rglob("*") if p.is_file()}
    orphans = sorted(actual_paths - manifest_paths)
    if orphans:
        fails["CN-SYNC-08"] = P2_WARN
        row["residue"] = ",".join(filter(None, [row["residue"], "ORPHAN_FILES"]))
    # CN-SYNC-09 索引/缓存：工具名单待 T2 实测确认后冻结，本轮恒记 SKIP（不产生 WARN）

    # 结论聚合（T1 §5.2）：触发词 NOT_TESTED 不阻断
    hard = [k for k, v in fails.items() if v in (P0_FAIL, P1_FAIL)]
    soft = [k for k, v in fails.items() if v in (P2_WARN, P3_WARN)]
    if hard:
        row["conclusion"] = "FAIL"
        row["blocking_items"] = sorted(hard)
    elif soft:
        row["conclusion"] = "WARN"
        row["blocking_items"] = sorted(soft)
    else:
        row["conclusion"] = "PASS"
    row["checked_at"] = _now()
    return row


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_check(manifest, tools, home_override=None):
    """manifest 全部 skill × 指定工具，返回状态行列表。"""
    rows = []
    for entry in manifest["skills"]:
        for tool in tools:
            rel = TOOL_ROOTS[tool]
            if home_override is not None:
                tool_root = Path(home_override) / rel
            else:
                tool_root = Path.home() / rel
            rows.append(check_skill_tool(entry, tool, tool_root))
    return rows


# ---------------------------------------------------------------------------
# 输出（T1 §5：skill × 工具状态表）
# ---------------------------------------------------------------------------
FIELDS = ["skill_id", "skill_name", "tool", "install_status", "installed_version",
          "expected_version", "version_drift", "residue", "trigger_result",
          "trigger_detail", "conclusion", "blocking_items"]


def render_markdown(rows, batch):
    lines = ["# 中文技能包同步状态表（批次 %s）" % batch, "",
             "| %s |" % " | ".join(FIELDS),
             "|%s|" % "|".join(["---"] * len(FIELDS))]
    for r in rows:
        lines.append("| %s |" % " | ".join(str(r[f]) for f in FIELDS))
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="PRD-212 中文技能包跨工具同步检查（只读）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("generate-manifest", help="从 role-packs 现状生成 manifest")
    gen.add_argument("--batch", required=True)
    gen.add_argument("--skills-root", default="role-packs")
    gen.add_argument("--out", default=None)

    chk = sub.add_parser("check", help="对照 manifest 检查各工具安装状态")
    chk.add_argument("--manifest", required=True)
    chk.add_argument("--tools", default=",".join(TOOL_ROOTS))
    chk.add_argument("--home", default=None, help="主目录覆盖（测试用）")
    chk.add_argument("--format", choices=["md", "json"], default="md")
    chk.add_argument("--out", default=None, help="写文件而非 stdout")
    args = ap.parse_args(argv)

    if args.cmd == "generate-manifest":
        data = generate_manifest(args.skills_root, args.batch)
        text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(text, encoding="utf-8")
            print("已生成 %s（%d 个 skill）" % (args.out, len(data["skills"])))
        else:
            sys.stdout.write(text)
        return 0

    manifest = load_manifest(args.manifest)
    tools = [t.strip() for t in args.tools.split(",") if t.strip()]
    unknown = [t for t in tools if t not in TOOL_ROOTS]
    if unknown:
        raise SystemExit("未知工具（应为 %s）：%s" % (",".join(TOOL_ROOTS), ",".join(unknown)))
    rows = run_check(manifest, tools, args.home)
    text = render_markdown(rows, manifest.get("batch", "-")) if args.format == "md" \
        else json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print("已写出 %s（%d 行状态）" % (args.out, len(rows)))
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
