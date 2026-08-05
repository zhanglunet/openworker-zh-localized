#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A2：spec.json / CLI 层的对抗用例（路径穿越、类型混淆、恶意配置）。

每条用例都真的去调 `excel_ai.py` 子命令。合格标准（三条全中才算过）：
  1. 退出码非零
  2. stderr 里有中文 `[错误]` 前缀
  3. **绝不出现 Traceback**
另有一类是"应当成功但结果必须正确"的用例，单独判。
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SCRIPT = os.path.join(ROOT, "scripts", "excel_ai.py")
BASE_SPEC = os.path.join(ROOT, "manual", "spec.json")
WORK = os.path.join(HERE, "_work_a2")

RESULTS = []


def base_spec():
    with open(BASE_SPEC, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def run(args, wall=120):
    try:
        p = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, timeout=wall)
    except subprocess.TimeoutExpired:
        return -999, "", "墙钟 %ds 超时" % wall
    return (p.returncode,
            p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def write_spec(name, spec):
    p = os.path.join(WORK, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)
    return p


def expect_clean_error(title, args, note=""):
    """期望：非零退出 + 中文 [错误] + 无 traceback。"""
    rc, out, err = run(args)
    tb = "Traceback" in err
    zh = "[错误]" in err or "[错误]" in out
    ok = (rc != 0) and zh and not tb
    detail = []
    if rc == 0:
        detail.append("退出码 0（静默通过！）")
    if tb:
        last = [l for l in err.strip().splitlines() if l.strip()][-1:]
        detail.append("出现 Traceback → %s" % (last[0][:100] if last else ""))
    if not zh and rc != 0:
        detail.append("退出码非零但没有中文 [错误] 提示")
    RESULTS.append((ok, title, "；".join(detail) or "干净的中文报错", note))
    print("  [%s] %-38s %s" % ("PASS" if ok else "FAIL", title, "；".join(detail) or "OK"))
    return ok


def expect_success(title, args, checker=None, note=""):
    rc, out, err = run(args)
    tb = "Traceback" in err
    detail = []
    if rc != 0:
        detail.append("退出码 %d" % rc)
    if tb:
        detail.append("出现 Traceback")
    ok = (rc == 0) and not tb
    if ok and checker:
        msg = checker(out, err)
        if msg:
            ok = False
            detail.append(msg)
    RESULTS.append((ok, title, "；".join(detail) or "正常完成", note))
    print("  [%s] %-38s %s" % ("PASS" if ok else "FAIL", title, "；".join(detail) or "OK"))
    return ok


def main():
    if os.path.isdir(WORK):
        shutil.rmtree(WORK)
    os.makedirs(WORK)
    out3 = os.path.join(WORK, "out_verify")

    print("=" * 96)
    print("A2-1 路径穿越 / 非法 workbook")
    print("=" * 96)
    for title, wb in [
        ("workbook=/etc/passwd（绝对路径穿越）", "/etc/passwd"),
        ("workbook=相对路径穿越到 /etc/passwd", "../../../../../../../etc/passwd"),
        ("workbook=/etc/shadow（无权限）", "/etc/shadow"),
        ("workbook 指向目录", "/etc"),
        ("workbook=/dev/null", "/dev/null"),
        ("workbook 不存在", "/nonexistent/nope.xlsx"),
        ("workbook 是 .xls 旧格式", "/etc/passwd.xls"),
        ("workbook 为空字符串", ""),
        ("workbook 是数字", 12345),
        ("workbook 是列表", ["/etc/passwd"]),
    ]:
        s = base_spec()
        s["workbook"] = wb
        expect_clean_error(title, ["verify", write_spec("wb.json", s), "-o", out3])

    print()
    print("=" * 96)
    print("A2-2 cross_checks 的 workbook 路径穿越")
    print("=" * 96)
    s = base_spec()
    s["cross_checks"] = [{"name": "穿越", "workbook": "/etc/passwd", "sheet": "x",
                          "header_rows": 1, "key": "工号", "left_key": "ID",
                          "compare": [{"left": "A", "right": "工号"}]}]
    expect_clean_error("cross_checks.workbook=/etc/passwd",
                       ["verify", write_spec("cc.json", s), "-o", out3])

    print()
    print("=" * 96)
    print("A2-3 spec 字段类型混淆（JSON 里塞错类型）")
    print("=" * 96)
    cases = [
        ("header_rows='abc'",        lambda s: s.update(header_rows="abc")),
        ("header_rows=-1",           lambda s: s.update(header_rows=-1)),
        ("header_rows=3.7",          lambda s: s.update(header_rows=3.7)),
        ("header_rows=null",         lambda s: s.update(header_rows=None)),
        ("header_rows 是列表",        lambda s: s.update(header_rows=[4])),
        ("sheet 不存在",              lambda s: s.update(sheet="不存在的表")),
        ("sheet 是数字",              lambda s: s.update(sheet=3)),
        ("keys 是列表不是对象",        lambda s: s.update(keys=["ID"])),
        ("dimensions 是字符串",       lambda s: s.update(dimensions="DEPT")),
        ("fields 是列表",             lambda s: s.update(fields=["A"])),
        ("derived 是列表",            lambda s: s.update(derived=["A+1"])),
        ("checks 是对象不是列表",      lambda s: s.update(checks={"name": "x"})),
        ("checks 元素是字符串",        lambda s: s.update(checks=["A+B"])),
        ("skip_when 是列表",          lambda s: s.update(skip_when=["ID"])),
        ("cross_checks 是对象",       lambda s: s.update(cross_checks={"a": 1})),
        ("整个 spec 是列表",           None),
    ]
    for title, mut in cases:
        if mut is None:
            p = os.path.join(WORK, "list.json")
            with open(p, "w", encoding="utf-8") as f:
                f.write('[1,2,3]')
        else:
            s = base_spec()
            mut(s)
            p = write_spec("mut.json", s)
        expect_clean_error(title, ["verify", p, "-o", out3])

    print()
    print("=" * 96)
    print("A2-4 checks / tolerance 恶意取值")
    print("=" * 96)
    tol_cases = [
        ("tolerance='abc'", "abc"),
        ("tolerance 是列表", [0.01]),
        ("tolerance=nan 字符串", "nan"),
        ("tolerance 为负数", -1),
    ]
    for title, tol in tol_cases:
        s = base_spec()
        s["checks"] = [{"name": "T", "target": "G_x", "expr": "A+D", "tolerance": tol}]
        expect_clean_error(title, ["verify", write_spec("tol.json", s), "-o", out3])

    # 以下三条是**有意的宽容设计**，正确行为就是成功而不是报错，单独按"应当成功"判：
    #   skip_when.empty / fill_merged 允许写单个字符串（否则 list("合计") 会被
    #   拆成 ['合','计']，误伤面极大）；tolerance:null 表示"用默认值 0.01"。
    s = base_spec()
    s["skip_when"] = {"empty": "ID", "label_in": "合计"}
    expect_success("宽容：skip_when 写单个字符串", ["verify", write_spec("lenient1.json", s), "-o", out3])
    s = base_spec()
    s["fill_merged"] = "DEPT"
    expect_success("宽容：fill_merged 写单个字符串", ["verify", write_spec("lenient2.json", s), "-o", out3])
    s = base_spec()
    s["checks"] = [{"name": "T", "target": "G_x", "expr": "A+D", "tolerance": None}]
    expect_success("宽容：tolerance=null 用默认值", ["verify", write_spec("lenient3.json", s), "-o", out3])

    # target 指向文本列 —— 读代码时发现：env[target] 是 str，float(str) 直接 ValueError
    s = base_spec()
    s["checks"] = [{"name": "把姓名当结果列", "target": "NAME", "expr": "A+D", "tolerance": 0.01}]
    expect_clean_error("checks.target 指向文本键列(NAME)",
                       ["verify", write_spec("tgt.json", s), "-o", out3],
                       note="env[target] 是字符串，float() 会炸")

    s = base_spec()
    s["checks"] = [{"name": "把部门当结果列", "target": "DEPT", "expr": "A+D", "tolerance": 0.01}]
    expect_clean_error("checks.target 指向文本维度列(DEPT)",
                       ["verify", write_spec("tgt2.json", s), "-o", out3])

    # 表达式里塞 DoS
    for title, expr in [
        ("check.expr 嵌套幂 DoS 3 层", "((10**999)**999)**999"),
        ("check.expr 字符串重复 DoS", "A + 0 * int(float('1' * 3) * 0) + sum([0] * 100000000)"),
        ("check.expr 列表拼接 DoS", "sum([[1]] * 300000, [])"),
        ("check.expr 序列复制 DoS", "A + 0 * len_of('a' * 1000000000)".replace("len_of", "float")),
        ("check.expr 深度嵌套 6 万层", "1+" * 60000 + "1"),
        ("derived 里塞 DoS", None),
    ]:
        s = base_spec()
        if title.startswith("derived"):
            s["derived"] = {"X": "((10**999)**999)**999"}
            s["checks"] = [{"name": "T", "target": "G_x", "expr": "X", "tolerance": 0.01}]
        else:
            s["checks"] = [{"name": "T", "target": "G_x", "expr": expr, "tolerance": 0.01}]
        expect_clean_error(title, ["verify", write_spec("dos.json", s), "-o", out3])

    print()
    print("=" * 96)
    print("A2-5 analyze / output 的字段类型混淆")
    print("=" * 96)
    # 先跑一次正常 verify 拿到 detail
    ok = expect_success("基线 verify（后续 analyze 用）",
                        ["verify", BASE_SPEC, "-o", out3])
    detail = os.path.join(out3, "verification_detail.csv")
    if not ok or not os.path.isfile(detail):
        print("  !! 基线 verify 失败，跳过 analyze 系列")
    else:
        outa = os.path.join(WORK, "out_analyze")
        acases = [
            ("outliers.field 指向文本键列", {"outliers": [{"field": "NAME"}]}),
            ("outliers.field 指向文本维度", {"outliers": [{"field": "DEPT", "method": "zscore"}]}),
            ("group_by.metrics 指向文本列", {"group_by": [{"dim": "DEPT", "metrics": ["NAME"]}]}),
            ("group_by.dim 不存在", {"group_by": [{"dim": "NOPE", "metrics": ["A"]}]}),
            ("top_n.field 指向文本列", {"top_n": [{"field": "NAME", "n": 3}]}),
            ("top_n.n 是字符串", {"top_n": [{"field": "A", "n": "三"}]}),
            ("outliers.k 是字符串", {"outliers": [{"field": "A", "k": "大"}]}),
            ("distributions.bins 含非数字", {"distributions": [{"dim": "A", "bins": ["低", 100]}]}),
            ("rules.when 是 DoS 表达式", {"rules": [{"name": "r", "when": "((10**999)**999)**999 > 0"}]}),
            ("rules.when 引用不存在变量", {"rules": [{"name": "r", "when": "NOPE > 0"}]}),
            ("what_if.set 指向文本列", {"what_if": [{"name": "w", "set": {"NAME": "NAME*2"},
                                                    "targets": [{"name": "t", "expr": "A"}]}]}),
            ("what_if.targets 表达式非法", {"what_if": [{"name": "w", "set": {"A": "A*1.1"},
                                                     "targets": [{"name": "t", "expr": "A.__class__"}]}]}),
            ("analysis 是列表", None),
        ]
        for title, an in acases:
            s = base_spec()
            if an is None:
                s["analysis"] = ["group_by"]
            else:
                s["analysis"] = an
            expect_clean_error(title, ["analyze", write_spec("an.json", s), "-d", detail, "-o", outa])

        print()
        print("=" * 96)
        print("A2-6 output / detail CSV 恶意输入")
        print("=" * 96)
        outo = os.path.join(WORK, "out_output")
        expect_clean_error("detail 指向 /etc/passwd",
                           ["output", BASE_SPEC, "-d", "/etc/passwd", "-o", outo])
        expect_clean_error("detail 指向不存在文件",
                           ["output", BASE_SPEC, "-d", "/nope/x.csv", "-o", outo])
        empty = os.path.join(WORK, "empty.csv")
        open(empty, "w").close()
        expect_clean_error("detail 是空文件", ["output", BASE_SPEC, "-d", empty, "-o", outo])
        onlyhdr = os.path.join(WORK, "hdr.csv")
        with open(onlyhdr, "w", encoding="utf-8-sig") as f:
            f.write("Excel行号,ID,NAME\n")
        expect_clean_error("detail 只有表头没有数据行",
                           ["output", BASE_SPEC, "-d", onlyhdr, "-o", outo])
        expect_clean_error("输出目录指向不可写位置",
                           ["output", BASE_SPEC, "-d", detail, "-o", "/proc/nope/out"])

    print()
    print("=" * 96)
    print("A2-7 tomd 的恶意输入")
    print("=" * 96)
    outm = os.path.join(WORK, "out_md")
    expect_clean_error("tomd /etc/passwd", ["tomd", "/etc/passwd", "-o", outm])
    expect_clean_error("tomd 目录", ["tomd", "/etc", "-o", outm])
    expect_clean_error("tomd 不存在的文件", ["tomd", "/nope.xlsx", "-o", outm])

    print()
    print("=" * 96)
    bad = [r for r in RESULTS if not r[0]]
    print("A2 小结：%d 条用例，攻破 %d 条" % (len(RESULTS), len(bad)))
    for _ok, title, detail, note in bad:
        print("  * %-40s %s %s" % (title, detail, ("｜" + note) if note else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
