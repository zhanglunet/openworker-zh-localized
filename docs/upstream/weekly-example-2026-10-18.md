# 《上游周报 2026-10-18》（示例）

> **示例**：本文件是按 `weekly-template.md` 手填的格式示例，
> 数据取自真实上游（2026-10-11 → 2026-10-17 一周，手工回放分类），
> 不是脚本自动发布的周报。仅用于证明模板每个章节都能填上。

---

# 《上游周报 2026-10-18》

## 1. 本周上游动态概览

| 上游 | 本周 commit 数 | 涉及文件数 |
|---|---|---|
| L1 `andrewyng/openworker`（`main`） | 47 | 119 |
| L2 `Lenovo202409/openworker-zh`（`main`） | 0 | 0 |

- 监控窗口：2026-10-11 → 2026-10-18（上次 `checked_at` 到本次）。
- 影响中文版的 commit：**8** 个。
- 水位：L1 tip `5bf0d2fb`，L2 tip（无变化）。
- 无 warnings。

## 2. 影响中文版的变更

> 注：`d5441c1b` 是 `4178d680` 的合并提交，两者在 commit 列表里重复出现，
> 文件清单已去重说明（哨兵按 commit 逐条报，人工阅读时注意）。

### 2.1 新增文件（2）——需翻译

- `surfaces/gui/src/components/composerDraft.ts`（`29292791` Merge PR #606 keep-unsent-draft）
- `surfaces/gui/src/windowDrag.ts`（`ec114c30` Merge PR #745 topbar-window-drag）

### 2.2 修改已汉化文件（12）——需对照更新

- `surfaces/gui/src/components/Composer.tsx`（`d5441c1b` / `4178d680` / `29292791` / `94d0e733`，本周被 4 个 commit 改动）
- `surfaces/gui/src/styles.css`（`d5441c1b` / `4178d680`）
- `surfaces/gui/src/components/SearchModal.tsx`（`73415e9a` Merge PR #118 search-modal-ime-enter）
- `surfaces/gui/src/App.tsx`（`ec114c30`）
- `surfaces/gui/src/components/Markdown.tsx`（`67cc6088` Merge PR #225 fix-artifact-preview）
- `surfaces/gui/src/api.ts`（`a79f7c47`）
- `surfaces/gui/src/components/InboxItemCard.tsx`（`a79f7c47`）
- `surfaces/gui/src/components/ManageTabs.tsx`（`a79f7c47`）
- `surfaces/gui/src/components/connectors/ConnectorsSection.tsx`（`a79f7c47`）
- `surfaces/gui/src/locales/en.json`（`a79f7c47`）
- `surfaces/gui/src/locales/zh.json`（`a79f7c47`，上游官方中文包有更新）

### 2.3 修改未汉化文件（18）——暂不跟进

命中 commit 里的非敏感区改动，代表：`coworker/engine.py`、`coworker/server/app.py`、
`coworker/providers/errors.py`、`coworker/connectors/gateway.py` 等共 18 个
（后端逻辑、测试文件，不碰 UI 字符串）。

### 2.4 待办：需跟进翻译清单

- [ ] `surfaces/gui/src/components/composerDraft.ts`（新增）
- [ ] `surfaces/gui/src/windowDrag.ts`（新增）
- [ ] `surfaces/gui/src/components/Composer.tsx`（4 个 commit 改动，优先看）
- [ ] `surfaces/gui/src/components/SearchModal.tsx`
- [ ] `surfaces/gui/src/components/Markdown.tsx`
- [ ] `surfaces/gui/src/App.tsx`
- [ ] `surfaces/gui/src/api.ts` / `InboxItemCard.tsx` / `ManageTabs.tsx` / `ConnectorsSection.tsx`
- [ ] `surfaces/gui/src/locales/zh.json`（对照上游官方译法）
- [ ] `surfaces/gui/src/styles.css`（纯样式，大概率无文案，顺带确认）

## 3. 无需跟进的变更

其余 39 个 commit 未命中汉化敏感区（多为 provider 模型 id / context window 参数调整、
`*.test.tsx` / e2e spec 测试文件、后端非 UI 逻辑），无需跟进。

## 4. 下周关注

- 上游官方 `zh.json` 本周有更新（`a79f7c47`），对照看官方译法有无变化，
  与我们自维护译法的差异点记一笔（方案 A 口径）。
- `Composer.tsx` 本周被 4 个 commit 反复改动，汉化 diff 需重点看。
- L2（`Lenovo202409/openworker-zh`）本周 0 commit，已连续多周无更新，
  若上游持续停滞，季度复盘时重估 L2 监控价值。
