#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""子进程沙箱执行器：在硬 CPU/内存上限下求值一条表达式，把结果以 JSON 打到 stdout。

必须用子进程 + RLIMIT_CPU：巨型整数幂、字符串重复这类 DoS 全在 C 层一条字节码里跑完，
Python 的 signal/alarm 根本插不进去，只有内核级的 SIGXCPU 能把它掐断。
"""
import json
import os
import resource
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))


def main():
    mode = sys.argv[1]           # eval | parse
    expr = sys.argv[2]
    cpu = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    mem_mb = int(sys.argv[4]) if len(sys.argv) > 4 else 1500
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    resource.setrlimit(resource.RLIMIT_AS, (mem_mb * 1024 ** 2, mem_mb * 1024 ** 2))
    sys.setrecursionlimit(3000)

    import excel_ai
    from excel_ai import SAFE, UserError

    env = {"A": 100.0, "B": 3.0, "NAME": "张三", "NAME__raw": "张三", "A__raw": "100"}
    t0 = time.time()
    try:
        if mode == "parse":
            SAFE.parse(expr, "attack")
            out = {"status": "REJECT_OR_OK_PARSE", "msg": "解析并通过白名单校验"}
        else:
            v = SAFE.eval(expr, env, "attack")
            s = repr(v)
            if len(s) > 70:
                s = s[:70] + "...(len=%d)" % len(s)
            out = {"status": "RESULT", "msg": s}
    except UserError as e:
        out = {"status": "REJECT", "msg": str(e).splitlines()[0][:110]}
    except MemoryError:
        out = {"status": "CRASH", "msg": "MemoryError（未被脚本捕获，触到内存上限）"}
    except RecursionError as e:
        out = {"status": "CRASH", "msg": "RecursionError: %s" % str(e)[:70]}
    except BaseException as e:  # noqa: BLE001
        out = {"status": "CRASH", "msg": "%s: %s" % (type(e).__name__, str(e)[:90])}
    out["sec"] = round(time.time() - t0, 3)
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
