# PRD-029/T2：上游变更检测实现方案

> trend #177。基于 T1 策略设计（`docs/plans/2026-10-17-upstream-sync-policy.md`，已合并 #5）。
> 本稿把"检测"落成可执行方案：检测脚本 + 监控清单 + 告警流程 + 与 T3 报告模板的字段对齐。

## 0. 先说清楚：和已有的 sync-upstream.yml 是什么关系

仓库里已经有一个 `.github/workflows/sync-upstream.yml`（每日定时）：它负责"代码合并"——
把 `andrewyng/openworker` 的 main 合进 `sync/upstream-main` 分支开 PR，人工检查后合并，
冲突时开 issue《上游同步需要人工解决冲突》。

本方案不重复造轮子，负责另一半："汉化 diff"——回答"这次上游变更里，哪些文件要重翻、
工作量多大"。两者衔接方式（§5）：

- 检测脚本以独立步骤挂在 sync-upstream.yml 成功合并之后，输出 JSON 挂到 sync PR；
- 月度/双周定时任务消费这些 JSON 生成报告（T3 模板），P0 则开 issue 告警。

## 1. 检测脚本：scripts/upstream-detect.py（草稿，随本 PR 落地）

纯标准库（urllib/json/argparse），无第三方依赖。用法：

```bash
export GITHUB_TOKEN=...   # 需 repo 读取权限的 token
# 干跑（默认）：只输出 JSON，不写回基线
python3 scripts/upstream-detect.py --state docs/upstream/sync-state.json
# 确认本轮检测有效后，再推进基线（书签往后挪）
python3 scripts/upstream-detect.py --state docs/upstream/sync-state.json --update-state
```

### 1.1 L1 检测（andrewyng/openworker，源头）

1. `GET /repos/andrewyng/openworker/releases?per_page=100` 取 release 列表（过滤 draft，
   草稿不参与 tag 推进），
   从 `last_synced_tag` 往后找新增 tag（按发布时间排序，遇到已同步 tag 即停）。
2. 对相邻 tag 逐段 `GET /repos/andrewyng/openworker/compare/{base}...{head}` 取文件级 diff，
   合并去重（同一文件取最后一次变更状态）。
3. 加密档触发条件（T1 已定）同样用 releases 数据判断：两周内新增 release ≥ 2 个，
   或任一 release 的 body 含 "breaking change"（大小写不敏感）。

### 1.2 L2 检测（Lenovo202409/openworker-zh，中转层）

1. `GET /repos/Lenovo202409/openworker-zh/compare/{last_synced_sha}...main` 取文件级 diff。
2. 停更检查：`GET /repos/Lenovo202409/openworker-zh` 取 `pushed_at`；
   若距今 > 90 天，输出 `l2.degraded=true` 并跳过 L2 diff（T1 修订：连续 3 个月无更新
   则降级为只看 L1）。
   - 现状（2026-10-17 核对）：L2 最后推送 2026-07-25，已近 3 个月；首次运行大概率直接触发降级，
     这是符合策略的，不是 bug。
   - `last_synced_sha` 未设定时脚本告警并跳过 L2 diff（与 L1 的 fail-quiet 对齐），不直接调 compare。

### 1.3 基线锚点（书签）

状态文件 `docs/upstream/sync-state.json`（`docs/upstream/` 目录已存在）：

```json
{
  "last_synced_tag": "v0.2.1",
  "last_synced_sha": "3613c327",
  "l2_degraded": false,
  "monitor_list_reviewed_at": "2026-10-17",
  "last_run": "2026-10-17T00:00:00Z"
}
```

打个比方：这就是夹在上游进度条上的"书签"。每次检测从书签位置往后看；
只有加 `--update-state` 时才把书签往后挪。默认干跑不写回，避免一次误跑污染基线。

首次运行建书签：`last_synced_tag` 取"已合入 owzh main 的最新 L1 tag"
（用 `git merge-base --is-ancestor` 或 tag 日期 ≤ 上次 sync 合并日期的最大 tag）；
`last_synced_sha` 取 L2 main 最新 sha（若未降级）。

### 1.4 文件分类

compare API 返回的每条 file 记录取 `filename` + `status`
（`added`/`modified`/`removed`/`renamed` 按 modified 处理）：

- 变更类型：新增 / 修改 / 删除（直接映射）。
- 敏感区命中：路径前缀匹配 §2 清单（大小写敏感，按仓库实际结构）。
- 输出 JSON 的 `files[]` 每条含：`path`、`change`、`sensitive`（bool）、`layer`（L1/L2）。

compare API 单次最多返回 300 个文件；超限时输出 `truncated=true` 并告警，
人工介入分段比对（T5 试运行验证是否够用）。

## 2. 监控清单（2026-10-17 已按仓库实际结构核对）

### 2.1 两层监控对象

| 层 | 仓库 | 监控内容 | API |
|---|---|---|---|
| L1 源头 | `andrewyng/openworker` | releases（tag 列表）→ compare 取文件 diff | `/releases`、`/compare/{base}...{head}` |
| L2 中转 | `Lenovo202409/openworker-zh` | main 分支 commits → compare 取文件 diff | `/compare/{sha}...main` |

L1 与 L2 顶层目录结构一致（coworker/、docs/、packaging/、stt/、surfaces/、tests/、
ui-mocks/），路径映射 1:1；owzh 独有 `website/`（中文站，oaosf.cn 对应，L1/L2 无此目录）。

### 2.2 汉化敏感区（owzh 实际结构，命中即标红）

| 敏感区 | 路径（已核对） | 说明 |
|---|---|---|
| UI 字符串 | `surfaces/gui/src/**/*.tsx`、`surfaces/gui/src/**/*.ts` | 中文直接内嵌在 React 代码里；**仓库内无 `locales/`、`i18n/` 目录，无独立语言包文件**（2026-10-17 全树核查，仅 `tests/test_shell_i18n_hazards.py` 名字含 i18n）。T1 稿中 "`*.json`/`locales/`" 的写法作废，以此为准。抽查 `surfaces/gui/src/App.tsx` 含约 60 处中文串。L1 侧 `surfaces/gui/src/` 同样存在，映射 1:1。 |
| 文档 | `docs/**/*.md` | 含 `docs/updates/`、`docs/upstream/`；`docs/plans/` 为本项目工作稿，不计入汉化工作量，排除 |
| 中文站文案 | `website/**` | Next.js 站点（oaosf.cn 对应）；只在 owzh 存在，上游 diff 不涉及，列入清单用于"影响已汉化文件"判定 |

非敏感（变更只记录，不进工作量）：`tests/`、`packaging/`、`releases/`、`.github/`、
`coworker/`、`stt/`、`ui-mocks/`、`surfaces/gui/e2e*/`（e2e 测试脚本）。

### 2.3 季度复核（PRD 风险要求）

- `monitor_list_reviewed_at` 记录上次复核日期；脚本每次运行时若超过 90 天，
  在输出中置 `monitor_review_due=true` 提醒。
- 复核内容：上游是否改名/重构导致路径失效（如 L1 把 `surfaces/gui` 改名）、
  新增的 UI 目录是否纳入敏感区。

## 3. 告警方案

### 3.1 P0 定义

`change ∈ {modified, removed}` 且命中 `surfaces/gui/src/`（用户看得见的 UI 字符串被改/被删）。

### 3.2 开 issue（当天，owzh 仓库）

- 月度档标题：`上游同步 YYYY-MM：<一句话摘要>`
- 双周档标题：`上游同步 YYYY-MM-DD：<一句话摘要>`（T1 修订：避免一月两报撞车）
- 正文：贴 T3 报告模板输出的全文。
- 去重：同标题的 open issue 已存在则追加评论，不重复开
  （做法参考 sync-upstream.yml 已有逻辑）。
- 与现有冲突 issue 区分：那个标题是《上游同步需要人工解决冲突》，
  管的是"代码合并不上"；这个管的是"中文要重翻"，标题不撞车。

### 3.3 无 P0

报告归档到 `docs/updates/`（目录已存在，内有 `CHANGELOG.md`、`WEEKLY.md`），不打扰。

## 4. 与 T1 / T3 的衔接

脚本 stdout 输出的 JSON 即 T3 报告模板的输入，字段对齐如下：

| T3 报告四节 | 输入字段 |
|---|---|
| 4.1 变更摘要矩阵 | `files[]`（`change` × `sensitive`，L1/L2 分开两节，`l2.degraded` 时注明"本轮只看 L1"） |
| 4.2 工作量估算 | `summary.added/modified/removed`、`summary.sensitive_hits`（T3 再定"字符串数"抽取规则与"50 字符串 ≈ 0.5 人日"系数校准） |
| 4.3 优先级建议 | `p0_files[]`（P0）、其余 sensitive added（P1）、docs 变更（P2） |
| 4.4 两层对照 | `l1.releases[]`、`l2` 小节 + 一句话结论字段 `verdict` |

本 PR 不写的内容（T3/T4 的活，不越界）：

- T3（#178）：报告模板正文 + 真实示例报告 + 工作量系数校准。
- T4（#179）：冲突分级（文本冲突/结构冲突/功能删除）、处理原则、回退流程。
- T5（#180）：真实跑一次全流程并复盘。

## 5. 运行方式建议

1. **事件驱动**：在 `sync-upstream.yml` 成功合并后加一个 step，跑脚本（干跑模式），
   把 JSON 作为 artifact 上传并在 sync PR 下贴摘要评论。检测频率自动跟随上游合入节奏。
2. **定时汇总**：月度（每月 5 日前）/ 双周（beta 期加密档）跑定时 workflow，
   用 `--update-state` 推进书签，生成报告输入；有 P0 则按 §3.2 开 issue。
3. **本地手动**：`python3 scripts/upstream-detect.py --state docs/upstream/sync-state.json`
   （需 `GITHUB_TOKEN`），T5 试运行即用此方式。
