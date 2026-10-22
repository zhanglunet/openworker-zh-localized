"""流水线里内嵌的 shell 必须能通过 `bash -n`。

为什么单独一条：CI 里的 shell 是**写完就直接上生产**的代码 —— 没有本地运行，
没有类型检查，YAML 校验只看缩进不看脚本内容。语法错误要等到 runner 上才暴露，
而那时往往已经跑完了半小时构建、只差最后一步。

`bash -n` 能抓的是：未闭合的引号、缺 `fi` / `done` / `esac`、重定向写坏、
括号不配对这一类**解析期**错误。

它抓不到什么，同样要说清楚，免得后来人高估这条守卫：
中文文案里嵌双引号（`echo "前面的"中间"后面"`）在 bash 看来完全合法 ——
它把整行拆成若干相邻的引用/非引用段再拼接，引号就这么无声消失了。
那是可读性与健壮性问题（任一段含空格或通配符就会散架），不是语法错误，
这条守卫不负责，别指望它。

per-step 的 `shell:` 覆盖必须尊重 —— Windows 那两步是 pwsh，拿 bash 去解析
会得到一堆假报错，而假报错多了守卫就会被人整条关掉。
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parent.parent

WORKFLOWS = sorted(
    {
        *ROOT.glob(".github/workflows/*.yml"),
        *ROOT.glob("docs/enterprise/templates/*.yml"),
    }
)

BASH_SHELLS = {"bash", "sh"}


def _steps(path: Path):
    """产出 (job 名, 步骤名, shell, 脚本)。shell 按 workflow → job → step 逐级覆盖。"""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or "jobs" not in doc:
        return
    wf_shell = ((doc.get("defaults") or {}).get("run") or {}).get("shell", "bash")
    for job_name, job in (doc.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        job_shell = ((job.get("defaults") or {}).get("run") or {}).get("shell", wf_shell)
        for i, step in enumerate(job.get("steps") or []):
            if not isinstance(step, dict) or not step.get("run"):
                continue
            yield (
                job_name,
                step.get("name", f"step[{i}]"),
                step.get("shell", job_shell),
                step["run"],
            )


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: str(p.relative_to(ROOT)))
def test_embedded_bash_parses(path):
    """把任何一处引号写漏、或 if 忘了配 fi，这条必须变红。"""
    failures = []
    for job_name, step_name, shell, script in _steps(path):
        if shell not in BASH_SHELLS:
            continue
        with tempfile.NamedTemporaryFile(
            "w", suffix=".sh", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(script)
            tmp = Path(fh.name)
        try:
            proc = subprocess.run(
                ["bash", "-n", str(tmp)], capture_output=True, text=True
            )
            if proc.returncode != 0:
                failures.append(
                    f"{path.relative_to(ROOT)} :: {job_name} :: {step_name}\n"
                    f"    {proc.stderr.strip().replace(str(tmp), '<step>')}"
                )
        finally:
            tmp.unlink(missing_ok=True)
    assert not failures, "内嵌 shell 语法错误：\n" + "\n".join(failures)


def test_the_scan_actually_reaches_the_pipelines():
    """扫描范围空了，上面那条就成了摆设。"""
    names = {p.name for p in WORKFLOWS}
    assert "release-corp.yml" in names
    assert len(WORKFLOWS) >= 3


def test_non_bash_steps_are_skipped_not_parsed():
    """Windows 那两步是 pwsh；拿 bash 解析会假报错，假报错会让人关掉守卫。"""
    tmpl = ROOT / "docs/enterprise/templates/release-corp.yml"
    shells = {shell for _, _, shell, _ in _steps(tmpl)}
    assert "pwsh" in shells, "模板里应当有 pwsh 步骤，否则这条断言失去意义"
    assert BASH_SHELLS & shells, "模板里也应当有 bash 步骤"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: str(p.relative_to(ROOT)))
def test_event_path_filters_are_not_mutually_exclusive(path):
    """GitHub rejects an event with both paths and paths-ignore before jobs exist."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    # PyYAML's YAML 1.1 loader reads the unquoted Actions `on` key as True.
    events = doc.get("on", doc.get(True, {}))
    if not isinstance(events, dict):
        return
    for event, config in events.items():
        if isinstance(config, dict):
            assert not {"paths", "paths-ignore"} <= config.keys(), (
                f"{path.relative_to(ROOT)} :: {event}: use ordered negative paths "
                "instead of combining paths and paths-ignore"
            )


def test_quality_gate_keeps_sensitive_paths_and_excludes_only_plans():
    doc = yaml.safe_load((ROOT / ".github/workflows/quality-gate.yml").read_text(encoding="utf-8"))
    event = doc.get("on", doc.get(True))["pull_request"]
    assert event["paths"] == [
        "surfaces/gui/src/**", "docs/**",
        ".github/workflows/quality-gate.yml", "!docs/plans/**",
    ]
