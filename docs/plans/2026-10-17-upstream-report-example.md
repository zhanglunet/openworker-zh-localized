# 上游同步汉化 diff 报告（真实示例）

> **数据说明（必读）**：本报告为 PRD-029/T3 的真实示例，数据取自 2026-10-17 当天：
> - L1（`andrewyng/openworker`）：`v0.3.0`（2026-09-30）→ `v0.3.1`（2026-10-05），
>   93 个文件变更、53 个 commits；
> - L2（`Lenovo202409/openworker-zh`）：最后推送 2026-07-25，已 83 天无更新，
>   按 T1 策略降级，本轮只看 L1——正好演示降级路径，属正常行为；
> - 输入 JSON 按 T2（`scripts/upstream-detect.py`）输出形状组装，
>   `additions` 取自 compare API 原始值（T2 脚本当前不输出该字段，
>   见模板文档"可选的 T2 增强"第 1 条）。
>
> **值得注意的发现**：上游 v0.3.1 新增了 `surfaces/gui/src/locales/` 语言包机制
> （`en.json` + `zh.json`，其中 `zh.json` 约 95KB 为官方中文翻译）。
> 这意味着上游开始自带中文——汉化版是继续沿用"中文内嵌 tsx"还是改用上游的语言包，
> 应纳入下次监控清单季度复核（T2 §2.3）的议题。本示例中这两个文件在 compare 中为
modified，按规则列为 P0（用户可见 UI 字符串被改，当天开 issue）。

---

# 上游同步汉化 diff 报告

> 数据窗口：L1 `andrewyng/openworker` 新增 v0.3.1（2026-10-05），共 1 个 release；生成时间 2026-10-17T00:00:00+00:00。
> L2 `Lenovo202409/openworker-zh`：已降级（最后推送 2026-07-25，距今 83 天），本轮只看 L1。

## 4.1 变更摘要矩阵

### L1（`andrewyng/openworker`）

| 变更类型＼影响面 | 影响已汉化文件 | 未影响已汉化文件 |
|---|---|---|
| 新增 | 6 | 25 |
| 修改 | 19 | 43 |
| 删除 | 0 | 0 |

### L2（`Lenovo202409/openworker-zh`）

本轮已降级，只看 L1（L2 连续 83 天无更新，按 T1 策略降级）。

## 4.2 工作量估算

- 新增字符串数：约 1640（口径：compare API 的 additions 字段（新增行数≈新增字符串数））
- 需重翻段落数：19（敏感区 modified 文件数）
- 粗估工作量：16.4 人日（每 50 字符串 ≈ 0.5 人日；T5 试运行后校准系数）

## 4.3 优先级建议

### P0：用户看得见的 UI 字符串被改/被删（16 个，当天开 issue）
- `surfaces/gui/src/App.tsx`
- `surfaces/gui/src/api.ts`
- `surfaces/gui/src/cardPayloads.ts`
- `surfaces/gui/src/components/AccessSection.tsx`
- `surfaces/gui/src/components/ApprovalCard.test.tsx`
- `surfaces/gui/src/components/ApprovalCard.tsx`
- `surfaces/gui/src/components/Composer.tsx`
- `surfaces/gui/src/components/RightRail.tsx`
- `surfaces/gui/src/components/SandboxSection.tsx`
- `surfaces/gui/src/components/SettingsView.sandbox.test.tsx`
- `surfaces/gui/src/gallery/states.contract.json`
- `surfaces/gui/src/gallery/states/approval.ts`
- `surfaces/gui/src/humanize.ts`
- `surfaces/gui/src/locales/en.json`
- `surfaces/gui/src/locales/zh.json`
- `surfaces/gui/src/types.ts`

### P1：新增功能的 UI 字符串（4 个，功能可用但显示英文）
- `surfaces/gui/src/components/SandboxChip.test.tsx`
- `surfaces/gui/src/components/SandboxChip.tsx`
- `surfaces/gui/src/components/SessionSites.test.tsx`
- `surfaces/gui/src/components/SessionSites.tsx`

### P2：文档类变更（5 个）
- `docs/headless.md`
- `docs/macos-sandbox.md`
- `docs/openshell-inside.md`
- `docs/openshell.md`
- `docs/windows-sandbox.md`

## 4.4 两层对照

### L1 releases

| tag | 发布日期 | breaking change |
|---|---|---|
| v0.3.1 | 2026-10-05 | 否 |

### L2

- 最后推送：2026-07-25；距今 83 天；状态：已降级（只看 L1）

**一句话结论**：本轮检测到 93 个文件变更（L1），其中 25 个命中汉化敏感区，P0（用户可见 UI 字符串被改/被删）16 个。L2 已降级，只看 L1。

---
**告警/备注**：
- 示例输入：由 2026-10-17 真实 compare 数据组装；additions 字段为 compare API 原始值（T2 脚本当前不输出该字段，见模板文档“可选的 T2 增强”）
