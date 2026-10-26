---
title: "造出了中文上下文面板：从一页设计稿到五个 PR 合并"
date: "2026-10-25"
status: 已发布
tags: [面板]
evidence:
  - https://github.com/zhanglunet/openworker-zh-localized/pull/42
  - https://github.com/zhanglunet/openworker-zh-localized/pull/43
  - https://github.com/zhanglunet/openworker-zh-localized/pull/44
  - https://github.com/zhanglunet/openworker-zh-localized/pull/46
  - https://github.com/zhanglunet/openworker-zh-localized/pull/47
artifacts:
  - ui-mocks/dsh-context-panel.html
  - ui-mocks/fixtures/panel-demo-data.json
  - docs/context-panel-guide.md
  - docs/context-panel-acceptance.md
  - tests/test_panel_acceptance_t5.py
bilingual: 见文末「英文摘要」段
---

# 造出了中文上下文面板：从一页设计稿到五个 PR 合并

> 中文用户双击就能看懂智能体的能力与调用——做法、踩坑、产物全部可查。

## 目标

给中文用户一个**零依赖、双击即开**的上下文面板：看懂一次会话里能力怎么装配（页签①「能力组成」）、调用怎么演进（页签②「调用演进」）。它是「中文开箱即用」差异点的第一块拼图（PRD-155，中文上下文可视化面板）。

**判定标准**（PRD-155/T5 验收两条，逐条可核对）：

1. 中文用户按文档 10 分钟内看懂面板；
2. 无密钥（演示数据、面板页、指南、验收记录逐行扫描零命中）。

对应验收 PR：[#47](https://github.com/zhanglunet/openworker-zh-localized/pull/47)，验收记录见 `docs/context-panel-acceptance.md`。

## 过程

从 2026-10-23 的一页设计稿到 2026-10-25 最后一个 PR 合并，五个任务各留一个可查的 PR：

**① 只做设计（T1，[#42](https://github.com/zhanglunet/openworker-zh-localized/pull/42)）**。不动一行实现，先定四件事：两区信息架构（能力组成 / 调用演进）、30 多条中文文案表（其中 11 条面板新词单独标出待拍板，如「上下文构成」「调用演进」；其余复用质量门已拍板的 25 条术语）、`panel-data v1` 数据契约（面板唯一认的数据格式）、适配层隔离——渲染层只认契约，上游接口变更的影响面压进单个适配器文件。关键取舍：借鉴 [bowenliang123/dsh-context](https://github.com/bowenliang123/dsh-context)（Apache-2.0）的「静态页 + 分区」形态，**不安装其英文-only 插件本体**，页脚保留借鉴声明。

**② 能力组成区落地（T2，[#43](https://github.com/zhanglunet/openworker-zh-localized/pull/43)）**。零依赖静态页：无构建、无 npm，Tailwind CDN + 明暗双主题，双击即开。演示数据全虚构，配 9 项自查断言：敏感模式扫描、占比五段恒和 1.00、账号一律占位符、文案逐字在场等。

**③ 调用演进时间线点亮（T3，[#44](https://github.com/zhanglunet/openworker-zh-localized/pull/44)）**。5 种节点（用户消息 / 工具调用 / 连接器调用 / 审批 / 智能体回复）与 3 种状态（成功 / 失败 / 已重试）全覆盖，演示数据里特意放了一对「失败 → 已重试」节点；点击节点出详情卡，契约里缺的字段显示「—」，**不造假数**。自查断言 9 → 13 项。

**④ 写入开箱文档（T4，[#46](https://github.com/zhanglunet/openworker-zh-localized/pull/46)）**。README 新增「开箱加餐」小节 + 使用指南 + 截图占位。

**⑤ 验收收尾（T5，[#47](https://github.com/zhanglunet/openworker-zh-localized/pull/47)）**。人工走查逐步计时（交互操作合计约 2.2 秒，含阅读理解合计 10 分钟内）+ 12 例自动化验收测试 + 真实截图替换占位 + 文档勘误（见下文踩坑②）。

## 踩坑

- **双击打不开数据**
  现象：面板壳正常上屏，数据区却是空的——本地双击（`file://`）打开时，页面用 fetch 去读同目录的 JSON 失败。
  原因：浏览器对 `file://` 来源的网络请求有安全限制，`fetch` 本地文件在很多浏览器里直接被拦。
  解法：页内嵌一份 `<script type="application/json">` 同源数据副本，demo 适配器先尝试 fetch fixtures、失败自动回退页内副本；再用测试钉住「页内副本与 fixtures 逐字一致」，防止两份数据日后漂移（`tests/test_panel_fixture_selfcheck.py`）。
- **文档和实现互相对不上**
  现象：T5 验收走查发现两处——使用指南步骤④写的是「◀ ▶ 步进关键节点或自动回放」，而 T3 实际交互是「点击节点看详情卡」；README 插入新小节后出现了两个「§9」。
  原因：文档写在实现之前、插入小节时没有重排后续编号——两类都是「先写文档、后核实现」的典型副产品。
  解法：验收逐条对照实现勘误，指南改为真实交互；README 章节重排为 9/10/11/12 并同步目录。勘误全程记录在 `docs/context-panel-acceptance.md` 的「勘误与收尾」小节，不悄悄改掉。

## 产物

- [ui-mocks/dsh-context-panel.html](../../../ui-mocks/dsh-context-panel.html) —— 双击即开的面板本体（`file://` 下自动回退页内数据副本）
- `ui-mocks/fixtures/panel-demo-data.json` —— `panel-data v1` 契约演示样例，可整体换成真实适配器输出
- `docs/context-panel-guide.md` —— 使用指南（README §9 的展开版）
- `docs/context-panel-acceptance.md` —— T5 验收记录（步骤 × 耗时表、密钥扫描、勘误清单）
- `tests/test_panel_fixture_selfcheck.py`（13 例）、`tests/test_panel_docs.py`（3 例）、`tests/test_panel_acceptance_t5.py`（12 例）—— 防回退的三层测试

---

## 英文摘要（bilingual）

We built a zero-dependency Chinese context panel for OpenWorker: double-click one static HTML file and you can read what capabilities an agent session assembles (tab 1) and how each call evolves (tab 2), including failure/retry states. It shipped as five reviewed pull requests over three days ([#42](https://github.com/zhanglunet/openworker-zh-localized/pull/42), [#43](https://github.com/zhanglunet/openworker-zh-localized/pull/43), [#44](https://github.com/zhanglunet/openworker-zh-localized/pull/44), [#46](https://github.com/zhanglunet/openworker-zh-localized/pull/46), [#47](https://github.com/zhanglunet/openworker-zh-localized/pull/47)), with a stable `panel-data v1` contract between the renderer and any data source, demo data that is fully fictional, and 28 regression tests pinning the behavior. The renderer never talks to upstream APIs directly — an adapter isolates upstream changes — so the same panel can later run on live local data by swapping one adapter. See [README.en.md](../../../README.en.md) for the English entry.

## 相关阅读

- 当期周报（commit 级流水账，与本篇互链不互替）：[docs/updates/WEEKLY.md](../../updates/WEEKLY.md)
- 栏目索引：[README.md](README.md)
