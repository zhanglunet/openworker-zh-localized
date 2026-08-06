"""Spreadsheet reverse-engineering tools (excel-ai-analyst / 大表哥, L3).

The skill (`excel-ai-analyst`) drives the same engine through a shell script. These tools
expose it as first-class callables instead, which buys three things the shell path can't:

* **No shell approval per step.** `run_shell` is EXEC-risk and prompts unless the user put
  `python3` on the allowlist; these are WRITE_LOCAL and scope to the session's writable
  roots like any other file write.
* **Works in the frozen sidecar.** The desktop build has no `python3` on PATH — it *is* the
  frozen binary — so shelling out to a script is not an option there.
* **Read scoping.** A spreadsheet path (and every `workbook` named inside a spec.json) is
  checked against the session's roots before the engine ever opens it.

The heavy dependencies (pandas, openpyxl) are an optional extra: the capability is skipped
entirely when they're absent (see `catalog.py`), so a default install pays no tool-schema
cost for a feature it can't run.

Methodology (why the tools are shaped this way) lives in the skill's SKILL.md. The short
version: step 1 turns the workbook into structured markdown, the agent *hand-writes* the
field ontology and formula chain into a spec.json, step 4 replays that understanding over
every real row, and only a 100% pass earns the right to analyse. Skipping verification is
editing code you haven't read.
"""

from __future__ import annotations

import argparse
import io
import json
import os
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Optional

import aisuite as ai

# Keep the log we hand back to the model bounded — these commands are chatty and the
# interesting part (what was written, what didn't match) is always at the end.
_LOG_TAIL = 4000

_INSTALL_HINT = (
    "表格分析引擎需要 pandas 与 openpyxl。请安装后重试："
    "pip install 'coworker[sheets]'（或 pip install pandas openpyxl）。"
)


def _resolve(path: str, workspace: Path) -> Path:
    p = Path(path).expanduser()
    return p.resolve() if p.is_absolute() else (workspace / p).resolve()


def _root_paths(workspace: Path, roots: Optional[list]) -> list[Path]:
    if roots:
        out = []
        for r in roots:
            rp = getattr(r, "path", None)
            if rp is not None:
                out.append(Path(rp).resolve())
        if out:
            return out
    return [workspace]


def _check_readable(path: str, workspace: Path, roots: Optional[list]) -> Optional[str]:
    """None when the path sits inside a session root, else the error to return.

    Writes are already path-scoped by the permission engine (it inspects the `path`
    argument); reads are not, so a spreadsheet outside the session's folders is refused
    here rather than quietly opened.
    """
    candidate = _resolve(path, workspace)
    for root in _root_paths(workspace, roots):
        try:
            candidate.relative_to(root)
            return None
        except ValueError:
            continue
    return (
        f"路径不在本会话可访问的目录内：{path}。"
        "请先把表格所在文件夹添加为工作目录，再重试。"
    )


def _spec_workbooks(spec_path: Path) -> list[str]:
    """Workbook paths named inside a spec.json — the engine opens these, so they need the
    same root check as a directly-passed file. A malformed spec returns nothing: the engine
    reports it far better than a half-parse here would."""
    try:
        data = json.loads(spec_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(data, dict):
        return []
    found: list[str] = []
    wb = data.get("workbook")
    if isinstance(wb, str) and wb:
        found.append(wb)
    for entry in data.get("cross_checks") or []:
        if isinstance(entry, dict):
            other = entry.get("workbook")
            if isinstance(other, str) and other:
                found.append(other)
    return found


def _listing(out_dir: Path) -> list[str]:
    if not out_dir.is_dir():
        return []
    return sorted(
        str(p.relative_to(out_dir))
        for p in out_dir.rglob("*")
        if p.is_file()
    )


def _run(command: str, args: argparse.Namespace, out_dir: Path) -> dict[str, Any]:
    """Call one engine subcommand in-process, with its console output captured.

    In-process rather than a subprocess on purpose: the desktop sidecar is a PyInstaller
    freeze, so `sys.executable` is the app itself and `python3 -m …` would relaunch the
    server. The cost is that the engine's CLI reflexes have to be contained — it calls
    `sys.exit(2)` when pandas is missing, which would otherwise take the server down.
    """
    from ..sheets import excel_ai  # lazy: pandas/openpyxl only load on first real use

    fn = getattr(excel_ai, f"cmd_{command}")
    buf_out, buf_err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            code = fn(args)
    except SystemExit:
        # require_deps() exits rather than raising; the message it printed names the
        # import that failed, which is worth keeping.
        detail = (buf_err.getvalue() or buf_out.getvalue()).strip()
        return {"error": _INSTALL_HINT, "detail": detail[-_LOG_TAIL:]}
    except excel_ai.UserError as exc:
        return {"error": str(exc), "log": buf_out.getvalue()[-_LOG_TAIL:]}
    except FileNotFoundError as exc:
        return {"error": f"找不到文件：{exc}"}
    except PermissionError as exc:
        return {"error": f"没有权限读写：{exc}"}
    except OSError as exc:
        return {"error": f"文件系统操作失败：{exc}"}
    except Exception as exc:  # noqa: BLE001 - a tool must not take the turn down
        return {"error": f"表格分析失败（{type(exc).__name__}）：{exc}"}

    log = (buf_out.getvalue() + buf_err.getvalue()).strip()
    return {
        "ok": code == 0,
        "output_dir": str(out_dir),
        "files": _listing(out_dir),
        "log": log[-_LOG_TAIL:],
    }


_TOMD_SCHEMA = {
    "type": "function",
    "function": {
        "name": "sheet_to_markdown",
        "description": (
            "Step 1 of spreadsheet reverse-engineering: convert a workbook into structured "
            "markdown — multi-row headers flattened, merged cells expanded, REAL cell formulas "
            "extracted, per-column profile (sample values, fill rate, inferred type, warnings). "
            "Read this before claiming to understand a sheet. Writes markdown into `path`."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "workbook": {
                    "type": "string",
                    "description": "Path to the .xlsx/.xlsm file to convert.",
                },
                "path": {
                    "type": "string",
                    "description": "Output directory for the generated markdown (created if absent).",
                },
                "sheets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Only convert these sheet names (default: all).",
                },
                "header_rows": {
                    "type": "integer",
                    "description": "Force the header row count instead of inferring it.",
                },
                "preview_rows": {
                    "type": "integer",
                    "description": "Data preview rows per sheet (default 10).",
                },
            },
            "required": ["workbook", "path"],
        },
    },
}

_VERIFY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "sheet_verify",
        "description": (
            "Step 4, the core of the method: replay your understanding (a spec.json of field "
            "bindings, derived values and check expressions) over EVERY real row and compare "
            "against the workbook's own values. Produces a pass rate plus a mismatch list. "
            "A mismatch means either you misread the sheet or the sheet itself is wrong — the "
            "latter is the most valuable thing this finds. Never analyse before this passes."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "spec": {"type": "string", "description": "Path to spec.json."},
                "path": {
                    "type": "string",
                    "description": "Output directory for the verification report and detail CSV.",
                },
            },
            "required": ["spec", "path"],
        },
    },
}

_RESULT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "sheet_result_xlsx",
        "description": (
            "Step 5a: write the annotated result workbook — blue = original input, green = "
            "AI-computed, orange = differs beyond tolerance — plus check-summary, data-lineage "
            "and field-ontology sheets taken from the spec. Needs sheet_verify's detail CSV."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "spec": {"type": "string", "description": "Path to spec.json."},
                "detail": {
                    "type": "string",
                    "description": "verification_detail.csv produced by sheet_verify.",
                },
                "path": {"type": "string", "description": "Output directory."},
            },
            "required": ["spec", "detail", "path"],
        },
    },
}

_ANALYZE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "sheet_analyze",
        "description": (
            "Step 5b: business analysis report from a verified sheet — group summaries, value "
            "distributions, top/bottom, outliers (IQR or z-score), rule-based anomalies, and "
            "What-If scenarios. Reads the spec's `analysis` section. Needs sheet_verify's "
            "detail CSV. The report is a skeleton: the actual insight is yours to write."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "spec": {
                    "type": "string",
                    "description": "Path to spec.json (its `analysis` section drives the report).",
                },
                "detail": {
                    "type": "string",
                    "description": "verification_detail.csv produced by sheet_verify.",
                },
                "path": {"type": "string", "description": "Output directory."},
            },
            "required": ["spec", "detail", "path"],
        },
    },
}


def _tag(fn, schema: dict) -> None:
    name = schema["function"]["name"]
    fn.__name__ = name
    fn.__doc__ = schema["function"]["description"]
    fn.__coworker_schema__ = schema
    fn.__aisuite_tool_metadata__ = ai.ToolMetadata(
        name=name,
        category="sheets",
        risk_level="medium",  # writes files; risk.py classifies these as WRITE_LOCAL
        capabilities=["sheets"],
        requires_approval=False,
    )


def sheet_tools(workspace: str, roots: Optional[list] = None) -> list:
    """The four engine steps as tools. `roots` is the session's live RootDir list (held by
    reference, so folders added mid-session are visible here too)."""
    ws = Path(workspace).resolve()

    def guard(*paths: str) -> Optional[dict[str, Any]]:
        for p in paths:
            err = _check_readable(p, ws, roots)
            if err:
                return {"error": err}
        return None

    def sheet_to_markdown(
        workbook: str,
        path: str,
        sheets: Optional[list] = None,
        header_rows: Optional[int] = None,
        preview_rows: int = 10,
    ) -> dict[str, Any]:
        blocked = guard(workbook)
        if blocked:
            return blocked
        from ..sheets import excel_ai

        out = _resolve(path, ws)
        args = argparse.Namespace(
            files=[str(_resolve(workbook, ws))],
            output=str(out),
            sheets=list(sheets) if sheets else None,
            header_scan=8,
            header_rows=header_rows,
            preview_rows=preview_rows if isinstance(preview_rows, int) else 10,
            # main() fills this in for the CLI; in-process we have to do it ourselves or
            # every summary row silently doubles the totals.
            summary_words=excel_ai.DEFAULT_SUMMARY_WORDS,
        )
        return _run("tomd", args, out)

    def sheet_verify(spec: str, path: str) -> dict[str, Any]:
        blocked = guard(spec)
        if blocked:
            return blocked
        spec_path = _resolve(spec, ws)
        blocked = guard(*_spec_workbooks(spec_path))
        if blocked:
            return blocked
        out = _resolve(path, ws)
        args = argparse.Namespace(spec=str(spec_path), output=str(out))
        return _run("verify", args, out)

    def sheet_result_xlsx(spec: str, detail: str, path: str) -> dict[str, Any]:
        blocked = guard(spec, detail)
        if blocked:
            return blocked
        out = _resolve(path, ws)
        args = argparse.Namespace(
            spec=str(_resolve(spec, ws)),
            detail=str(_resolve(detail, ws)),
            output=str(out),
        )
        return _run("output", args, out)

    def sheet_analyze(spec: str, detail: str, path: str) -> dict[str, Any]:
        blocked = guard(spec, detail)
        if blocked:
            return blocked
        out = _resolve(path, ws)
        args = argparse.Namespace(
            spec=str(_resolve(spec, ws)),
            detail=str(_resolve(detail, ws)),
            output=str(out),
        )
        return _run("analyze", args, out)

    _tag(sheet_to_markdown, _TOMD_SCHEMA)
    _tag(sheet_verify, _VERIFY_SCHEMA)
    _tag(sheet_result_xlsx, _RESULT_SCHEMA)
    _tag(sheet_analyze, _ANALYZE_SCHEMA)
    return [sheet_to_markdown, sheet_verify, sheet_result_xlsx, sheet_analyze]


def sheets_available() -> bool:
    """Whether the engine's heavy deps are importable. Drives the catalog requirement, so a
    default install never pays the tool-schema cost for a feature it can't run."""
    try:
        import openpyxl  # noqa: F401
        import pandas  # noqa: F401
    except Exception:
        return False
    return True


__all__ = ["sheet_tools", "sheets_available"]
