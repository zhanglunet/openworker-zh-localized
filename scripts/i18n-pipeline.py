#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
i18n-pipeline.py — PRD-084/T2 翻译流水线（opencode 式多语言 README 自动化）。

把 PRD-068 哨兵的 needs_translation 清单变成中文翻译 diff（初稿），
术语锁定 + 链接检查自带，最后由人工审校决定是否合并。

设计稿：docs/plans/2026-10-19-i18n-pipeline-design.md（T1，用户三项决策已拍板）。
纯标准库。单文件。

流水线（设计 §1）：
  哨兵 needs_translation JSON ──▶ 本脚本 ──▶ 中文翻译 diff ＋ PR-BODY.md ＋ report.json
                                              （人工审校 → 合并，见 --help 的 [i18n] PR 规范）

翻译引擎（设计 §2，用户决策① C 混合方案）：
  SiliconForge 网关（OpenAI 兼容）出初稿 ＋ 确定性术语后处理，双保险。
  凭据：一律从环境变量读，绝不硬编码、不写文件、不打日志：
    I18N_GATEWAY_API_KEY  （必填，缺失则直接报错退出）
    I18N_GATEWAY_URL      （默认 http://127.0.0.1:8337，即网关本地代理约定）
    I18N_MODEL            （默认 AI/Qwen3.8-Flash-Next，不用 auto）
  网关挂掉 → 失败退出，不输出半成品（文档翻译是周级低频，不要求高可用）。

术语（设计 §3，用户决策①）：
  prompt 注入（system prompt 附 25 条术语表）＋ 后处理确定性替换，双保险。
  术语表源头：运行时优先从 scripts/quality-gate.py 的 TERMS 常量 import
  （同一份表，不另立第二份）；import 失败时用内嵌副本兜底（--self-test 会校验条数）。
  后处理只对“本次翻译涉及的术语”执法（英文原文里出现过的术语）：
  英文原形 → 拍板译法；已知错误译法（wrongs）→ 拍板译法（仅当该术语在原文出现过，
  防“走 PRD-029 流程”这类误伤——067/T5 试运行已证实 blind 替换会 corrupt 正确中文）。
  代码块 / 行内代码 / URL 内的术语不受影响。

自检（本脚本产出即自带；CI 术语锁定是 T3 的事，两者互补）：
  术语锁定：后处理后仍有英文术语残留 → 报错退出（非零）。
  链接检查（用户决策② B）：内链（仓库内相对路径）断了 → 报错；
                           外链（http/https）不可达 → 只警告，不阻断。
  占位符：中英文 {…} 占位符集合不一致 → 报错（沿用 067 规则）。

输入（设计 §1.1）：
  {"source": "weekly-report | manual", "source_ref": "...",
   "items": [{"path": "README.md", "status": "added|modified", "upstream_sha": "a79f7c47"}]}
  status=removed 的文件不进流水线（走 PRD-029/T4 冲突流程）；
  docs/plans/、*test* 沿用 067 排除口径，不进流水线。
  上游英文按 upstream_sha 从 andrewyng/openworker 拉取（--upstream-repo 可覆盖）。

特殊处理（设计 §1.3）：
  surfaces/gui/src/locales/zh.json 命中时不做“翻译”，改做“对照 diff”：
  取该 commit 与其父 commit 的官方 zh.json，输出变更对照表（.compare.md）。

CLI:
  --input JSON        哨兵清单 JSON 文件（见上）
  --repo-root DIR     本地仓库根（读现有中文版，默认当前目录）
  --out-dir DIR       产出目录（默认 ./i18n-out）；--dry-run 时只打印不写盘
  --dry-run           跑完全流程但不写文件（diff 打印到 stdout）
  --self-test         内置正反用例自测（无网络），全部通过才算过
  --gateway-url URL   覆盖网关地址（默认读 I18N_GATEWAY_URL）
  --model MODEL       覆盖模型（默认读 I18N_MODEL）
  --terms-file PATH   术语表覆盖文件（`英文=中文` 每行一条；只改表不改代码）
  --upstream-repo R   上游仓库（默认 andrewyng/openworker）
"""

import argparse
import difflib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

# ---------------------------------------------------------------------------
# 术语表：优先从 quality-gate.py 同一份 TERMS 读（设计 §3），失败用内嵌副本
# ---------------------------------------------------------------------------
TERMS_SOURCE = "内嵌副本"
try:
    from quality_gate import TERMS as _QG_TERMS  # noqa
    TERMS = _QG_TERMS
    TERMS_SOURCE = "scripts/quality-gate.py"
except Exception:
    TERMS = [
        {"en": r"agents?",          "zh": "智能体",   "wrongs": ["代理"]},
        {"en": r"workflows?",       "zh": "工作流",   "wrongs": ["流程"]},
        {"en": r"runs?",            "zh": "运行",     "wrongs": []},
        {"en": r"sessions?",        "zh": "会话",     "wrongs": []},
        {"en": r"inbox(?:es)?",     "zh": "收件箱",   "wrongs": []},
        {"en": r"approvals?",       "zh": "审批",     "wrongs": []},
        {"en": r"prompts?",         "zh": "提示词",   "wrongs": []},
        {"en": r"models?",          "zh": "模型",     "wrongs": []},
        {"en": r"providers?",       "zh": "服务商",   "wrongs": ["供应商"]},
        {"en": r"tool\s*calls?",    "zh": "工具调用", "wrongs": []},
        {"en": r"skills?",          "zh": "技能",     "wrongs": []},
        {"en": r"personas?",        "zh": "角色",     "wrongs": []},
        {"en": r"coworkers?",       "zh": "数字同事", "wrongs": []},
        {"en": r"onboarding",       "zh": "新手引导", "wrongs": []},
        {"en": r"settings",         "zh": "设置",     "wrongs": []},
        {"en": r"sidebars?",        "zh": "侧边栏",   "wrongs": []},
        {"en": r"(?:failure|failures|failed)", "zh": "失败", "wrongs": []},
        {"en": r"retr(?:y|ies)",    "zh": "重试",     "wrongs": []},
        {"en": r"summar(?:y|ies)",  "zh": "摘要",     "wrongs": ["总结"]},
        {"en": r"builds?",          "zh": "构建",     "wrongs": []},
        {"en": r"test\s*suites?",   "zh": "测试套件", "wrongs": []},
        {"en": r"connectors?",      "zh": "连接器",   "wrongs": []},
        {"en": r"mentions?",        "zh": "提及",     "wrongs": []},
        {"en": r"threads?",         "zh": "会话串",   "wrongs": []},
        {"en": r"attachments?",     "zh": "附件",     "wrongs": []},
    ]

TERMS_VERSION = "25 条，拍板日期 2026-10-18"
DEFAULT_MODEL = "AI/Qwen3.8-Flash-Next"
DEFAULT_GATEWAY_URL = "http://127.0.0.1:8337"
UPSTREAM_DEFAULT = "andrewyng/openworker"
ZH_JSON_PATH = "surfaces/gui/src/locales/zh.json"
EXCLUDE_PREFIXES = ("docs/plans/",)
CHUNK_CHARS = 1800       # 每批翻译的英文字符上限
REF_ZH_CHARS = 2500      # 旧中文版做风格参考时的截断长度
LINK_TIMEOUT = 10        # 外链检查超时（秒），重试 1 次


class PipelineError(Exception):
    """流水线失败（调用方按此区分报错退出）。"""


class GatewayError(PipelineError):
    """网关调用失败：key 缺失 / 网络错误 / 非 200。"""


# ---------------------------------------------------------------------------
# 输入解析（设计 §1.1）
# ---------------------------------------------------------------------------
def parse_input(data):
    """校验哨兵清单 JSON，返回 items 列表。removed / plans / test 直接排除。"""
    if not isinstance(data, dict) or "items" not in data:
        raise PipelineError("输入 JSON 必须含 items 数组")
    items = []
    for it in data["items"]:
        for k in ("path", "status", "upstream_sha"):
            if k not in it:
                raise PipelineError("item 缺字段 %r: %r" % (k, it))
        path = it["path"]
        if it["status"] == "removed":
            continue  # 设计 §1.1：删文件走 PRD-029/T4 冲突流程，不进流水线
        if path.startswith(EXCLUDE_PREFIXES) or "test" in path.lower():
            continue  # 设计 §6：过程稿与测试排除
        if it["status"] not in ("added", "modified"):
            raise PipelineError("未知 status %r: %s" % (it["status"], path))
        items.append({"path": path, "status": it["status"],
                      "upstream_sha": it["upstream_sha"]})
    return {"source": data.get("source", "manual"),
            "source_ref": data.get("source_ref", ""),
            "items": items}


# ---------------------------------------------------------------------------
# 上游英文拉取（设计 §1.1：按 upstream_sha 经 compare/API 约定拉取）
# ---------------------------------------------------------------------------
def fetch_upstream(path, sha, repo=UPSTREAM_DEFAULT):
    url = "https://raw.githubusercontent.com/%s/%s/%s" % (repo, sha, path)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.read().decode("utf-8")
    except Exception as e:
        raise PipelineError("拉取上游英文失败 %s@%s: %s" % (path, sha[:8], e))


def fetch_upstream_parent_sha(sha, repo=UPSTREAM_DEFAULT):
    url = "https://api.github.com/repos/%s/commits/%s" % (repo, sha)
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode("utf-8"))
        return d["parents"][0]["sha"]
    except Exception as e:
        raise PipelineError("取父 commit 失败 %s: %s" % (sha[:8], e))


# ---------------------------------------------------------------------------
# 网关翻译层（设计 §2）：OpenAI 兼容，key 只从环境变量读
# ---------------------------------------------------------------------------
def _terms_prompt_lines(terms):
    return ["%s → %s" % (t["en"], t["zh"]) for t in terms]


def gateway_translate(en_text, ref_zh=None, terms=None,
                      gateway_url=None, model=None, timeout=60):
    """调网关翻译一批英文。失败抛 GatewayError（不输出半成品）。key 绝不打日志。"""
    terms = terms if terms is not None else TERMS
    api_key = os.environ.get("I18N_GATEWAY_API_KEY")
    if not api_key:
        raise GatewayError("I18N_GATEWAY_API_KEY 未设置：翻译需调用方配置网关密钥")
    base = (gateway_url or os.environ.get("I18N_GATEWAY_URL")
            or DEFAULT_GATEWAY_URL).rstrip("/")
    mdl = model or os.environ.get("I18N_MODEL") or DEFAULT_MODEL

    system = ("你是一名英中技术文档翻译。把用户给出的英文 Markdown 翻译成简体中文。\n"
              "要求：\n"
              "1) 保留所有 Markdown 格式、代码块、链接、占位符（如 {input}）原样不动；\n"
              "2) 以下术语必须严格使用指定译法，不得意译：\n"
              + "\n".join(_terms_prompt_lines(terms)) + "\n"
              "3) 只输出译文正文，不要解释、不要加前后缀。")
    user = en_text
    if ref_zh:
        user += ("\n\n----\n以下为该文档当前的中文版（风格与措辞参考，"
                 "只需翻译上面的英文新内容，保持与旧版一致的措辞）：\n" + ref_zh)

    body = json.dumps({
        "model": mdl,
        "temperature": 0.2,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
    }).encode("utf-8")
    req = urllib.request.Request(
        base + "/v1/chat/completions", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + api_key})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status != 200:
                raise GatewayError("网关返回 HTTP %s" % r.status)
            d = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise GatewayError("网关 HTTP %s（不输出半成品）" % e.code)
    except GatewayError:
        raise
    except Exception as e:
        raise GatewayError("网关调用失败（不输出半成品）: %s" % e)
    try:
        text = d["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise GatewayError("网关返回体不是 chat-completions 格式")
    text = text.strip()
    m = re.match(r"^```(?:markdown|md)?\s*\n(.*?)\n```\s*$", text, re.S)
    return m.group(1) if m else text


# ---------------------------------------------------------------------------
# 确定性术语后处理（设计 §3）：只对本次翻译涉及的术语执法
# ---------------------------------------------------------------------------
_FENCE_RE = re.compile(r"(```.*?```)", re.S)
_INLINE_CODE_RE = re.compile(r"(`[^`\n]+?`)")
_URL_RE = re.compile(r"https?://[^\s)>\]]+")


def _split_protected(text):
    """把文本切成 (is_protected, 片段)：代码块/行内代码/URL 不动，其余可处理。"""
    parts = []
    for chunk in _FENCE_RE.split(text):
        if chunk.startswith("```"):
            parts.append((True, chunk))
            continue
        pos = 0
        for m in list(_INLINE_CODE_RE.finditer(chunk)) + list(_URL_RE.finditer(chunk)):
            pass
        # 合并两种保护模式，按位置排序切分
        marks = sorted(
            [(m.start(), m.end()) for m in _INLINE_CODE_RE.finditer(chunk)] +
            [(m.start(), m.end()) for m in _URL_RE.finditer(chunk)])
        for s, e in marks:
            if s > pos:
                parts.append((False, chunk[pos:s]))
            parts.append((True, chunk[s:e]))
            pos = e
        parts.append((False, chunk[pos:]))
    return parts


def _compile_terms(terms):
    return [(t, re.compile(r"\b" + t["en"] + r"\b", re.IGNORECASE)) for t in terms]


def involved_terms(en_text, terms=None):
    """英文原文里出现过的术语（本次翻译涉及的）——只对它们执法。"""
    terms = terms if terms is not None else TERMS
    return [t for t, rx in _compile_terms(terms) if rx.search(en_text)]


def apply_terms(en_text, zh_text, terms=None):
    """后处理：英文原形→拍板译法；wrongs→拍板译法（仅当该术语在原文出现过）。

    保护代码块/行内代码/URL。连续重复译法做一次归一（如“服务商（服务商）”→“服务商”）。
    """
    terms = terms if terms is not None else TERMS
    active = involved_terms(en_text, terms)
    if not active:
        return zh_text
    compiled = [(t, re.compile(r"\b" + t["en"] + r"\b", re.IGNORECASE))
                for t in active]
    out = []
    for protected, seg in _split_protected(zh_text):
        if protected:
            out.append(seg)
            continue
        for t, rx in compiled:
            seg = rx.sub(t["zh"], seg)
            for w in t["wrongs"]:
                if w and w in seg:
                    seg = seg.replace(w, t["zh"])
        out.append(seg)
    text = "".join(out)
    for t in active:  # 归一：“服务商（服务商）”/“服务商 服务商”→“服务商”
        z = re.escape(t["zh"])
        text = re.sub(z + r"[（(]\s*" + z + r"\s*[)）]", t["zh"], text)
        text = re.sub(z + r"\s+" + z, t["zh"], text)
    return text


def self_check_terms(en_text, zh_text, terms=None):
    """术语锁定自检：后处理后仍有英文术语残留（保护区外）→ failure。

    wrongs 只查“本次涉及的术语”（与 apply_terms 同口径，避免“走 PRD-029 流程”误伤）。
    返回 [failure]，failure={"check","line","expected","detail"}。
    """
    terms = terms if terms is not None else TERMS
    active = involved_terms(en_text, terms)
    failures = []
    for lineno, line in enumerate(zh_text.splitlines(), 1):
        prose = "".join(seg for p, seg in _split_protected(line) if not p)
        for t in active:
            if re.search(r"\b" + t["en"] + r"\b", prose, re.IGNORECASE):
                failures.append({"check": "术语锁定自检", "line": lineno,
                                 "expected": t["zh"],
                                 "detail": "英文术语 %r 残留未译" % t["en"]})
            for w in t["wrongs"]:
                if w and w in prose:
                    failures.append({"check": "术语锁定自检", "line": lineno,
                                     "expected": t["zh"],
                                     "detail": "错误译法 %r，应为 %r" % (w, t["zh"])})
    return failures


# ---------------------------------------------------------------------------
# 链接检查（设计 §5.2，用户决策② B：内链阻断，外链警告）
# ---------------------------------------------------------------------------
_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_REF_DEF_RE = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)", re.M)


def _iter_link_targets(text):
    for m in _LINK_RE.finditer(text):
        yield m.group(1)
    for m in _REF_DEF_RE.finditer(text):
        yield m.group(1)


def _anchor_ok(text, anchor):
    norm = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", anchor.lower())
    if not norm:
        return True
    for line in text.splitlines():
        h = re.match(r"^#{1,6}\s+(.*)", line)
        if h and norm in re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", h.group(1).lower()):
            return True
    return False


def check_links(zh_text, file_path, repo_root, urlopen=None):
    """返回 (errors, warnings)。内链文件缺失→error；外链不可达→warning；锚点疑似缺失→warning。"""
    urlopen = urlopen or urllib.request.urlopen
    errors, warnings = [], []
    seen_external = set()
    file_dir = os.path.dirname(os.path.join(repo_root, file_path))
    try:
        with open(os.path.join(repo_root, file_path), encoding="utf-8") as f:
            _ = f.read()  # 当前文件存在性（翻译前可能不存在，属正常）
    except OSError:
        pass
    for target in _iter_link_targets(zh_text):
        if target.startswith(("http://", "https://")):
            if target in seen_external:
                continue
            seen_external.add(target)
            ok = False
            for _ in range(2):  # 重试 1 次
                try:
                    req = urllib.request.Request(target, method="HEAD",
                                                 headers={"User-Agent": "i18n-pipeline/1.0"})
                    with urlopen(req, timeout=LINK_TIMEOUT):
                        ok = True
                        break
                except Exception:
                    continue
            if not ok:
                warnings.append("外链不可达（仅警告）: %s" % target)
        elif target.startswith("#"):
            if not _anchor_ok(zh_text, target[1:]):
                warnings.append("锚点疑似缺失（仅警告）: %s" % target)
        elif target.startswith("mailto:"):
            continue
        else:
            p, _, anchor = target.partition("#")
            full = os.path.normpath(os.path.join(file_dir, p))
            if not os.path.isfile(full):
                errors.append("内链断裂: %s（%s 中）" % (target, file_path))
            elif anchor and os.path.isfile(full):
                try:
                    with open(full, encoding="utf-8") as f:
                        if not _anchor_ok(f.read(), anchor):
                            warnings.append("锚点疑似缺失（仅警告）: %s" % target)
                except OSError:
                    pass
    return errors, warnings


# ---------------------------------------------------------------------------
# 占位符检查（设计 §5.3，沿用 067 规则）
# ---------------------------------------------------------------------------
_PH_RE = re.compile(r"\{[^{}]+\}")


def check_placeholders(en_text, zh_text):
    from collections import Counter
    en_ph, zh_ph = Counter(_PH_RE.findall(en_text)), Counter(_PH_RE.findall(zh_text))
    if en_ph != zh_ph:
        return ["占位符不一致：英文 %s vs 中文 %s" % (sorted(en_ph.elements()),
                                                sorted(zh_ph.elements()))]
    return []


# ---------------------------------------------------------------------------
# zh.json 对照 diff（设计 §1.3）：不翻译，输出官方译法前后对照表
# ---------------------------------------------------------------------------
def zh_json_compare(path, sha, repo=UPSTREAM_DEFAULT):
    parent = fetch_upstream_parent_sha(sha, repo)
    old = json.loads(fetch_upstream(path, parent, repo))
    new = json.loads(fetch_upstream(path, sha, repo))
    rows = []
    for k in sorted(set(old) | set(new)):
        if old.get(k) != new.get(k):
            status = "新增" if k not in old else ("删除" if k not in new else "修改")
            rows.append((k, old.get(k, "—"), new.get(k, "—"), status))
    lines = ["# 官方中文包对照 diff（不翻译，仅供人工决定是否同步措辞）",
             "",
             "文件：`%s` ｜ commit `%s`（父 `%s`）" % (path, sha[:8], parent[:8]),
             "",
             "| key | 旧译法 | 新译法 | 变化 |",
             "|---|---|---|---|"]
    for k, o, n, s in rows:
        lines.append("| `%s` | %s | %s | %s |" % (k, o, n, s))
    if not rows:
        lines.append("| — | 无变化 | — | — |")
    return "\n".join(lines) + "\n", len(rows)


# ---------------------------------------------------------------------------
# 分块翻译
# ---------------------------------------------------------------------------
def chunk_text(text, max_chars=CHUNK_CHARS):
    blocks, cur, cur_len = [], [], 0
    for b in re.split(r"\n\s*\n", text):
        b = b.strip("\n")
        if not b:
            continue
        if cur_len + len(b) + 2 > max_chars and cur:
            blocks.append("\n\n".join(cur))
            cur, cur_len = [], 0
        cur.append(b)
        cur_len += len(b) + 2
    if cur:
        blocks.append("\n\n".join(cur))
    return blocks or [""]


def translate_document(en_text, ref_zh=None, terms=None,
                       gateway_url=None, model=None):
    """整篇文档分块翻译＋术语后处理。返回中文全文。"""
    terms = terms if terms is not None else TERMS
    ref = (ref_zh or "")[:REF_ZH_CHARS]
    chunks = chunk_text(en_text)
    out = []
    for ch in chunks:
        raw = gateway_translate(ch, ref_zh=ref if ref else None, terms=terms,
                                gateway_url=gateway_url, model=model)
        out.append(apply_terms(ch, raw, terms))
    return "\n\n".join(out)


# ---------------------------------------------------------------------------
# PR body 模板（设计 §1.2）
# ---------------------------------------------------------------------------
def render_pr_body(source, source_ref, items, model):
    lines = [
        "## [i18n] 翻译跟进：%s" % (source_ref or source),
        "",
        "> ⚠️ **机器初稿，需人工审校** —— 本 PR 由翻译流水线自动生成，合并前必须人工审校。",
        "",
        "**来源**：%s（%s）" % (source, source_ref or "—"),
        "**术语表版本**：%s（源头：%s）" % (TERMS_VERSION, TERMS_SOURCE),
        "**翻译模型**：%s" % model,
        "",
        "### 审校 checklist",
        "- [ ] 术语：25 条拍板术语译法无误（CI 已过，人工抽查流畅度）",
        "- [ ] 链接：内链有效（CI 已过）；外链警告已人工看过",
        "- [ ] 流畅度：通读一遍，无机器翻译腔、无漏段",
        "",
        "### 变更文件",
    ]
    for it in items:
        lines.append("- `%s`（%s，上游 %s）" % (it["path"], it["status"],
                                              it["upstream_sha"][:8]))
    return "\n".join(lines) + "\n"


def unified_diff(old_text, new_text, path):
    return "".join(difflib.unified_diff(
        old_text.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile="a/" + path, tofile="b/" + path))


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def run_pipeline(parsed, repo_root=".", out_dir="i18n-out", dry_run=False,
                 gateway_url=None, model=None, repo=UPSTREAM_DEFAULT,
                 translate_fn=None):
    """跑完全流程。任一环节失败即抛 PipelineError（不输出半成品）。"""
    translate_fn = translate_fn or translate_document
    mdl = model or os.environ.get("I18N_MODEL") or DEFAULT_MODEL
    results, all_errors, all_warnings = [], [], []
    outputs = {}  # path -> 新中文全文（先内存攒齐，最后统一写盘）

    for it in parsed["items"]:
        path, status, sha = it["path"], it["status"], it["upstream_sha"]
        if path == ZH_JSON_PATH:
            md, n = zh_json_compare(path, sha, repo)
            outputs[path + ".compare.md"] = md
            results.append({"path": path, "mode": "对照diff", "changes": n,
                            "errors": [], "warnings": []})
            continue
        en_text = fetch_upstream(path, sha, repo)
        old_zh = ""
        local = os.path.join(repo_root, path)
        if status == "modified" and os.path.isfile(local):
            with open(local, encoding="utf-8") as f:
                old_zh = f.read()
        new_zh = translate_fn(en_text, ref_zh=old_zh or None,
                              gateway_url=gateway_url, model=model)
        errors = [f["detail"] + "（行 %d）" % f["line"]
                  for f in self_check_terms(en_text, new_zh)]
        errors += check_placeholders(en_text, new_zh)
        link_err, link_warn = check_links(new_zh, path, repo_root)
        errors += link_err
        warnings = link_warn
        if errors:
            raise PipelineError("自检失败 %s：\n- %s" % (path, "\n- ".join(errors)))
        outputs[path] = new_zh
        results.append({"path": path, "mode": "翻译", "status": status,
                        "errors": [], "warnings": warnings,
                        "diff": unified_diff(old_zh, new_zh, path)})
        all_warnings += ["%s: %s" % (path, w) for w in warnings]

    pr_body = render_pr_body(parsed["source"], parsed["source_ref"],
                             parsed["items"], mdl)
    report = {"source": parsed["source"], "source_ref": parsed["source_ref"],
              "terms": TERMS_VERSION, "terms_source": TERMS_SOURCE,
              "model": mdl, "results": [
                  {k: v for k, v in r.items() if k != "diff"} for r in results],
              "warnings": all_warnings}

    if dry_run:
        print(pr_body)
        for r in results:
            if r.get("diff"):
                print(r["diff"])
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return report

    os.makedirs(out_dir, exist_ok=True)
    for p, content in outputs.items():
        fp = os.path.join(out_dir, p)
        os.makedirs(os.path.dirname(fp) or ".", exist_ok=True)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
    with open(os.path.join(out_dir, "PR-BODY.md"), "w", encoding="utf-8") as f:
        f.write(pr_body)
    with open(os.path.join(out_dir, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report


def load_terms_file(path, terms):
    """--terms-file：`英文=中文` 每行一条，覆盖同名术语（只改表不改代码）。"""
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            en, zh = line.split("=", 1)
            en, zh = en.strip(), zh.strip()
            for t in terms:
                if t["en"] == en:
                    t["zh"] = zh
                    break
            else:
                terms.append({"en": re.escape(en), "zh": zh, "wrongs": []})
    return terms


# ---------------------------------------------------------------------------
# 自测（无网络）
# ---------------------------------------------------------------------------
def cmd_self_test():
    passed, failed = 0, 0

    def check(name, cond, detail=""):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print("FAIL: %s %s" % (name, detail))

    # 1. 输入解析：removed/计划稿/test 排除，缺字段报错
    p = parse_input({"source": "weekly-report", "source_ref": "x", "items": [
        {"path": "README.md", "status": "modified", "upstream_sha": "a" * 40},
        {"path": "docs/a.md", "status": "removed", "upstream_sha": "b" * 40},
        {"path": "docs/plans/d.md", "status": "modified", "upstream_sha": "c" * 40},
        {"path": "x.test.md", "status": "added", "upstream_sha": "d" * 40}]})
    check("parse_input 排除", [i["path"] for i in p["items"]] == ["README.md"])
    try:
        parse_input({"items": [{"path": "a"}]})
        check("parse_input 缺字段报错", False)
    except PipelineError:
        check("parse_input 缺字段报错", True)

    # 2. 术语后处理：英文原形→拍板译法
    out = apply_terms("Contact your provider.", "联系你的 provider。")
    check("en→zh 替换", out == "联系你的 服务商。", repr(out))

    # 3. wrongs＋英文同现：provider（供应商）→ 服务商
    out = apply_terms("Set the provider.", "设置 provider（供应商）。")
    check("wrongs 同现替换", out == "设置 服务商。", repr(out))

    # 4. 孤立 wrongs 不动（防“走 PRD-029 流程”误伤）
    out = apply_terms("Follow the process.", "走 PRD-029 流程。")
    check("孤立 wrongs 不动", out == "走 PRD-029 流程。", repr(out))

    # 5. 代码保护
    out = apply_terms("Use provider.", "运行 `provider` 命令。")
    check("行内代码保护", "`provider`" in out, repr(out))
    out = apply_terms("Use provider.", "```\nprovider = 1\n```\n用 provider。")
    check("代码块保护", "provider = 1" in out and "用 服务商。" in out, repr(out))

    # 6. 自检：干净通过；残留英文失败
    check("自检干净", self_check_terms("Use provider.", "用服务商。") == [])
    fails = self_check_terms("Use provider.", "用 provider。")
    check("自检残留失败", len(fails) == 1 and fails[0]["expected"] == "服务商",
          repr(fails))

    # 7. 链接：内链断裂报错；存在通过
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        os.makedirs(os.path.join(td, "docs"))
        open(os.path.join(td, "docs", "a.md"), "w").write("x")
        e, w = check_links("[a](a.md)", "docs/b.md", td)
        check("内链存在", e == [] and w == [], repr((e, w)))
        e, w = check_links("[a](missing.md)", "docs/b.md", td)
        check("内链断裂报错", len(e) == 1, repr(e))

    # 8. 外链只警告（mock 不可达）
    import unittest.mock as mock
    with mock.patch("urllib.request.urlopen", side_effect=Exception("down")):
        e, w = check_links("[a](https://example.invalid/x)", "docs/b.md", ".",
                           urlopen=urllib.request.urlopen)
    check("外链只警告", e == [] and len(w) == 1, repr((e, w)))

    # 9. 占位符
    check("占位符一致", check_placeholders("Hi {name}", "你好 {name}") == [])
    check("占位符不一致报错",
          len(check_placeholders("Hi {name}", "你好")) == 1)

    # 10. 术语表 25 条
    check("术语表 25 条", len(TERMS) == 25, "实际 %d（源头 %s）"
          % (len(TERMS), TERMS_SOURCE))

    # 11. 网关 key 缺失报错（不碰网络）
    os.environ.pop("I18N_GATEWAY_API_KEY", None)
    try:
        gateway_translate("hi")
        check("缺 key 报错", False)
    except GatewayError as ex:
        check("缺 key 报错", "I18N_GATEWAY_API_KEY" in str(ex), str(ex)[:60])

    # 12. PR body 含四要素
    body = render_pr_body("weekly-report", "《上游周报》#1",
                          [{"path": "README.md", "status": "modified",
                            "upstream_sha": "a" * 40}], "m")
    check("PR body 四要素", all(s in body for s in
          ["机器初稿，需人工审校", "《上游周报》#1", "审校 checklist",
           "术语表版本"]), body[:120])

    # 13. zh.json 对照：合成 dict 走纯逻辑
    old, new = {"a": "旧", "b": "同"}, {"a": "新", "c": "增"}
    rows = [(k, old.get(k, "—"), new.get(k, "—"),
             "新增" if k not in old else ("删除" if k not in new else "修改"))
            for k in sorted(set(old) | set(new)) if old.get(k) != new.get(k)]
    check("对照 diff 行", [(r[0], r[3]) for r in rows] ==
          [("a", "修改"), ("b", "删除"), ("c", "新增")], repr(rows))

    print("自测：%d 通过，%d 失败（术语表源头：%s）" % (passed, failed, TERMS_SOURCE))
    return 1 if failed else 0


I18N_PR_HELP = """
[i18n] PR 规范（设计 §1.2，流水线产出统一走这套）：
  分支：i18n/YYYYMMDD-<slug>（如 i18n/20261019-readme-update），从 main 拉出
  标题：[i18n] 前缀（如 “[i18n] README.md 跟进上游 a79f7c47”）
  Body 必含：① 来源（周报 issue 链接/手动触发说明）② “机器初稿，需人工审校”声明
             ③ 审校 checklist（三项）④ 术语表版本
  人工闸门：合并前维护者必须审校；CI 术语锁定失败阻断；建议分支保护要求 1 个 approve
"""


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="PRD-084/T2 翻译流水线：哨兵 needs_translation → 中文翻译 diff（初稿）",
        epilog=I18N_PR_HELP)
    ap.add_argument("--input", help="哨兵清单 JSON 文件")
    ap.add_argument("--repo-root", default=".", help="本地仓库根（默认 .)")
    ap.add_argument("--out-dir", default="i18n-out", help="产出目录（默认 ./i18n-out)")
    ap.add_argument("--dry-run", action="store_true", help="跑完全流程但不写文件")
    ap.add_argument("--self-test", action="store_true", help="内置自测（无网络）")
    ap.add_argument("--gateway-url", help="覆盖网关地址")
    ap.add_argument("--model", help="覆盖模型")
    ap.add_argument("--terms-file", help="术语表覆盖文件（`英文=中文` 每行一条）")
    ap.add_argument("--upstream-repo", default=UPSTREAM_DEFAULT)
    args = ap.parse_args(argv)

    global TERMS, TERMS_SOURCE
    if args.terms_file:
        TERMS = load_terms_file(args.terms_file, [dict(t, wrongs=list(t["wrongs"]))
                                                  for t in TERMS])
        TERMS_SOURCE += " + " + args.terms_file

    if args.self_test:
        return cmd_self_test()
    if not args.input:
        ap.error("--input 必填（或用 --self-test）")
    with open(args.input, encoding="utf-8") as f:
        parsed = parse_input(json.load(f))
    if not parsed["items"]:
        print("输入为空（全部被排除），无事可做。")
        return 0
    try:
        run_pipeline(parsed, repo_root=args.repo_root, out_dir=args.out_dir,
                     dry_run=args.dry_run, gateway_url=args.gateway_url,
                     model=args.model, repo=args.upstream_repo)
    except PipelineError as e:
        print("失败：%s" % e, file=sys.stderr)
        return 1
    print("完成：%d 个文件（术语表：%s）" % (len(parsed["items"]), TERMS_SOURCE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
