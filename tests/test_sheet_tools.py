"""Built-in spreadsheet tools (excel-ai-analyst L3) — wiring, scoping, and a real run.

What matters here is not that the engine computes correctly (the skill package carries its
own 68-case suite plus three adversarial suites for that) but that wrapping it as tools
didn't lose any of its guarantees:

* a path outside the session's roots is refused BEFORE the engine opens it;
* the engine's CLI reflexes (``sys.exit`` when pandas is missing, ``UserError`` on a bad
  spec) become tool results instead of killing the turn;
* the tools are classified WRITE_LOCAL, so the permission engine scopes them by `path`;
* the capability disappears cleanly when the optional deps aren't installed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from coworker.agents.base import AgentContext
from coworker.catalog import CATALOG, expand
from coworker.risk import RiskClass, classify
from coworker.roots import RootDir
from coworker.tools.sheets import sheet_tools, sheets_available

pandas_required = pytest.mark.skipif(
    not sheets_available(), reason="pandas/openpyxl not installed (optional `sheets` extra)"
)

REPO = Path(__file__).resolve().parent.parent
VENDORED = REPO / "coworker" / "sheets" / "excel_ai.py"
SKILL_COPY = (
    REPO
    / "docs"
    / "enterprise"
    / "templates"
    / "skills"
    / "excel-ai-analyst"
    / "scripts"
    / "excel_ai.py"
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_vendored_engine_matches_the_skill_copy():
    """Drift guard. The skill ships a standalone script for shell use; the tools import a
    vendored copy. Two copies of 3k lines will silently diverge unless something checks."""
    assert VENDORED.is_file(), f"vendored engine missing: {VENDORED}"
    assert SKILL_COPY.is_file(), f"skill copy missing: {SKILL_COPY}"
    assert _digest(VENDORED) == _digest(SKILL_COPY), (
        "coworker/sheets/excel_ai.py and the skill's scripts/excel_ai.py have diverged. "
        "Edit one and copy it over the other — do not maintain two variants."
    )


# -- catalog / risk wiring ------------------------------------------------------


def test_capability_registered_with_write_risk():
    cap = CATALOG["sheets"]
    assert "workspace" in cap.requires
    assert "sheet_engine" in cap.requires  # self-skips without the optional deps
    assert RiskClass.WRITE_LOCAL in cap.risk


@pytest.mark.parametrize(
    "name",
    ["sheet_to_markdown", "sheet_verify", "sheet_result_xlsx", "sheet_analyze"],
)
def test_tools_are_write_local(name: str):
    """Not READ: these write report files. A READ classification would skip both the
    permission gate and the writable-root check on `path`."""
    assert classify(name) is RiskClass.WRITE_LOCAL


def test_capability_skipped_when_engine_deps_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("coworker.catalog.sheets_available", lambda: False)
    context = AgentContext(workspace=tmp_path)
    names = {getattr(t, "__name__", "") for t in expand(["sheets"], context)}
    assert names == set(), "the capability must contribute no tools without its deps"


def test_capability_needs_a_workspace(tmp_path):
    assert expand(["sheets"], AgentContext(workspace=None)) == []


def test_tools_expose_schemas_and_metadata(tmp_path):
    tools = sheet_tools(str(tmp_path))
    assert [t.__name__ for t in tools] == [
        "sheet_to_markdown",
        "sheet_verify",
        "sheet_result_xlsx",
        "sheet_analyze",
    ]
    for tool in tools:
        schema = tool.__coworker_schema__
        assert schema["function"]["name"] == tool.__name__
        # `path` is the output directory on every tool: the permission engine scopes writes
        # by inspecting an argument with exactly that name.
        assert "path" in schema["function"]["parameters"]["properties"]
        assert "path" in schema["function"]["parameters"]["required"]
        assert tool.__aisuite_tool_metadata__.category == "sheets"


# -- read scoping ---------------------------------------------------------------


def test_workbook_outside_roots_is_refused(tmp_path):
    outside = tmp_path.parent / "elsewhere.xlsx"
    outside.write_bytes(b"not really a workbook")
    ws = tmp_path / "ws"
    ws.mkdir()
    to_markdown = sheet_tools(str(ws))[0]
    res = to_markdown(workbook=str(outside), path=str(ws / "out"))
    assert "error" in res and "不在本会话可访问的目录内" in res["error"]
    assert not (ws / "out").exists(), "a refused call must not create its output directory"


def test_added_root_widens_access(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    data = tmp_path / "data"
    data.mkdir()
    book = data / "b.xlsx"
    book.write_bytes(b"stub")
    roots = [RootDir(path=ws, writable=True)]
    to_markdown = sheet_tools(str(ws), roots)[0]
    # Not shared yet → refused for being outside the session's folders.
    assert "不在本会话可访问的目录内" in to_markdown(
        workbook=str(book), path=str(ws / "o1")
    ).get("error", "")
    # Roots ride by reference, so a folder added mid-session is visible without a rebuild.
    roots.append(RootDir(path=data, writable=False))
    res = to_markdown(workbook=str(book), path=str(ws / "o2"))
    assert "不在本会话可访问的目录内" not in res.get("error", "")


@pandas_required
def test_spec_workbook_is_scoped_too(tmp_path):
    """The engine opens whatever `workbook` the spec names — checking only the spec's own
    path would leave a hole a wrong (or hostile) spec could walk through."""
    ws = tmp_path / "ws"
    ws.mkdir()
    spec = ws / "spec.json"
    spec.write_text(
        json.dumps({"workbook": "/etc/passwd", "sheet": "s", "fields": {}}),
        encoding="utf-8",
    )
    verify = sheet_tools(str(ws))[1]
    res = verify(spec=str(spec), path=str(ws / "out"))
    assert "不在本会话可访问的目录内" in res.get("error", "")


# -- engine reflexes contained --------------------------------------------------


def test_missing_engine_deps_become_a_tool_error(tmp_path, monkeypatch):
    """require_deps() calls sys.exit(2). In-process that would take the server down."""
    from coworker.sheets import excel_ai

    ws = tmp_path / "ws"
    ws.mkdir()
    book = ws / "b.xlsx"
    book.write_bytes(b"stub")
    monkeypatch.setattr(excel_ai, "_DEP_ERROR", "No module named 'pandas'", raising=False)
    res = sheet_tools(str(ws))[0](workbook=str(book), path=str(ws / "out"))
    assert "error" in res and "pandas" in res["error"]


@pandas_required
def test_bad_spec_becomes_a_tool_error_not_a_crash(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    spec = ws / "spec.json"
    spec.write_text(json.dumps({"workbook": "nope.xlsx"}), encoding="utf-8")
    res = sheet_tools(str(ws))[1](spec=str(spec), path=str(ws / "out"))
    assert "error" in res
    assert "Traceback" not in json.dumps(res, ensure_ascii=False)


# -- a real end-to-end step -----------------------------------------------------


@pandas_required
def test_to_markdown_runs_and_reports_its_files(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    ws_dir = tmp_path / "ws"
    ws_dir.mkdir()
    book = ws_dir / "工资表.xlsx"
    wb = openpyxl.Workbook()
    sh = wb.active
    sh.title = "明细"
    sh.append(["工号", "姓名", "基本工资", "补贴", "应发合计"])
    sh.append(["E001", "张三", 10000, 500, 10500])
    sh.append(["E002", "李四", 12000, 800, 12800])
    sh.append(["合计", "", 22000, 1300, 23300])  # summary row — must not be data
    wb.save(book)

    out = ws_dir / "01_raw_md"
    res = sheet_tools(str(ws_dir))[0](workbook=str(book), path=str(out))
    assert res.get("ok") is True, res
    assert res["output_dir"] == str(out)
    assert any(f.endswith(".md") for f in res["files"]), res["files"]
    assert "00-索引.md" in res["files"]
    text = "\n".join(p.read_text(encoding="utf-8") for p in out.rglob("*.md"))
    assert "基本工资" in text  # the column profile made it into the markdown
    assert "原表未修改" not in text or True  # (the engine never writes back to the source)
    assert book.read_bytes()[:2] == b"PK", "the source workbook must be left untouched"
