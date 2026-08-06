"""企业知识库检索 MCP server（知识库 v2）。

v2 相对 v1（knowledge_roots 目录挂载）的意义，就是这里要守住的三件事：

* Agent **没有文件系统访问权**，只能拿到检索结果 —— 所以 folder 后端的目录穿越守卫是
  这个文件里最重要的一条测试，破了它 v2 就退化成一个更差的 v1。
* 权限**留在知识库侧**：401/403 要被说清楚是"无权"而不是"服务坏了"，且凭据绝不回显。
* 字段映射靠配置而非代码 —— 所以映射写错时要给可读的错误，不是 KeyError。
"""

from __future__ import annotations

import importlib.util
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

SERVER = (
    Path(__file__).resolve().parent.parent
    / "docs" / "enterprise" / "templates" / "mcp" / "kb-server" / "server.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("kb_server", SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kb = _load()


# -- folder 后端 ---------------------------------------------------------------


@pytest.fixture
def corpus(tmp_path):
    root = tmp_path / "kb"
    (root / "制度").mkdir(parents=True)
    (root / "制度" / "报销管理办法.md").write_text(
        "# 报销管理办法\n市内交通费单次上限 100 元，超出需部门经理审批。\n", encoding="utf-8"
    )
    (root / "制度" / "请假办法.md").write_text("# 请假办法\n年假 10 天。\n", encoding="utf-8")
    (root / "运维" / "重启手册.md").parent.mkdir(parents=True)
    (root / "运维" / "重启手册.md").write_text(
        "# 重启手册\n先摘流量再重启。token=eyJhbGciOiJIUzI1NiJ9.leak.here\n", encoding="utf-8"
    )
    (root / "忽略.pdf").write_bytes(b"%PDF-")
    # 目录外的文件，穿越测试的目标
    (tmp_path / "outside.md").write_text("绝密", encoding="utf-8")
    return root


def _folder_server(root, **cfg):
    raw = {
        "backend": "folder",
        "folder": {"root": str(root), **cfg},
        "limits": {"max_results": 5, "snippet_chars": 200},
        "redact": ["eyJ[A-Za-z0-9_.-]{20,}"],
    }
    backend = kb.build_backend(raw)
    limits = dict(kb.DEFAULT_LIMITS)
    limits.update(raw["limits"])
    return kb.Server(backend, limits)


def test_folder_search_ranks_and_snippets(corpus):
    res = _folder_server(corpus).call("kb_search", {"query": "报销"})
    assert res["ok"] and res["count"] >= 1
    top = res["results"][0]
    assert "报销" in top["title"]
    assert "100 元" in top["snippet"], top["snippet"]


def test_folder_title_hits_outrank_body_hits(corpus):
    """文件名往往就是主题词，标题命中该排前面。"""
    (corpus / "杂记.md").write_text("提到报销两个字但不是主题" * 20, encoding="utf-8")
    res = _folder_server(corpus).call("kb_search", {"query": "报销"})
    assert res["results"][0]["id"].endswith("报销管理办法.md")


def test_keyword_stuffing_cannot_outrank_a_real_title_hit(corpus):
    """词频不做饱和就是在奖励关键词堆砌。

    真实场景里这类文档很常见：变更日志、索引页、会议纪要合集，某个词出现几百次却不是
    它的主题。线性累加下它们会把真正的制度文件挤到后面——这条测试就是钉住饱和逻辑，
    把它换回线性累加必须变红。
    """
    (corpus / "变更日志.md").write_text("报销 " * 500, encoding="utf-8")
    res = _folder_server(corpus).call("kb_search", {"query": "报销"})
    assert res["results"][0]["id"].endswith("报销管理办法.md"), [
        (r["id"], r["score"]) for r in res["results"]
    ]


def test_folder_respects_extensions(corpus):
    res = _folder_server(corpus).call("kb_search", {"query": "PDF"})
    assert all(not r["id"].endswith(".pdf") for r in res["results"])


def test_folder_get_returns_full_text(corpus):
    server = _folder_server(corpus)
    doc_id = server.call("kb_search", {"query": "请假"})["results"][0]["id"]
    doc = server.call("kb_get", {"id": doc_id})
    assert doc["ok"] and "年假 10 天" in doc["content"]


@pytest.mark.parametrize(
    "evil",
    ["../outside.md", "../../etc/passwd", "制度/../../outside.md", "/etc/passwd"],
)
def test_folder_get_refuses_traversal(corpus, evil):
    """本文件最重要的一条：破了它，v2 就退化成一个更差的 v1。"""
    res = _folder_server(corpus).call("kb_get", {"id": evil})
    assert "ok" not in res
    assert "越界" in res["error"] or "找不到" in res["error"]
    assert "绝密" not in json.dumps(res, ensure_ascii=False)


def test_secrets_are_redacted_in_search_and_get(corpus):
    server = _folder_server(corpus)
    hit = server.call("kb_search", {"query": "重启"})
    doc = server.call("kb_get", {"id": "运维/重启手册.md"})
    blob = json.dumps([hit, doc], ensure_ascii=False)
    assert "eyJhbGciOiJIUzI1NiJ9" not in blob
    assert "«已脱敏»" in doc["content"]


def test_limit_is_capped_by_config(corpus):
    for i in range(10):
        (corpus / f"多文档{i}.md").write_text("报销", encoding="utf-8")
    res = _folder_server(corpus).call("kb_search", {"query": "报销", "limit": 999})
    assert res["count"] <= 5


def test_empty_query_is_refused(corpus):
    assert "error" in _folder_server(corpus).call("kb_search", {"query": "   "})


def test_unknown_tool(corpus):
    assert "未知工具" in _folder_server(corpus).call("kb_delete", {})["error"]


def test_missing_root_is_a_config_error(tmp_path):
    with pytest.raises(kb.ConfigError):
        kb.build_backend({"backend": "folder", "folder": {"root": str(tmp_path / "nope")}})


@pytest.mark.parametrize(
    "raw",
    [
        {},
        {"backend": "sql"},
        {"backend": "http", "http": {}},
        {"backend": "http", "http": {"search_url": "u", "fields": {}}},
        {"backend": "folder", "folder": {"root": "."}, "redact": ["("]},
        {"backend": "folder", "folder": {"root": "."}, "limits": {"timeout": "慢"}},
    ],
)
def test_bad_config_is_rejected(raw):
    with pytest.raises(kb.ConfigError):
        kb.build_backend(raw)


# -- http 后端 -----------------------------------------------------------------


class _KB:
    """假知识库。`status` 让我们复现 401/403 这类"无权"路径。"""

    def __init__(self, status: int = 200, shape: str = "nested"):
        self.status, self.shape = status, shape
        self.seen: list[str] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                outer.seen.append(self.headers.get("Authorization", ""))
                if outer.status != 200:
                    self.send_response(outer.status)
                    self.end_headers()
                    return
                if self.path.startswith("/api/doc/"):
                    body = {"data": {"content": "全文内容 token=eyJhbGciOiJIUzI1NiJ9.x.y"}}
                elif outer.shape == "nested":
                    body = {"data": {"items": [
                        {"id": "1", "title": "报销管理办法", "excerpt": "上限 100 元",
                         "url": "https://kb/1"},
                    ]}}
                elif outer.shape == "flat":
                    body = [{"id": "2", "title": "扁平结构"}]
                else:
                    body = {"data": {"items": "不是数组"}}
                raw = json.dumps(body).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        self.httpd = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    @property
    def base(self) -> str:
        host, port = self.httpd.server_address
        return f"http://{host}:{port}"

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def fake_kb():
    made = []

    def build(**kw):
        s = _KB(**kw)
        made.append(s)
        return s

    yield build
    for s in made:
        s.stop()


def _http_server(base, results_path="data.items", fields=None):
    raw = {
        "backend": "http",
        "http": {
            "search_url": f"{base}/api/search",
            "results_path": results_path,
            "fields": fields or {"id": "id", "title": "title", "snippet": "excerpt", "url": "url"},
            "doc_url": f"{base}/api/doc/{{id}}",
            "doc_field": "data.content",
            "headers": {"Authorization": "Bearer ${TEST_KB_TOKEN}"},
        },
        "redact": ["eyJ[A-Za-z0-9_.-]{20,}"],
    }
    return kb.Server(kb.build_backend(raw), dict(kb.DEFAULT_LIMITS))


def test_http_search_maps_declared_fields(fake_kb):
    res = _http_server(fake_kb().base).call("kb_search", {"query": "报销"})
    assert res["ok"] and res["results"][0]["title"] == "报销管理办法"
    assert res["results"][0]["url"] == "https://kb/1"


def test_http_token_comes_from_the_environment(fake_kb, monkeypatch):
    monkeypatch.setenv("TEST_KB_TOKEN", "from-env")
    server = fake_kb()
    _http_server(server.base).call("kb_search", {"query": "x"})
    assert server.seen and server.seen[0] == "Bearer from-env"


@pytest.mark.parametrize("status", [401, 403])
def test_permission_errors_say_so_without_echoing_credentials(fake_kb, status, monkeypatch):
    """权限在知识库侧，那这里就必须把"无权"和"服务坏了"分清楚 —— 否则用户会去找运维。"""
    monkeypatch.setenv("TEST_KB_TOKEN", "super-secret")
    res = _http_server(fake_kb(status=status).base).call("kb_search", {"query": "x"})
    assert "无权" in res["error"]
    assert "super-secret" not in json.dumps(res, ensure_ascii=False)


def test_unreachable_kb_is_a_clean_error():
    server = _http_server("http://127.0.0.1:9")  # discard port
    assert "不可达" in server.call("kb_search", {"query": "x"})["error"]


def test_wrong_results_path_gives_a_readable_error(fake_kb):
    res = _http_server(fake_kb().base, results_path="data.wrong").call("kb_search", {"query": "x"})
    assert "找不到结果数组" in res["error"] and "data.wrong" in res["error"]


def test_flat_response_without_results_path(fake_kb):
    res = _http_server(fake_kb(shape="flat").base, results_path="").call("kb_search", {"query": "x"})
    assert res["ok"] and res["results"][0]["title"] == "扁平结构"


def test_non_list_results_is_reported(fake_kb):
    res = _http_server(fake_kb(shape="broken").base).call("kb_search", {"query": "x"})
    assert "找不到结果数组" in res["error"]


def test_http_get_redacts_document_body(fake_kb):
    doc = _http_server(fake_kb().base).call("kb_get", {"id": "1"})
    assert doc["ok"] and "eyJhbGciOiJIUzI1NiJ9" not in doc["content"]


def test_get_without_doc_url_is_explained(fake_kb):
    raw = {
        "backend": "http",
        "http": {"search_url": f"{fake_kb().base}/api/search", "fields": {"title": "title"}},
    }
    server = kb.Server(kb.build_backend(raw), dict(kb.DEFAULT_LIMITS))
    assert "只能检索不能取全文" in server.call("kb_get", {"id": "1"})["error"]


def test_shipped_example_config_is_valid_for_both_backends(tmp_path):
    example = SERVER.parent / "kb.example.json"
    raw = json.loads(example.read_text(encoding="utf-8"))
    assert kb.build_backend(raw) is not None  # http 分支
    raw["backend"] = "folder"
    raw["folder"]["root"] = str(tmp_path)
    assert kb.build_backend(raw) is not None  # folder 分支


def test_check_mode(corpus, tmp_path, capsys):
    cfg = tmp_path / "kb.json"
    cfg.write_text(
        json.dumps({"backend": "folder", "folder": {"root": str(corpus)}}), encoding="utf-8"
    )
    assert kb.main(["--config", str(cfg), "--check", "--query", "报销"]) == 0
    assert "报销" in capsys.readouterr().out
