#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRD-067/T2：中文提示词质量门测试套件（纯标准库）

规则依据：docs/plans/2026-10-18-quality-gate-cases.md §3
前提（已拍板）：方案 A（继续自维护）；术语表 25 条（用户 2026-10-18 已拍板）。

三类检查（函数均可独立调用）：
  check_missing(upstream_items, local_files) -> (failures, warnings)
      漏翻检查（方案 A 口径）：文件路径锚点 + ±20 行窗口 + 英文原样残留启发式。
      upstream_items: [{"path": "surfaces/gui/src/X.tsx", "line": 42,
                        "literal": "Delete item"}]   # 上游新增的英文字符串
      local_files:    {"surfaces/gui/src/X.tsx": ["line1", ...]}  # 行号 1-based
  check_terms(files, terms=TERMS) -> [failure]
      术语一致性：同一英文术语的中文译法在单文件内必须唯一；英文术语混入中文
      字符串字面量视为未译；大小写/单复数归一；品牌词豁免。
      files: {"path": "全文文本"}
  check_placeholders(templates) -> [failure]
      模板完整性：templates=[{"name":..,"zh":"..","en":".."}]；
      占位符集合必须一致；拼写相近的缺失/多余判为"拼写错误"；
      JSX 花括号是 JS 表达式不是文案占位符，不纳入（调用方不喂 JSX 表达式）。
  check_keys(en_json_text, zh_json_text) -> [failure]
      方案 B 口径（备用）：en.json 的 key 在 zh.json 必须存在、非空、与英文不同。

失败项格式：{"check":..., "file":..., "line":..., "expected":..., "detail":...}

CLI:
  --self-test            内置正反用例自测（证明三类检查都能 work，含"测试能 fail"验证）
  --root DIR             扫描真实仓库（术语一致性）
  --upstream JSON        追加漏翻检查（JSON 文件：上游新增英文串列表）
  --templates JSON       追加模板检查（JSON 文件：[{name,zh,en}]）
  --scheme A|B           方案开关（默认 A；B 需 --en-json/--zh-json）
  --terms-file PATH      术语表覆盖文件（`英文=中文` 每行一条；T1 说 terms.yaml，
                         标准库无 yaml 解析器，等价目标是"只改表不改代码"）
"""

import argparse
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# 术语表（T1 §4，用户 2026-10-18 已拍板；T2 按此表实现）
# en: 英文术语（正则片段，大小写/单复数归一）；zh: 中文；
# wrongs: 已知错误译法（来自表内"勿用"备注），出现即失败。
# 注：thread 的备选"串"是单字，会误伤"字符串"等，故不做独立候选，仅文档说明。
# ---------------------------------------------------------------------------
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

# 品牌专有名词：保持英文原样不算错（T1 §3.1 豁免、§3.2 规则 4）
BRAND_WORDS = ("OpenWorker", "GitHub", "GitLab", "Slack", "macOS", "Windows",
               "Linux", "iOS", "Android", "Tauri")

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
# 字符串字面量："..." / '...' / `...`（转义引号做最小处理）
LITERAL_RE = re.compile(r'''"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)'|`((?:[^`\\]|\\.)*)`''')
WINDOW = 20  # 漏翻检查 ±20 行窗口（T1 §3.1）


def has_cjk(s):
    return bool(CJK_RE.search(s))


def is_ascii(s):
    try:
        s.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def extract_literals(line):
    """抽取一行里的字符串字面量内容（去引号）。"""
    out = []
    for m in LITERAL_RE.finditer(line):
        for g in m.groups():
            if g is not None:
                out.append(g)
                break
    return out


def extract_english_literals(text):
    """T1 §3.1：抽取引号包裹的纯 ASCII 文本（长度≥3），作为"上游新增英文串"候选。"""
    found = []
    for i, line in enumerate(text.splitlines(), 1):
        for lit in extract_literals(line):
            s = lit.strip()
            if len(s) >= 3 and is_ascii(s) and re.search(r"[A-Za-z]", s):
                found.append({"line": i, "literal": s})
    return found


def is_exempt_literal(literal):
    """T1 §3.1 豁免：品牌专有名词 / URL / 纯数字与格式串 / 纯占位符，不算漏翻。"""
    low = literal.lower()
    if any(b.lower() in low for b in BRAND_WORDS):
        return True
    if "http://" in low or "https://" in low or low.startswith("www."):
        return True
    tmp = re.sub(r"\{[^{}]*\}", "", literal)          # {count} 类占位符
    tmp = re.sub(r"%(\(\w+\))?[sd]", "", tmp)          # %d / %s / %(name)s
    tmp = re.sub(r"[\s\d._\-/,;:!?'\"()\[\]%@$*+=<>|~^&#]+", "", tmp)
    if not tmp:
        return True
    return False


def levenshtein(a, b):
    """小编辑距离（占位符拼写检查用）。"""
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1,
                           prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


# 占位符三种风格（T1 §3.3）：{name} / %(name)s、%s / {{name}}
PLACEHOLDER_RES = [
    re.compile(r"\{\{(\w+)\}\}"),        # 双花括号（先匹配，避免被单花括号吃掉）
    re.compile(r"(?<!\{)\{([A-Za-z_]\w*)\}(?!\})"),  # 单花括号
    re.compile(r"%(\(\w+\))?[sd]"),      # printf 风格
]


def extract_placeholders(text):
    """返回占位符 multiset（Counter 字典），printf 按原文区分 %s/%d。"""
    counts = {}
    tmp = text
    for rx in PLACEHOLDER_RES:
        for m in rx.finditer(tmp):
            key = m.group(0)
            if rx is PLACEHOLDER_RES[1]:
                key = "{" + m.group(1) + "}"
            counts[key] = counts.get(key, 0) + 1
        tmp = rx.sub("", tmp)
    return counts

# ---------------------------------------------------------------------------
# 检查 1：漏翻检查（方案 A 口径，T1 §3.1）
# ---------------------------------------------------------------------------
def check_missing(upstream_items, local_files):
    """upstream_items: [{"path","line","literal"}]；local_files: {path: [行]}。
    返回 (failures, warnings)。"""
    failures, warnings = [], []
    for item in upstream_items:
        path, line, literal = item["path"], item["line"], item["literal"]
        if is_exempt_literal(literal):
            continue
        if path not in local_files:
            failures.append({"check": "漏翻检查", "file": path, "line": line,
                             "expected": "新建对应文件并翻译",
                             "detail": "上游新增英文串所在文件在汉化版缺失：%r" % literal})
            continue
        lines = local_files[path]
        anchor = line - 1
        if 0 <= anchor < len(lines):
            lo, hi = max(0, anchor - WINDOW), min(len(lines), anchor + WINDOW + 1)
            window = list(zip(range(lo + 1, hi + 1), lines[lo:hi]))
        else:  # 锚点越界：退化为全文件搜索，并如实注明
            window = list(enumerate(lines, 1))
            warnings.append({"check": "漏翻检查", "file": path, "line": line,
                             "detail": "锚点行 %d 超出文件范围，已退化为全文件搜索" % line})
        residual = None
        for lineno, text in window:
            for lit in extract_literals(text):
                if lit.strip() == literal:
                    residual = (lineno, text.strip())
                    break
            if residual:
                break
        if residual:
            lineno, _ = residual
            failures.append({"check": "漏翻检查", "file": path, "line": lineno,
                             "expected": "中文翻译",
                             "detail": "英文原样残留（疑似漏翻）：%r" % literal})
        elif not any(has_cjk(t) for _, t in window):
            warnings.append({"check": "漏翻检查", "file": path, "line": line,
                             "detail": "窗口内无中文覆盖且无英文残留，待人工确认：%r" % literal})
        # else: 窗口内有中文覆盖 → 视为已翻
    return failures, warnings


# ---------------------------------------------------------------------------
# 检查 2：术语一致性（T1 §3.2）
# ---------------------------------------------------------------------------
def _en_in_cjk_literals(text, terms):
    """中文字符串字面量里混入的英文术语：[(行号, 英文匹配, 字面量)]。"""
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        for lit in extract_literals(line):
            if not has_cjk(lit):
                continue
            for t in terms:
                m = re.search(r"\b" + t["en"] + r"\b", lit, re.IGNORECASE)
                if m and t["zh"] not in lit:
                    hits.append((i, m.group(0), lit.strip()))
    return hits


def check_terms(files, terms=TERMS):
    """files: {path: 全文}。返回 [failure]。"""
    failures = []
    compiled = [(t, re.compile(t["en"], re.IGNORECASE)) for t in terms]
    for path, text in files.items():
        for t, rx in compiled:
            found_zh = t["zh"] in text
            found_wrongs = [w for w in t["wrongs"] if w in text]
            if found_zh and found_wrongs:
                lineno = next(i for i, l in enumerate(text.splitlines(), 1)
                              if any(w in l for w in found_wrongs))
                failures.append({"check": "术语一致性", "file": path, "line": lineno,
                                 "expected": t["zh"],
                                 "detail": "同一文件出现两种译法：%r 与 %r" %
                                           (t["zh"], "/".join(found_wrongs))})
            elif not found_zh and found_wrongs:
                lineno = next(i for i, l in enumerate(text.splitlines(), 1)
                              if any(w in l for w in found_wrongs))
                failures.append({"check": "术语一致性", "file": path, "line": lineno,
                                 "expected": t["zh"],
                                 "detail": "错误译法 %r，应为 %r" %
                                           ("/".join(found_wrongs), t["zh"])})
            # 英文术语混入中文字符串 → 未译（T1 §3.3：同时触发 3.2）
            # 注：品牌词不在 TERMS 里，不会误伤；代码/注释里的英文不含中文，不进字面量分支
        for lineno, matched, lit in _en_in_cjk_literals(text, terms):
            # 同一字面量里已有任一术语的中文译法则跳过（避免"OpenWorker 智能体"这类误报）
            if any(tt["zh"] in lit for tt in terms):
                continue
            zh = next(t["zh"] for t in terms
                      if re.search(r"\b" + t["en"] + r"\b", matched, re.IGNORECASE))
            failures.append({"check": "术语一致性", "file": path, "line": lineno,
                             "expected": zh,
                             "detail": "英文术语 %r 混入中文字符串未译：%r" % (matched, lit)})
    return failures


# ---------------------------------------------------------------------------
# 检查 3：模板完整性（T1 §3.3）
# ---------------------------------------------------------------------------
def check_placeholders(templates):
    """templates: [{"name","zh","en"}]。返回 [failure]。
    规则 1：占位符集合必须一致；规则 2：拼写相近的缺失/多余判"拼写错误"；
    JSX 花括号不纳入（调用方不喂 JSX 表达式）。"""
    failures = []
    for tpl in templates:
        name, zh, en = tpl["name"], tpl["zh"], tpl["en"]
        zh_ph, en_ph = extract_placeholders(zh), extract_placeholders(en)
        if zh_ph == en_ph:
            continue
        # 规则 2：拼写错误优先判定（编辑距离≤2 的缺失/多余配对）
        zh_only = [k for k in zh_ph if zh_ph[k] > en_ph.get(k, 0)]
        en_only = [k for k in en_ph if en_ph[k] > zh_ph.get(k, 0)]
        spelling = []
        for z in list(zh_only):
            for e in list(en_only):
                zn = z.strip("{}%()s d").strip("()")
                en_ = e.strip("{}%()s d").strip("()")
                if zn and en_ and zn != en_ and levenshtein(zn, en_) <= 2:
                    spelling.append((e, z))
                    zh_only.remove(z)
                    en_only.remove(e)
                    break
        for e, z in spelling:
            failures.append({"check": "模板完整性", "file": name, "line": 0,
                             "expected": e,
                             "detail": "占位符拼写错误：%r 应为 %r（运行时直接报错）" % (z, e)})
        if zh_only or en_only:
            failures.append({"check": "模板完整性", "file": name, "line": 0,
                             "expected": "与英文原文占位符集合一致",
                             "detail": "占位符集合不一致：中文多 %s；中文缺 %s" %
                                       (zh_only or "无", en_only or "无")})
    return failures


# ---------------------------------------------------------------------------
# 方案 B 口径（备用，T1 §3.1）：en.json key 精确对齐
# ---------------------------------------------------------------------------
def _flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        key = "%s.%s" % (prefix, k) if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        else:
            out[key] = v
    return out


def check_keys(en_json_text, zh_json_text):
    """en.json 的 key 在 zh.json 必须存在、非空、与英文不同。"""
    failures = []
    en = _flatten(json.loads(en_json_text))
    zh = _flatten(json.loads(zh_json_text))
    for key, en_val in en.items():
        if key not in zh:
            failures.append({"check": "漏翻检查(方案B)", "file": "zh.json",
                             "line": 0, "expected": "存在 key %r" % key,
                             "detail": "key 缺失"})
        elif not str(zh[key]).strip():
            failures.append({"check": "漏翻检查(方案B)", "file": "zh.json",
                             "line": 0, "expected": "非空翻译",
                             "detail": "key %r 值为空" % key})
        elif str(zh[key]).strip() == str(en_val).strip():
            failures.append({"check": "漏翻检查(方案B)", "file": "zh.json",
                             "line": 0, "expected": "中文翻译",
                             "detail": "key %r 英文原样残留" % key})
    return failures


# ---------------------------------------------------------------------------
# 文件收集（T1 §3.2 扫描范围）
# ---------------------------------------------------------------------------
def collect_files(root):
    """返回 {相对路径: 全文}。
    范围：surfaces/gui/src/**/*.tsx|ts（不含 *test*）+ docs/**/*.md（不含 docs/plans/）；
    coworker/ 暂不纳入（ops.md 未汉化，T4 基线时复核）。"""
    files = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if rel.startswith("surfaces/gui/src/") and rel.endswith((".tsx", ".ts")):
                if "test" in fn.lower():
                    continue
            elif rel.startswith("docs/") and rel.endswith(".md"):
                if rel.startswith("docs/plans/"):
                    continue
            else:
                continue
            try:
                with open(full, encoding="utf-8") as f:
                    files[rel] = f.read()
            except (OSError, UnicodeDecodeError):
                continue
    return files


def load_terms_file(path):
    """`英文=中文` 每行一条：覆盖/新增术语（T1 §5"只改表不改代码"的等价实现）。"""
    terms = list(TERMS)
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            en, zh = line.split("=", 1)
            en, zh = en.strip(), zh.strip()
            terms = [t for t in terms if t["en"] != re.escape(en)]
            terms.append({"en": re.escape(en), "zh": zh, "wrongs": []})
    return terms

# ---------------------------------------------------------------------------
# 自测：正反用例（"测试能 fail"验证——故意写错时必须报出）
# ---------------------------------------------------------------------------
def _lines(text):
    return text.splitlines()


SELF_TESTS = [
    # ---- 漏翻检查 ----
    {"name": "漏翻/检出英文原样残留",
     "fn": lambda: check_missing(
         [{"path": "a.tsx", "line": 10, "literal": "Delete item"}],
         {"a.tsx": _lines('import x from "y";\n' * 9 + 'const t = "Delete item"; // 未翻\n')}),
     "expect_fail": True},
    {"name": "漏翻/窗口内有中文视为已翻",
     "fn": lambda: check_missing(
         [{"path": "a.tsx", "line": 10, "literal": "Delete item"}],
         {"a.tsx": _lines('import x from "y";\n' * 9 + 'const t = "删除条目";\n')}),
     "expect_fail": False},
    {"name": "漏翻/品牌词豁免",
     "fn": lambda: check_missing(
         [{"path": "a.tsx", "line": 3, "literal": "OpenWorker Cloud"}],
         {"a.tsx": _lines('x\n' * 2 + 'const t = "OpenWorker Cloud";\n')}),
     "expect_fail": False},
    {"name": "漏翻/对应文件缺失",
     "fn": lambda: check_missing(
         [{"path": "new/File.tsx", "line": 1, "literal": "New feature"}],
         {"a.tsx": _lines("x\n")}),
     "expect_fail": True},
    {"name": "漏翻/纯格式串豁免",
     "fn": lambda: check_missing(
         [{"path": "a.tsx", "line": 2, "literal": "{count}"}],
         {"a.tsx": _lines('x\nconst t = "{count}";\n')}),
     "expect_fail": False},
    # ---- 术语一致性 ----
    {"name": "术语/同一文件两种译法",
     "fn": lambda: check_terms(
         {"a.tsx": 'const a = "智能体列表";\nconst b = "代理设置";\n'}),
     "expect_fail": True},
    {"name": "术语/纯错误译法",
     "fn": lambda: check_terms(
         {"a.tsx": 'const b = "代理设置";\n'}),
     "expect_fail": True},
    {"name": "术语/译法一致通过",
     "fn": lambda: check_terms(
         {"a.tsx": 'const a = "智能体列表";\nconst b = "智能体详情";\n'}),
     "expect_fail": False},
    {"name": "术语/英文混入中文字符串",
     "fn": lambda: check_terms(
         {"humanize.ts": 'export const t = { pre: "添加 Skill ", post: " 到你的 Skills" };\n'}),
     "expect_fail": True},
    {"name": "术语/代码里的英文不算",
     "fn": lambda: check_terms(
         {"a.ts": "import { Skill } from './skill';\nconst s = new Skill();\n"}),
     "expect_fail": False},
    {"name": "术语/品牌词豁免",
     "fn": lambda: check_terms(
         {"a.tsx": 'const t = "OpenWorker Cloud 登录";\n'}),
     "expect_fail": False},
    {"name": "术语/备选译法被拒",
     "fn": lambda: check_terms(
         {"a.tsx": 'const p = "供应商列表";\n'}),
     "expect_fail": True},
    # ---- 模板完整性 ----
    {"name": "模板/占位符一致通过",
     "fn": lambda: check_placeholders(
         [{"name": "t1", "zh": "已收到 {input}，正在处理", "en": "Received {input}, processing"}]),
     "expect_fail": False},
    {"name": "模板/漏占位符",
     "fn": lambda: check_placeholders(
         [{"name": "t2", "zh": "处理完成", "en": "Done {output}"}]),
     "expect_fail": True},
    {"name": "模板/占位符拼写错误",
     "fn": lambda: check_placeholders(
         [{"name": "t3", "zh": "输入 {imput}", "en": "Input {input}"}]),
     "expect_fail": True},
    {"name": "模板/printf 风格一致",
     "fn": lambda: check_placeholders(
         [{"name": "t4", "zh": "共 %d 项", "en": "%d items"}]),
     "expect_fail": False},
    {"name": "模板/printf 类型不同",
     "fn": lambda: check_placeholders(
         [{"name": "t5", "zh": "共 %s 项", "en": "%d items"}]),
     "expect_fail": True},
    {"name": "模板/双花括号一致",
     "fn": lambda: check_placeholders(
         [{"name": "t6", "zh": "{{name}} 你好", "en": "Hello {{name}}"}]),
     "expect_fail": False},
    # ---- 方案 B 口径 ----
    {"name": "方案B/英文原样残留",
     "fn": lambda: check_keys('{"a": "Hello", "b": "World"}',
                               '{"a": "你好", "b": "World"}'),
     "expect_fail": True},
    {"name": "方案B/全部通过",
     "fn": lambda: check_keys('{"a": "Hello"}', '{"a": "你好"}'),
     "expect_fail": False},
]


def run_self_test():
    """跑内置正反用例；任一用例的实际结果与预期不符则整体失败。"""
    passed, failed = 0, []
    for t in SELF_TESTS:
        try:
            result = t["fn"]()
            got_fail = bool(result[0]) if isinstance(result, tuple) else bool(result)
        except Exception as e:  # noqa: BLE001 — 自测本身抛错也算失败
            print("FAIL  %s：自测抛错 %r" % (t["name"], e))
            failed.append(t["name"])
            continue
        if got_fail == t["expect_fail"]:
            print("ok    %s（预期%s，实际%s）" %
                  (t["name"], "失败" if t["expect_fail"] else "通过",
                   "失败" if got_fail else "通过"))
            passed += 1
        else:
            print("FAIL  %s：预期%s，实际%s" %
                  (t["name"], "失败" if t["expect_fail"] else "通过",
                   "失败" if got_fail else "通过"))
            failed.append(t["name"])
    print("自测：%d 通过 / %d 失败（共 %d 项）" % (passed, len(failed), len(SELF_TESTS)))
    return failed


def fmt(f):
    loc = "%s:%s" % (f["file"], f["line"]) if f.get("line") else f["file"]
    return "[%s] %s\n  期望：%s\n  说明：%s" % (f["check"], loc, f["expected"], f["detail"])


def main(argv=None):
    ap = argparse.ArgumentParser(description="PRD-067/T2 中文提示词质量门（纯标准库）")
    ap.add_argument("--self-test", action="store_true", help="内置正反用例自测")
    ap.add_argument("--root", help="扫描真实仓库根目录（术语一致性）")
    ap.add_argument("--upstream", help="上游新增英文串 JSON 文件（含漏翻检查）")
    ap.add_argument("--templates", help="模板 JSON 文件 [{name,zh,en}]（含模板检查）")
    ap.add_argument("--scheme", choices=("A", "B"), default="A", help="方案开关（默认 A）")
    ap.add_argument("--en-json", help="方案 B：上游 en.json")
    ap.add_argument("--zh-json", help="方案 B：汉化版 zh.json")
    ap.add_argument("--terms-file", help="术语表覆盖文件（`英文=中文` 每行一条）")
    args = ap.parse_args(argv)

    if args.self_test:
        failed = run_self_test()
        return 1 if failed else 0

    terms = load_terms_file(args.terms_file) if args.terms_file else TERMS
    failures, warnings = [], []

    if args.root:
        files = collect_files(args.root)
        print("扫描文件 %d 个" % len(files), file=sys.stderr)
        failures += check_terms(files, terms)

    if args.upstream:
        with open(args.upstream, encoding="utf-8") as f:
            items = json.load(f)
        local = {}
        if args.root:
            for p, text in collect_files(args.root).items():
                local[p] = text.splitlines()
        f2, w = check_missing(items, local)
        failures += f2
        warnings += w

    if args.templates:
        with open(args.templates, encoding="utf-8") as f:
            failures += check_placeholders(json.load(f))

    if args.scheme == "B":
        if not (args.en_json and args.zh_json):
            print("方案 B 需要 --en-json 和 --zh-json", file=sys.stderr)
            return 2
        with open(args.en_json, encoding="utf-8") as f:
            en_t = f.read()
        with open(args.zh_json, encoding="utf-8") as f:
            zh_t = f.read()
        failures += check_keys(en_t, zh_t)

    for w in warnings:
        print("警告：[%s] %s:%s %s" % (w["check"], w["file"], w.get("line"), w["detail"]))
    for f in failures:
        print(fmt(f))
    print("质量门：%d 失败 / %d 警告" % (len(failures), len(warnings)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
