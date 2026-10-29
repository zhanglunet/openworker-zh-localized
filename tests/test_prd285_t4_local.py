# -*- coding: utf-8 -*-
"""PRD-285/T4 自测（trend #1429）：本地处理断言——快照/回滚/抽查全链零网络（AST/源码扫描）。

运行：.venv/bin/python -m pytest tests/test_prd285_t4_local.py -q

覆盖（T4 验收"断言通过"，≥6 例）：
  AST 断言两模块零网络 import（requests/urllib/socket/http.client/http/ssl/…）
  两模块 import 面仅 stdlib 白名单（copy/hashlib/json/uuid/datetime/pathlib/typing）
  spotcheck_archive 源码零网络字面量（http(s)/ws(s)/ftp(s) URL 形态、网络模块名、
                    子进程调用形态；skillpack_snapshot 加扫同断言）
  全流程（take_snapshot → spot_check → restore）执行期零网络：
                    socket/urllib/http.client 全部封桩为陷阱，全链跑通零触发
  抽查记录落档本地路径：spotcheck-record-v1 落本地 audit.jsonl（本地文件路径、
                    无 URL/host 形态、记录 JSON 零网络字面量、读回一致）
  确定性：全链两遍快照指纹/抽查记录/JSONL 字节逐字段一致

红线自证（trend #1429）：本地处理（全链零网络，T2/T3 最小实现之上以 AST+源码+
运行期封桩三道钉死）；示例全中文虚构（zh-sales-lead-brief 等占位）；
不含真实主机名、IP、账号、密钥。
"""
import ast
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, REPO / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ssp = _load("skillpack_snapshot", "scripts/skillpack_snapshot.py")   # T2
sca = _load("spotcheck_archive", "scripts/spotcheck_archive.py")     # T3

TARGETS = {"skillpack_snapshot": REPO / "scripts/skillpack_snapshot.py",
           "spotcheck_archive": REPO / "scripts/spotcheck_archive.py"}

T0 = "2026-10-29T09:00:00+08:00"
T1 = "2026-10-29T09:05:00+08:00"

# 网络/子进程模块（AST import 零引入；T2/T3 模块自述"仅 copy/hashlib/json/
# uuid/datetime/pathlib/typing 标准库"）
NET_MODULES = {"requests", "urllib", "urllib.request", "urllib.parse",
               "http", "http.client", "socket", "ssl", "ftplib", "smtplib",
               "telnetlib", "subprocess", "asyncio", "websockets", "websocket"}
STDLIB_WHITELIST = {"copy", "hashlib", "json", "uuid", "datetime",
                    "pathlib", "typing", "__future__"}
# 源码网络字面量（URL 形态 / 网络与子进程调用名），小写匹配
NETWORK_LITERALS = (
    "http://", "https://", "ws://", "wss://", "ftp://", "ftps://",
    "socket", "urllib", "requests.", "http.client", "urlopen",
    "getaddrinfo", "create_connection", "gethostbyname",
    "subprocess", "os.system", "popen",
    "localhost", "127.0.0.1", "0.0.0.0",
)


def sample_pack():
    """虚构中文技能包（与 T2/T3 测试同源的占位样例）。"""
    return {
        "zh-sales-lead-brief/SKILL.md": (
            "---\nname: zh-sales-lead-brief\n"
            "description: 每日销售线索简报（虚构示例技能）\n---\n\n"
            "按触发词「销售简报」调用本技能。\n"
        ),
        "zh-sales-lead-brief/references/playbook.md": (
            "# 跟进手册（虚构示例）\n\n第一步：占位步骤。\n"
        ),
    }


def tampered_snapshot(snapshot):
    """篡改快照副本：内容与清单记录不符（抽查应检出，触发自动回滚）。"""
    bad = json.loads(json.dumps(snapshot, ensure_ascii=False))
    first = sorted(bad["files"])[0]
    bad["files"][first]["content"] = bad["files"][first]["content"] + "\n（升级写坏一行，占位）\n"
    return bad


def _poison_network(testcase):
    """socket/urllib/http.client 封桩为陷阱——全链期间任何网络调用即炸。"""
    import socket as socket_mod
    import urllib.request
    import http.client

    def _boom(*args, **kwargs):
        raise AssertionError("网络调用发生（PRD-285 零网络红线被触发）: "
                             "%s%s" % (args[:1], kwargs))

    poisons = [
        (socket_mod, "socket"), (socket_mod, "create_connection"),
        (socket_mod, "getaddrinfo"), (socket_mod, "gethostbyname"),
        (socket_mod, "gethostbyaddr"),
        (urllib.request, "urlopen"),
        (http.client, "HTTPConnection"), (http.client, "HTTPSConnection"),
    ]
    saved = [(obj, name, getattr(obj, name)) for obj, name in poisons]
    for obj, name, _ in saved:
        setattr(obj, name, _boom)
    testcase.addCleanup(lambda: [setattr(obj, name, old)
                                 for obj, name, old in saved])


class TestPrd285T4Local(unittest.TestCase):
    # 1. AST 断言两模块零网络 import
    def test_01_ast_zero_network_imports(self):
        for name, path in TARGETS.items():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            roots = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    roots.append(node.module)
            net = sorted({r for r in roots if r.split(".")[0] in NET_MODULES})
            self.assertEqual(net, [], "%s 引入网络/子进程模块: %s" % (name, net))

    # 2. 两模块 import 面仅 stdlib 白名单
    def test_02_import_surface_stdlib_whitelist(self):
        for name, path in TARGETS.items():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            roots = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots.extend(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    roots.append(node.module.split(".")[0])
            outside = sorted(set(roots) - STDLIB_WHITELIST)
            self.assertEqual(outside, [],
                             "%s import 面超出 stdlib 白名单: %s" % (name, outside))

    # 3. 源码零网络字面量（spotcheck_archive 主断言；skillpack_snapshot 加扫）
    def test_03_source_zero_network_literals(self):
        for name, path in TARGETS.items():
            low = path.read_text(encoding="utf-8").lower()
            hits = sorted({t for t in NETWORK_LITERALS if t in low})
            self.assertEqual(hits, [], "%s 源码命中网络字面量: %s" % (name, hits))

    # 4. 全流程（snapshot → spot_check → restore）执行期零网络（socket 封桩）
    def test_04_full_flow_runtime_zero_network(self):
        _poison_network(self)
        with tempfile.TemporaryDirectory(prefix="prd285_t4_flow_") as tmp:
            audit_path = Path(tmp) / "audit.jsonl"

            # 场景 A：抽查全过（failed=0）→ 不回滚，记录落档
            ssp.clear_slot()
            snap = ssp.take_snapshot(sample_pack(), T0)
            flow = sca.upgrade_flow_with_check(
                snap, restore_fn=ssp.restore, check_fn=ssp.spot_check,
                at=T1, audit_path=audit_path)
            self.assertEqual(flow["record"]["failed"], 0)
            self.assertFalse(flow["rolled_back"])
            self.assertIsNone(flow["restored"])

            # 场景 B：升级写坏 → 抽查检出（failed>0）→ 按单槽快照自动回滚旧包
            ssp.clear_slot()
            snap = ssp.take_snapshot(sample_pack(), T0)
            bad = tampered_snapshot(snap)
            flow = sca.upgrade_flow_with_check(
                bad, restore_fn=ssp.restore, check_fn=ssp.spot_check,
                at=T1, audit_path=audit_path)
            self.assertEqual(flow["record"]["failed"], 1)
            self.assertTrue(flow["rolled_back"])
            self.assertEqual(flow["restored"], sample_pack())  # 目录级还原旧包

            # 抽查记录两场景均落档
            records = sca.read_records(audit_path)
            self.assertEqual([r["failed"] for r in records], [0, 1])

    # 5. 抽查记录落档本地路径（本地文件、无 URL/host 形态、记录零网络字面量）
    def test_05_spotcheck_record_lands_local_path(self):
        ssp.clear_slot()
        snap = ssp.take_snapshot(sample_pack(), T0)
        with tempfile.TemporaryDirectory(prefix="prd285_t4_archive_") as tmp:
            audit_path = Path(tmp) / "audit.jsonl"
            ssp.clear_slot()
            flow = sca.upgrade_flow_with_check(
                snap, restore_fn=ssp.restore, check_fn=ssp.spot_check,
                at=T1, audit_path=audit_path)
            # 落档为本地文件系统路径（绝对路径、无 URL scheme）
            self.assertTrue(audit_path.is_file())
            self.assertTrue(Path(audit_path).is_absolute())
            self.assertNotIn("://", str(audit_path))
            # 记录 schema 固定六字段，记录 JSON 全文零网络字面量
            records = sca.read_records(audit_path)
            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record["schema"], sca.SPOTCHECK_RECORD_SCHEMA)
            self.assertEqual(
                set(record), {"schema", "snapshot_fingerprint", "checked",
                              "passed", "failed", "at"})
            text = json.dumps(record, ensure_ascii=False).lower()
            hits = sorted({t for t in NETWORK_LITERALS if t in text})
            self.assertEqual(hits, [], "抽查记录命中网络字面量: %s" % hits)
            # 读回与 flow 返回一致（本地存档可信）
            self.assertEqual(record, flow["record"])

    # 6. 确定性（全链两遍：指纹/记录/JSONL 字节逐字段一致）
    def test_06_deterministic(self):
        runs = []
        for _ in range(2):
            ssp.clear_slot()
            snap = ssp.take_snapshot(sample_pack(), T0)
            with tempfile.TemporaryDirectory(prefix="prd285_t4_det_") as tmp:
                audit_path = Path(tmp) / "audit.jsonl"
                ssp.clear_slot()
                flow = sca.upgrade_flow_with_check(
                    snap, restore_fn=ssp.restore, check_fn=ssp.spot_check,
                    at=T1, audit_path=audit_path)
                runs.append({
                    "fingerprint": snap["fingerprint"],
                    "record": flow["record"],
                    "bytes": audit_path.read_bytes(),
                })
        self.assertEqual(runs[0]["fingerprint"], runs[1]["fingerprint"])
        self.assertEqual(runs[0]["record"], runs[1]["record"])
        self.assertEqual(runs[0]["bytes"], runs[1]["bytes"])  # 同内容必同字节


if __name__ == "__main__":
    unittest.main()
