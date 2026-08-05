#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A1：安全表达式求值器的逃逸 / DoS 探针。

每条用例在**独立子进程**里跑（_runner.py），带硬 CPU 上限 3s + 内存上限 1.5GB：
巨型整数幂、字符串重复这类 DoS 全部发生在 C 层单条字节码内，只有内核 SIGXCPU 掐得断。

判定：
  逃逸类 —— 期望 REJECT（UserError）。出现 RESULT / CRASH / TIMEOUT 即攻破。
  DoS 类 —— 期望 3 秒内 REJECT 或 RESULT。TIMEOUT / KILLED / CRASH 即攻破。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "_runner.py")

ESCAPES = [
    ("海象表达式",          "(x := 1) + x"),
    ("海象污染变量",        "(A := 999)"),
    ("lambda 调用",         "(lambda: 1)()"),
    ("lambda 当参数",       "max(lambda: 1, 2)"),
    ("生成器表达式",        "sum(x for x in [1,2,3])"),
    ("列表推导",            "sum([x for x in [1,2]])"),
    ("集合推导",            "sum({x for x in [1]})"),
    ("字典推导",            "sum({k: 1 for k in [1]})"),
    ("f-string",            "f'{A}'"),
    ("f-string 取属性",     "f'{A.__class__}'"),
    ("str.format",          "'{}'.format(A)"),
    ("属性访问",            "A.__class__"),
    ("属性访问链逃逸",      "A.__class__.__base__.__subclasses__()"),
    ("字符串属性",          "'x'.__class__"),
    ("getattr",             "getattr(A, '__class__')"),
    ("__import__",          "__import__('os')"),
    ("eval",                "eval('1')"),
    ("exec",                "exec('x=1')"),
    ("open 读文件",         "open('/etc/passwd')"),
    ("__builtins__ 名字",   "__builtins__"),
    ("__builtins__ 下标",   "__builtins__['eval']"),
    ("globals()",           "globals()"),
    ("vars()",              "vars()"),
    ("下标访问",            "[1,2][0]"),
    ("字符串下标",          "'abc'[0]"),
    ("切片",                "[1,2,3][0:1]"),
    ("in 运算符",           "1 in [1,2]"),
    ("not in",              "1 not in [1,2]"),
    ("is 比较",             "A is None"),
    ("按位或",              "1 | 2"),
    ("按位异或",            "1 ^ 2"),
    ("左移",                "1 << 62"),
    ("整除",                "7 // 2"),
    ("矩阵乘 @",            "A @ B"),
    ("星号展开",            "max(*[1,2])"),
    ("关键字参数",          "round(A, ndigits=2)"),
    ("字典字面量",          "sum({'a': 1})"),
    ("集合字面量",          "sum({1, 2})"),
    ("嵌套调用后取属性",    "abs(A).__class__"),
    ("裸函数对象求值",      "abs"),
    ("函数对象格式化泄漏",  "'%s' % abs"),
    ("函数对象进 sum",      "sum([abs])"),
    ("await",               "await A"),
    ("yield",               "(yield 1)"),
    ("分号多语句",          "1; 2"),
    ("import 语句",         "import os"),
    ("字节串",              "b'abc'"),
    ("省略号",              "..."),
    ("复数",                "1j"),
    ("__raw 变量做属性跳板", "NAME__raw.__class__"),
]

DOS = [
    ("超大幂 2**10**9",           "2 ** 10 ** 9"),
    ("超大幂 直写指数",           "2 ** 1000000000"),
    ("嵌套幂 2 层",               "(10 ** 999) ** 999"),
    ("嵌套幂 3 层",               "((10 ** 999) ** 999) ** 999"),
    ("嵌套幂 4 层",               "(((10 ** 999) ** 999) ** 999) ** 999"),
    ("幂+乘法放大",               "(10 ** 1000) * (10 ** 1000)"),
    ("字符串重复 1e9",            "'a' * 1000000000"),
    ("字符串重复链",              "'a' * 100000 * 100000"),
    ("列表重复 1e8",              "sum([0] * 100000000)"),
    ("sum 大列表",                "sum([1] * 50000000)"),
    ("列表拼接二次方",            "sum([[1]] * 300000, [])"),
    ("格式化宽度爆炸",            "'%9999999999d' % 1"),
    ("格式化精度爆炸",            "'%.999999999f' % 1.0"),
    ("巨整数转字符串",            "'%s' % (10 ** 100000)"),
    ("深度嵌套加法 6 万层",       "1+" * 60000 + "1"),
    ("深度嵌套括号 6 万层",       "(" * 60000 + "1" + ")" * 60000),
    ("深度嵌套一元负号",          "-" * 60000 + "1"),
    ("深度嵌套函数调用",          "abs(" * 20000 + "1" + ")" * 20000),
    ("round 巨大 ndigits",        "round(1.5, 10 ** 9)"),
    ("int 十万位字符串",          "int('1' * 100000)"),
    ("非法幂次类型",              "2 ** 'x'"),
]


def run_one(expr, cpu=3, mem=1500, wall=12):
    try:
        p = subprocess.run([sys.executable, RUNNER, "eval", expr, str(cpu), str(mem)],
                           capture_output=True, timeout=wall)
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "墙钟 %ds 未返回" % wall, wall
    if p.returncode != 0 and not p.stdout.strip():
        err = (p.stderr.decode("utf-8", "replace").strip().splitlines() or [""])[-1]
        tag = "KILLED" if p.returncode < 0 else "CRASH"
        return tag, "退出码 %d %s" % (p.returncode, err[:80]), 0.0
    try:
        d = json.loads(p.stdout.decode("utf-8", "replace"))
    except Exception:
        return "CRASH", "子进程输出无法解析：%s" % p.stdout[:80], 0.0
    return d["status"], d["msg"], d["sec"]


def main():
    broken = []
    print("=" * 96)
    print("A1-1 逃逸类 —— 期望全部 REJECT，出现 RESULT/CRASH 即攻破")
    print("=" * 96)
    for nm, ex in ESCAPES:
        st, msg, sec = run_one(ex)
        if st != "REJECT":
            broken.append(("逃逸", nm, ex, st, msg))
        print("  [%-7s] %-22s %-34s → %s" % (st, nm, ex[:34], msg[:70]))

    print()
    print("=" * 96)
    print("A1-2 DoS 类 —— 期望 3 秒内 REJECT/RESULT，TIMEOUT/KILLED/CRASH 即攻破")
    print("=" * 96)
    for nm, ex in DOS:
        st, msg, sec = run_one(ex)
        if st not in ("REJECT", "RESULT"):
            broken.append(("DoS", nm, ex[:55], st, msg))
        print("  [%-7s] %-24s %6.2fs → %s" % (st, nm, sec, msg[:70]))

    print()
    print("=" * 96)
    print("攻破 %d 条" % len(broken))
    for kind, nm, ex, st, msg in broken:
        print("  * [%s][%s] %s  «%s»  → %s" % (kind, st, nm, ex[:46], msg[:70]))
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
