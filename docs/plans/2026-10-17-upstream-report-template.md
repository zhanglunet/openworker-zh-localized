# PRD-029/T3：汉化 diff 报告模板

> trend #178。输入是 T2 检测脚本（`scripts/upstream-detect.py`）输出的 JSON，
> 输出是一份维护者能直接按单干活的 markdown 报告。
> 渲染器：`scripts/upstream-report.py`（纯标准库）；真实示例：`2026-10-17-upstream-report-example.md`。

## 报告四节（固定格式）

### 4.1 变更摘要矩阵

| 变更类型＼影响面 | 影响已汉化文件 | 未影响已汉化文件 |
|---|---|---|
| 新增 | ⚠️ 需汉化（列文件清单） | 记录即可 |
| 修改 | ⚠️ 需重翻（列文件清单） | 记录即可 |
| 删除 | ⚠️ 跟随删除僵尸翻译 | 记录即可 |

- L1（`andrewyng/openworker`）与 L2（`Lenovo202409/openworker-zh`）分开两节列，
  互不混算（中转层已处理的变更不重复计入）。
- `l2.degraded=true` 时 L2 一节只写一句话："本轮已降级，只看 L1"，
  不再列空矩阵。
- T2 JSON 字段：`files[]`（`change` × `sensitive` × `layer`）。

### 4.2 工作量估算

- **新增字符串数**：优先用 compare API file 记录的 `additions` 字段
  （新增行数≈新增字符串数，对敏感区文件求和）；
  T2 JSON 的 `files[]` 无 `additions` 时回退为"敏感文件数×50 字符串/文件"，
  报告中必须明确标注所用口径。
- **需重翻段落数**：敏感区 `modified` 文件数。
- **粗估工作量**：新增字符串数 ÷ 50 × 0.5 人日，保留 1 位小数。
  系数沿用 T1（"每 50 字符串 ≈ 0.5 人日"），**T5 试运行后校准**，
  在报告里原样注明，不假装精确。

### 4.3 优先级建议

| 优先级 | 定义 | 动作 |
|---|---|---|
| P0 | `modified`/`removed` 且命中 `surfaces/gui/src/`（用户看得见的 UI 字符串被改/被删） | 当天在 owzh 仓库开 issue（标题格式见 T2 §3.2） |
| P1 | 敏感区新增（`added`，非 docs）：新增功能的 UI 字符串，功能可用但显示英文 | 进汉化排期 |
| P2 | `docs/**`（除 `docs/plans/`）变更：文档类 | 随版本更新文档 |

- T2 JSON 字段：`p0_files[]`；P1/P2 由渲染器按上述规则从 `files[]` 派生。
- 每类列出文件清单（默认前 30 个，超出注"等 N 个，详见检测 JSON"）。

### 4.4 两层对照

- L1：本轮新增 releases 表（tag / 发布日期 / 是否 breaking change）。
- L2：最后推送时间、距今天数、状态（正常 / 已降级）。
- 末尾一句话结论（T2 JSON 的 `verdict` 字段），
  如"L2 已同步 L1 vX.Y.Z，本轮只需处理 L2 增量"或"本轮只看 L1"。

## 渲染器用法

```bash
# T2 检测 → T3 渲染，一条龙
python3 scripts/upstream-detect.py --state docs/upstream/sync-state.json \
  | python3 scripts/upstream-report.py --output docs/updates/report-YYYY-MM.md

# 或分开跑
python3 scripts/upstream-report.py --input detect.json --output report.md
python3 scripts/upstream-report.py --input detect.json --max-files 50  # 多列文件
```

- 纯标准库（argparse/json/sys），无第三方依赖。
- 默认干跑：只读 JSON、不写任何文件（输出走 stdout 或 `--output`）。

## 真实示例

`docs/plans/2026-10-17-upstream-report-example.md`：
用 2026-10-17 当天 L1 真实数据（`v0.3.0`→`v0.3.1`）跑出的完整报告，
L2 已降级（最后推送 2026-07-25），正好演示降级路径。文首注明了数据窗口与日期。

## 可选的 T2 增强（不改已合并的 T2 脚本，只记一笔）

以下改进留待 T5 试运行复盘时决定是否做进 T2，不在本 PR 动已合并的
`scripts/upstream-detect.py`：

1. `files[]` 补 `additions`/`deletions` 字段：T2 的 compare API 本来就返回这些字段，
   只是没写进 JSON；补上后渲染器永远走"优先口径"，不再需要回退。
2. 敏感区排除测试文件：`surfaces/gui/src/**/*.test.tsx` 这类测试文件目前按路径前缀
   算敏感，实际不需要重翻；可在 `SENSITIVE_EXCLUDE` 里加一条。
3. L1 releases 过滤 prerelease：beta 期预发布版本是否计入同步窗口，T5 时定。

## 不越界

- T4（trend #179）：冲突分级（文本冲突/结构冲突/功能删除）、处理原则、回退流程——本 PR 不写。
- T5（trend #180）：真实跑一次全流程并复盘，含工作量系数校准、脚本真实 API 联调——本 PR 不写。
