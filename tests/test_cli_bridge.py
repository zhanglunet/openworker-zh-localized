"""企业 CLI → MCP 桥。

把 `corp-cli` 直接加进 allowed_commands，等于交出这个 CLI 的全部子命令和全部参数。
本桥的存在意义就是不那样做，所以这里测的重点不是"能不能跑通"，而是**不该能做的事真的做不到**：
未声明的子命令、未声明的参数、shell 注入、类型/枚举越界、超时、凭据回流。
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import stat
from pathlib import Path

import pytest

BRIDGE = (
    Path(__file__).resolve().parent.parent
    / "docs" / "enterprise" / "templates" / "mcp" / "cli-bridge" / "server.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("cli_bridge", BRIDGE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cb = _load()


@pytest.fixture
def fake_cli(tmp_path):
    """一个假 CLI：把收到的 argv 原样吐回来，方便断言"到底传了什么"。"""
    script = tmp_path / "corp-cli"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys, time\n"
        "argv = sys.argv[1:]\n"
        "if argv[:1] == ['sleep']:\n"
        "    time.sleep(float(argv[1]))\n"
        "if argv[:1] == ['leak']:\n"
        "    print('token=eyJhbGciOiJIUzI1NiJ9.super.secret')\n"
        "    sys.exit(0)\n"
        "if argv[:1] == ['env']:\n"
        "    print(json.dumps({k: v for k, v in os.environ.items()}))\n"
        "    sys.exit(0)\n"
        "if argv[:1] == ['fail']:\n"
        "    sys.stderr.write('boom\\n'); sys.exit(3)\n"
        "if argv[:1] == ['flood']:\n"
        "    print('x' * 100000); sys.exit(0)\n"
        "print(json.dumps(argv))\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return script


def _spec(cli: Path, **overrides) -> dict:
    spec = {
        "defaults": {"timeout": 10, "max_output": 500, "redact": ["eyJ[A-Za-z0-9_.-]{20,}"]},
        "tools": [
            {
                "name": "ticket_search",
                "description": "搜索工单",
                "argv": [str(cli), "ticket", "search"],
                "params": [
                    {"name": "query", "type": "string", "required": True},
                    {"name": "status", "type": "string", "flag": "--status",
                     "enum": ["open", "closed"]},
                    {"name": "limit", "type": "integer", "flag": "--limit"},
                    {"name": "notify", "type": "boolean", "flag": "--notify"},
                ],
            }
        ],
    }
    spec.update(overrides)
    return spec


def run(bridge, name, args):
    return asyncio.run(bridge.call(name, args))


# -- spec 校验：坏配置必须启动即失败，而不是带着半个配置跑起来 ----------------------


@pytest.mark.parametrize(
    "spec",
    [
        {},
        {"tools": []},
        {"tools": [{"name": "x"}]},                                   # 缺 description/argv
        {"tools": [{"name": "x", "description": "d", "argv": []}]},   # argv 为空
        {"tools": [{"name": "有中文", "description": "d", "argv": ["a"]}]},
        {"tools": [{"name": "a", "description": "d", "argv": ["x"],
                    "params": [{"name": "p", "type": "date"}]}]},     # 未知类型
        {"tools": [{"name": "a", "description": "d", "argv": ["x"]},
                   {"name": "a", "description": "d", "argv": ["y"]}]},  # 重名
        {"defaults": {"redact": ["("]}, "tools": [                     # 坏正则
            {"name": "a", "description": "d", "argv": ["x"]}]},
    ],
)
def test_bad_spec_is_rejected(spec):
    with pytest.raises(cb.SpecError):
        cb.Bridge(spec)


def test_check_mode_lists_tools(fake_cli, tmp_path, capsys):
    path = tmp_path / "tools.json"
    path.write_text(json.dumps(_spec(fake_cli)), encoding="utf-8")
    assert cb.main(["--spec", str(path), "--check"]) == 0
    assert "ticket_search" in capsys.readouterr().out


def test_missing_spec_exits_nonzero(tmp_path):
    assert cb.main(["--spec", str(tmp_path / "nope.json"), "--check"]) == 2


# -- 白名单：只有声明过的能做 --------------------------------------------------


def test_undeclared_tool_is_refused(fake_cli):
    bridge = cb.Bridge(_spec(fake_cli))
    res = run(bridge, "ticket_delete", {"id": "1"})
    assert res["ok"] is False and "未声明" in res["error"]


def test_undeclared_param_is_refused_not_ignored(fake_cli):
    """静默忽略会让调用方以为参数生效了 —— 对 --force 这种参数，后果是灾难性的。"""
    bridge = cb.Bridge(_spec(fake_cli))
    res = run(bridge, "ticket_search", {"query": "x", "force": True})
    assert res["ok"] is False and "未声明的参数" in res["error"]


def test_missing_required_param(fake_cli):
    bridge = cb.Bridge(_spec(fake_cli))
    assert "缺少必填参数" in run(bridge, "ticket_search", {})["error"]


@pytest.mark.parametrize(
    "args, hint",
    [
        ({"query": "x", "limit": "many"}, "integer"),
        ({"query": "x", "limit": True}, "integer"),   # bool 是 int 子类，别混过去
        ({"query": 5}, "string"),
        ({"query": "x", "status": "deleted"}, "只能取"),
    ],
)
def test_type_and_enum_are_enforced(fake_cli, args, hint):
    bridge = cb.Bridge(_spec(fake_cli))
    res = run(bridge, "ticket_search", args)
    assert res["ok"] is False and hint in res["error"]


# -- 注入：argv 直传，不经 shell ------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    ["; rm -rf /", "$(whoami)", "`id`", "x | cat /etc/passwd", "x && echo pwned", "x\nid"],
)
def test_shell_metacharacters_stay_literal(fake_cli, payload):
    bridge = cb.Bridge(_spec(fake_cli))
    res = run(bridge, "ticket_search", {"query": payload})
    assert res["ok"] is True
    argv = json.loads(res["stdout"])
    # 载荷原样作为一个实参出现，没有被拆开、也没有被求值
    assert argv == ["ticket", "search", payload]


def test_flags_and_positionals_render_as_declared(fake_cli):
    bridge = cb.Bridge(_spec(fake_cli))
    res = run(bridge, "ticket_search", {"query": "磁盘", "status": "open", "limit": 5})
    assert json.loads(res["stdout"]) == ["ticket", "search", "磁盘", "--status", "open", "--limit", "5"]


def test_boolean_false_omits_the_flag(fake_cli):
    bridge = cb.Bridge(_spec(fake_cli))
    on = json.loads(run(bridge, "ticket_search", {"query": "q", "notify": True})["stdout"])
    off = json.loads(run(bridge, "ticket_search", {"query": "q", "notify": False})["stdout"])
    assert "--notify" in on and "--notify" not in off


# -- 运行时边界 ----------------------------------------------------------------


def test_nonzero_exit_is_reported_not_raised(fake_cli):
    spec = _spec(fake_cli)
    spec["tools"][0]["argv"] = [str(fake_cli), "fail"]
    spec["tools"][0]["params"] = []
    res = run(cb.Bridge(spec), "ticket_search", {})
    assert res["ok"] is False and res["exit_code"] == 3 and "boom" in res["stderr"]


def test_timeout_kills_the_child(fake_cli):
    spec = _spec(fake_cli)
    spec["tools"][0] = {
        "name": "slow", "description": "d",
        "argv": [str(fake_cli), "sleep", "5"], "timeout": 1,
    }
    res = run(cb.Bridge(spec), "slow", {})
    assert res["ok"] is False and "超时" in res["error"]


def test_output_is_truncated(fake_cli):
    spec = _spec(fake_cli)
    spec["tools"][0] = {"name": "flood", "description": "d", "argv": [str(fake_cli), "flood"]}
    res = run(cb.Bridge(spec), "flood", {})
    assert len(res["stdout"]) < 1000 and "已截断" in res["stdout"]


def test_secrets_are_redacted_before_returning(fake_cli):
    """CLI 打出来的 token 不该回流进对话与日志。"""
    spec = _spec(fake_cli)
    spec["tools"][0] = {"name": "leak", "description": "d", "argv": [str(fake_cli), "leak"]}
    res = run(cb.Bridge(spec), "leak", {})
    assert "eyJhbGciOiJIUzI1NiJ9" not in res["stdout"]
    assert "«已脱敏»" in res["stdout"]


def test_environment_is_not_inherited_wholesale(fake_cli, monkeypatch):
    monkeypatch.setenv("CORP_TOKEN", "wanted")
    monkeypatch.setenv("UNRELATED_SECRET", "should-not-leak")
    spec = _spec(fake_cli)
    spec["defaults"]["env_passthrough"] = ["CORP_TOKEN"]
    spec["tools"][0] = {"name": "env", "description": "d", "argv": [str(fake_cli), "env"]}
    env = json.loads(run(cb.Bridge(spec), "env", {})["stdout"])
    assert env.get("CORP_TOKEN") == "wanted"
    assert "UNRELATED_SECRET" not in env


def test_missing_executable_is_a_clean_error(tmp_path):
    spec = _spec(tmp_path / "does-not-exist")
    res = run(cb.Bridge(spec), "ticket_search", {"query": "x"})
    assert res["ok"] is False and "找不到可执行文件" in res["error"]


def test_shipped_example_spec_is_valid():
    example = BRIDGE.parent / "tools.example.json"
    bridge = cb.Bridge(json.loads(example.read_text(encoding="utf-8")))
    assert {"ticket_search", "ticket_get", "ticket_create"} <= set(bridge.tools)
    schema = bridge.tools["ticket_create"].schema()
    assert schema["required"] == ["title"]
    assert schema["additionalProperties"] is False
