# OpenWorker 汉化版 · 定位、目标与愿景

- 记录日期：2026-10-24
- 读者：想知道「这个仓库是什么、近期做什么、长期往哪走」的维护者与企业定制同事
- 依据：仓库 [README.md](../README.md)、[README.en.md](../README.en.md)、[docs/enterprise/](enterprise/)、[PRD-029 上游同步策略](plans/2026-10-17-upstream-sync-policy.md)、[翻译流水线设计](plans/2026-10-19-i18n-pipeline-design.md)、[正式发布指南](release-signed-updates.md)、[签名暂缓记录](release-signing-deferred-plan.md)

仓库现有文档没有单独的「愿景」章。第 3 节是对上述材料的**归纳**，用来对齐口径，不另立产品决议。

---

## 1. 定位

本仓库是 [OpenWorker](https://github.com/andrewyng/openworker) 的**全量中文本地化版**。标语与 README 相同：

> 英文的 AI 桌面助手，中文的打开方式。

相对上游 `andrewyng/openworker`：与上游功能一致，只做语言层。PRD-029 把这条原则写成同步策略——上游的功能变更和汉化工作量分开记账，汉化版多出来的维度是「语言层 diff」。直接基线是 [Lenovo202409/openworker-zh](https://github.com/Lenovo202409/openworker-zh)（PRD-029 的 L2 中转层）。本仓库在这条基线上补齐前端加 Tauri 桌面壳的中文，并写清源码运行与环境安装。

README 差异表里相对上游多出的「自定义 API」和「阶跃星辰 StepFun」，是中转基线里已经带上的能力，本仓库照单继承。

两层读者：

| 读者 | 本仓库提供什么 |
|------|----------------|
| 中文个人用户 | GUI + Tauri 桌面壳；浏览器、Tauri 开发模式、macOS DMG 三种跑法；中文介绍站 [oaosf.cn](https://oaosf.cn) |
| 企业定制版 | 汉化基线。链路是上游 → 汉化版 → 企业版（[三仓同步方案](enterprise/UPSTREAM_SYNC.md)）。企业版消化汉化版，拿到的是「上游功能 + 中文界面」 |

许可证与上游相同，为 MIT，用于学习和个人本地使用。

---

## 2. 目标

### 2.1 近期

这三项在 2026-10-24 仍未合入 `main`，以当时打开的 PR 为准。

| PRD | 要交付的事 | 仓库里已经有的 | 尚未合入的 |
|-----|------------|----------------|------------|
| PRD-121 开箱即用 | 中文一行安装：装完看到中文界面 | 副标语已写「1 个 DMG 开箱即用」，公开 DMG 可下载试用 | [#38](https://github.com/zhanglunet/openworker-zh-localized/pull/38) 一行安装脚本（草稿） |
| PRD-122 双语 README | 英文 README 与中文版全章节对应 | 顶部中英切换，以及浓缩版 [README.en.md](../README.en.md)（PRD-102/T3，已合入） | [#39](https://github.com/zhanglunet/openworker-zh-localized/pull/39) 英文版全章节覆盖 |
| PRD-155 中文上下文可视化面板 | 中文面板：能力组成 + 调用演进 | `main` 上尚无该面板 | [#42](https://github.com/zhanglunet/openworker-zh-localized/pull/42) 信息架构、[#43](https://github.com/zhanglunet/openworker-zh-localized/pull/43) 能力组成、[#44](https://github.com/zhanglunet/openworker-zh-localized/pull/44) 调用演进 |

### 2.2 中期

- **跟得上上游。** 同步、周报、质量门、翻译流水线已经在仓库里运转，中期是持续用它们消化上游：
  - 同步策略：[PRD-029](plans/2026-10-17-upstream-sync-policy.md)（release 级汉化 diff）
  - 上游周报：[PRD-068](plans/2026-10-18-diff-monitor-design.md)（每周哨兵）
  - 质量门：[PRD-067](plans/2026-10-18-quality-gate-cases.md)
  - 翻译流水线：[PRD-084](plans/2026-10-19-i18n-pipeline-design.md)。设计稿的口径是第一期只做英→中
- **双语对外。** 中文是主文档。英文入口已有；全章节英文 README 归 PRD-122。翻译流水线（PRD-084）的范围是英→中初稿。
- **企业可复用。** [docs/enterprise/](enterprise/) 是企业定制的准备文档（目标、同步、部署、换肤打包）。本仓库保持为那条链路的中文基线。
- **正式发布。** 签名、公证与自动更新的做法写在 [release-signed-updates.md](release-signed-updates.md)。Apple Developer 与证书材料暂缓，见 [release-signing-deferred-plan.md](release-signing-deferred-plan.md)。README 第 10 节仍把「发布首个正式签名、公证版本」列为未完成项。当前公开 DMG 是未公证的本地化构建。

企业版自己的目标（员工开箱、数据不出内网、大表哥、一周内合入上游、多平台包）写在 [企业 PRD 第 1.2 节](enterprise/PRD.md)，不在本页展开。

---

## 3. 愿景（归纳）

下面三条从 README 与既有 PRD 归纳而来。仓库里没有单独的愿景章，这里不把它们写成新的验收标准。

1. **中文用户装上即用。** README 第 1 节的出发点是：官方 OpenWorker 默认界面全英文，汉化后日常中文用户更容易上手。副标语把这一点收成「1 个 DMG 开箱即用」。
2. **长期做上游的中文配音版，而不是停更后的死 fork。** PRD-084 把翻译流水线比作配音：上游通知一到，出带术语锁定的中文初稿，质量门通过再合入。PRD-029 的定期同步用来保证这条线不断档。
3. **做企业私有定制的稳定中文基线。** 企业 PRD 的背景是：汉化版已经完成界面中文化、macOS DMG、中文站与上游同步；企业版在此之上加技能、知识库、私有模型和品牌，同步时不覆盖这些定制（[三仓同步方案](enterprise/UPSTREAM_SYNC.md)）。

---

## 4. 本文不改什么

- 只记录口径，不改产品行为，也不新增功能承诺。
- 近期三项的完成与否以对应 PR 合入 `main` 为准；本页的 PR 编号是 2026-10-24 的快照。
