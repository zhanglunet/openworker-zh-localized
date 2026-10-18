"""上游监控共享定义（PRD-068/T1 §1）。

汉化敏感区定义的**唯一源头**：
- `scripts/upstream-detect.py`（PRD-029，release 级检测）
- `scripts/upstream-weekly.py`（PRD-068，commit 级哨兵）

都从这里 import。口径变更只改这一处，不会出现两套敏感区打架。

纯标准库，无第三方依赖。
"""

# 汉化敏感区（owzh 实际结构，2026-10-17 已核对；T1 稿的 locales//i18n/ 写法作废）
SENSITIVE_PREFIXES = ("surfaces/gui/src/", "docs/", "website/")
SENSITIVE_EXCLUDE = ("docs/plans/",)  # 本项目工作稿，不计汉化工作量
SENSITIVE_EXCLUDE_SUFFIXES = (".test.tsx", ".test.ts")  # T5 复盘建议②：测试断言的英文不需要重翻，计入 P0 是噪音
P0_PREFIXES = ("surfaces/gui/src/",)  # 用户看得见的 UI 字符串


def is_sensitive(path):
    if path.startswith(SENSITIVE_EXCLUDE):
        return False
    if path.endswith(SENSITIVE_EXCLUDE_SUFFIXES):
        return False
    return path.startswith(SENSITIVE_PREFIXES)


def is_p0(change, path):
    return change in ("modified", "removed") and path.startswith(P0_PREFIXES)
