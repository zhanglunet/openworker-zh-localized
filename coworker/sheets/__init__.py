"""Spreadsheet reverse-engineering engine (excel-ai-analyst / 大表哥).

`excel_ai` is vendored verbatim from the skill package
(`docs/enterprise/templates/skills/excel-ai-analyst/scripts/excel_ai.py`) so the built-in
tools in `coworker/tools/sheets.py` can call it in-process — the desktop sidecar is a
PyInstaller freeze with no `python3` to shell out to. `tests/test_sheet_tools.py` asserts
the two copies stay byte-identical; edit the skill copy and re-sync, never fork them.

Nothing is imported here: `excel_ai` pulls in pandas/openpyxl, which are an optional extra.
Import it lazily, inside the call that needs it.
"""
