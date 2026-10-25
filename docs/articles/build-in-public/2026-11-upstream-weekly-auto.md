---
title: "让上游周报自己写出来：从 diff 哨兵到定时成稿"
date: "2026-11-01"  # 草案：目标发布月份，发布时定稿
status: 草案
tags: [上游同步]
evidence:
  - https://github.com/zhanglunet/openworker-zh-localized/pull/24
  - https://github.com/zhanglunet/openworker-zh-localized/pull/26
artifacts:
  - docs/updates/WEEKLY.md
  - docs/updates/CHANGELOG.md
  - .github/workflows/upstream-weekly.yml
bilingual: 见文末「英文摘要」段（草案，发布前补齐 ≥3 句）
---

# 让上游周报自己写出来：从 diff 哨兵到定时成稿

> 一句话导语（草案）：上游有动静，周报自动把 commit 级流水账转写好——拆一遍这条链路。

> 草案说明：本篇为栏目草案大纲（PRD-184/T3）。四段为写作提纲，踩坑为候选清单（标「待复核 / 在途」，成稿时逐条核实）；没有背书不发文、写不出踩坑不立项两条硬约束在立项时已核对。

## 目标

- 做成什么（拟）：讲清上游周报的自动转写链路——上游 diff 哨兵发现动静、影响面分析、模板转写成 `docs/updates/WEEKLY.md`，定时任务驱动，全程无人抄 commit。
- 判定标准（拟）：cron 触发后周报与更新日志自动刷新；试运行报告在案（PR #26），读者照文能复走一遍链路。

## 过程

- 链路拆解（拟，按 PRD-068 的五个已合并任务讲）：
  1. 监控设计：上游 diff 哨兵方案（[PR #17](https://github.com/zhanglunet/openworker-zh-localized/pull/17)）；
  2. 影响面分析实现（[PR #20](https://github.com/zhanglunet/openworker-zh-localized/pull/20)）；
  3. 周报模板（[PR #22](https://github.com/zhanglunet/openworker-zh-localized/pull/22)）；
  4. 定时调度（[PR #24](https://github.com/zhanglunet/openworker-zh-localized/pull/24)）；
  5. 试运行与报告（[PR #26](https://github.com/zhanglunet/openworker-zh-localized/pull/26)）。
- 写作时补：一个真实周期的输入/输出对照（占位，取发布前最近一周的周报做样例）。

## 踩坑

- 候选一（在途，可查）：周报标题里的 `$date` 紧贴全角括号时标题缺日期。
  现象：生成的周报标题里日期不出现，其余文字正常。
  原因：shell 对 `$date` 后紧跟全角字符的变量名边界判定有歧义，变量没被展开。
  解法（在途）：调整 `$date` 与全角括号的相对位置——修复见在途 [PR #41](https://github.com/zhanglunet/openworker-zh-localized/pull/41)，合并后本篇按定稿写法回写。
- 候选二（待复核）：生成式提交把周报流水账淹没。
  现象：git 历史里高频出现「刷新站点报告」类自动提交，周报逐条罗列时噪音大。
  原因：自动任务的生成提交与人工提交混在同一条提交流里，转写未做过滤。
  解法（候选）：转写时按作者 / 路径过滤生成类提交（具体口径成稿时定）。

## 产物

- [docs/updates/WEEKLY.md](../../updates/WEEKLY.md) —— 每周上游动静流水账（自动刷新）
- `docs/updates/CHANGELOG.md` —— 更新日志（同链路生成）
- `.github/workflows/upstream-weekly.yml` —— 定时调度入口

---

## 英文摘要（bilingual）

（草案，发布前补齐 ≥3 句：链路怎么跑、读者能复用什么、坑在哪）See [README.en.md](../../../README.en.md) for the English entry.

## 相关阅读

- 栏目索引：[README.md](README.md)
