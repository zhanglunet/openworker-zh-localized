#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRD-122/T3（trend issue #611）：中英 README 章节同步检查。

比对 README.md 与 README.en.md 的 H2 标题结构：
  - 数量必须一致；顺序一一对应；
  - 每一对标题须在 CANON 映射表中登记为同一节（编号/语言不同但语义对应）；
  - 不一致时报错（exit 1），CI 阻断。
零依赖标准库；--self-test 自检映射表覆盖两份文件的 H2 全集。
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# 中英同一节的登记表（zh 片段, en 片段）——按出现顺序一一对应
CANON = [
    ("一行安装", "One-line Install"),
    ("下载与中文介绍站", "Downloads & the Chinese Intro Site"),
    ("目录", "Table of Contents"),
    ("1. 为什么做这个汉化版", "1. Why Make a Chinese Edition"),
    ("2. 与原版的主要区别", "2. Main Differences from the Original"),
    ("3. 支持的运行方式", "3. Supported Ways to Run"),
    ("4. 快速开始", "4. Quick Start"),
    ("5. 第一次安装环境", "5. First-Time Environment Setup"),
    ("6. 使用方式", "6. How to Use"),
    ("7. 常见问题", "7. FAQ"),
    ("8. 已汉化的内容", "8. What Has Been Localized"),
    ("9. 开箱加餐", "9. Bonus"),
    ("10. 仓库结构", "10. Repository Structure"),
    ("11. 已知问题", "11. Known Issues"),
    ("12. 贡献与许可", "12. Contributing and License"),
]


def h2_list(text: str) -> list[str]:
    return [ln[3:].strip() for ln in text.splitlines()
            if ln.startswith("## ")]


def check() -> list[str]:
    zh = h2_list((REPO / "README.md").read_text(encoding="utf-8"))
    en = h2_list((REPO / "README.en.md").read_text(encoding="utf-8"))
    problems: list[str] = []
    if len(zh) != len(en):
        return [f"H2 数量不一致：zh={len(zh)} en={len(en)}——两份章节结构漂移"]
    if len(zh) != len(CANON):
        problems.append(
            f"登记表覆盖 {len(CANON)} 节，实际 {len(zh)} 节——新章节未登记")
    for idx, (hzh, hen) in enumerate(zip(zh, en)):
        if idx >= len(CANON):
            break
        zkey, ekey = CANON[idx]
        if zkey not in hzh:
            problems.append(f"第 {idx + 1} 节 zh 标题不含 {zkey!r}：{hzh!r}")
        if ekey not in hen:
            problems.append(f"第 {idx + 1} 节 en 标题不含 {ekey!r}：{hen!r}")
    return problems


def self_test() -> int:
    problems = check()
    if problems:
        for p in problems:
            print(f"README-SYNC: {p}")
        return 1
    print("README-SYNC: 通过（中英章节结构一致且登记表全覆盖）")
    return 0


if __name__ == "__main__":
    sys.exit(self_test())
