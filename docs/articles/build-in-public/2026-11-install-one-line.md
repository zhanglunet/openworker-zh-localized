---
title: "修好了中文用户的第一步：一行命令装好运行环境"
date: "2026-11-01"  # 草案：目标发布月份，发布时定稿
status: 草案
tags: [打包]
evidence:
  - https://github.com/zhanglunet/openworker-zh-localized/pull/38
artifacts:
  - scripts/install-zh.sh（在途 PR #38）
  - tests/test_install_zh.py
bilingual: 见文末「英文摘要」段（草案，发布前补齐 ≥3 句）
---

# 修好了中文用户的第一步：一行命令装好运行环境

> 一句话导语（草案）：把 README 五步手工安装收成一行命令，全新机器也能照跑。

> 草案说明：本篇为栏目草案大纲（PRD-184/T3）。四段为写作提纲，踩坑为候选清单（标「待复核」，以 PR #38 合并时的实测为准）；没有背书不发文、写不出踩坑不立项两条硬约束在立项时已核对。

## 目标

- 做成什么（拟）：把 README §5 的五步手工环境安装（Python / Node.js / Rust / CMake / PATH）收成一行命令，含装前环境检查、已装组件跳过与装后自检。
- 判定标准（拟）：全新 macOS 环境上从零到启动脚本跑通，只敲一条命令；实测记录（机器形态、耗时区间）随文发布。

## 过程

- 链路拆解（拟，对应在途 PR [#38](https://github.com/zhanglunet/openworker-zh-localized/pull/38) 的 diff）：
  1. 为何选 Miniforge：不写系统目录、无需管理员权限（README §5.1 路线的脚本化）；
  2. 装前检查：哪些组件已存在、版本够不够、能否直接复用；
  3. 已知坑的固化：把 README §5.2「修复 mcp 版本不兼容问题」的手工步骤收进脚本；
  4. 装后自检：venv 内导入冒烟 + 关键版本号打印，失败给中文指引。
- 写作时补：每步的实测输出（占位，待 PR 合并后回填）。

## 踩坑

- 候选一（待复核）：全新机器 pip 安装阶段 mcp 相关包版本冲突报错。
  现象：按 README §5.2 安装后在「修复 mcp 版本不兼容问题」一步才失败，新手在此卡住。
  原因：上游依赖约束变动后，默认解析出的版本组合失配。
  解法（候选）：脚本内固定已验证的版本组合，装完立即做导入冒烟，失败时给中文报错指引而不是裸报错栈。
- 候选二（待复核）：机器上有多个 Python（系统自带 / brew / Miniforge）时 venv 绑错解释器，装完跑不起来。
  现象：安装成功、启动时报依赖缺失。
  原因：PATH 顺序因机器而异，venv 用了非 Miniforge 解释器。
  解法（候选）：脚本显式用 Miniforge 解释器路径创建 venv，并校验解释器版本号后继续。

## 产物

- `scripts/install-zh.sh` —— 一行安装脚本（在途 PR #38，合并后此行改为定稿链接）
- `tests/test_install_zh.py` —— 脚本自查测试（占位：以 PR #38 实际文件为准回填）
- README §4/§5 的联动改法（开箱文档接入属 PRD-183/T4 范围，本篇只链接不展开）

---

## 英文摘要（bilingual）

（草案，发布前补齐 ≥3 句：做成什么、怎么装、卡点在哪）See [README.en.md](../../../README.en.md) for the English entry.

## 相关阅读

- 当期周报（commit 级流水账，与本篇互链不互替）：[docs/updates/WEEKLY.md](../../updates/WEEKLY.md)
- 栏目索引：[README.md](README.md)
