#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键跑完全部安全对抗用例。

    python3 attacks/security/run_all.py

退出码 0 = 全部守住；非零 = 有用例被攻破（详见各套件输出）。
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SUITES = [
    ("A1 表达式求值器：逃逸 + DoS", "a1_probe_eval.py", 900),
    ("A2 spec/CLI：路径穿越 + 类型混淆", "a2_spec_cli.py", 1800),
    ("A3 CSV / xlsx 公式注入", "a3_csv_injection.py", 600),
    ("A4 1 万行性能 + 汇总行正确性", "a4_perf.py", 1800),
]


def main():
    bad = []
    for title, script, wall in SUITES:
        print("\n" + "#" * 96)
        print("# %s  （%s）" % (title, script))
        print("#" * 96, flush=True)
        t0 = time.time()
        try:
            p = subprocess.run([sys.executable, "-u", os.path.join(HERE, script)],
                               timeout=wall)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            rc = -1
            print("!! 套件整体超时 %ds" % wall)
        dt = time.time() - t0
        print("→ %s 用时 %.1fs，退出码 %d" % (script, dt, rc))
        if rc != 0:
            bad.append(title)

    print("\n" + "=" * 96)
    if bad:
        print("有套件被攻破：")
        for t in bad:
            print("  * %s" % t)
        return 1
    print("全部套件通过：表达式求值器守住白名单与资源上限；spec/CLI 全是中文报错；"
          "CSV/xlsx 无公式注入且转义可逆；1 万行在预算内。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
