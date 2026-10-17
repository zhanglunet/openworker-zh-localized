# PRD-029/T5：试运行复盘报告

> trend #180。T1（策略 #5）、T2（检测脚本 #7）、T3（报告模板 #11）均已合并进 main。
> 本次是第一次用真实数据跑完全流程（检测 → JSON → 报告 → 告警判断）并复盘。
> 只开 PR 不合并；T4（#179 冲突分级）不越界。

## 0. token 约束说明（必读）

检测脚本生产用法需要 `GITHUB_TOKEN`（跑在 GitHub Actions 里用平台提供的 token）。
本次试运行**没有提取、打印、记录任何 token 明文**：做法是把已合并的
`scripts/upstream-detect.py` 当模块导入，`gh_get` 换成走 PAT 通道
（`gh_api_pat.py`，凭据由通道托管、不经手明文）的等效实现，跑完全部真实逻辑。
这是真实数据全链路，等效性成立；约束如实注明。

## 1. 数据窗口与运行方式

- 运行时间：2026-10-17（UTC 08:00）。
- L1（`andrewyng/openworker`）：基线 `last_synced_tag=v0.3.0`，
  检测到新增 release `v0.3.1`（2026-10-05），compare `v0.3.0...v0.3.1`。
- L2（`Lenovo202409/openworker-zh`）：`last_synced_sha=None`（刻意），
  用于验证 T2 评审修的 guard（sha 未设定时不应 crash）。
- 模式：干跑（不带 `--update-state`，不写回基线）。

## 2. 全流程结果

```
upstream-detect.py（真实逻辑 + PAT 通道数据）
  → trial_detect.json
  → upstream-report.py --input trial_detect.json
  → 汉化 diff 报告（markdown，79 行）
```

| 环节 | 结果 |
|---|---|
| 检测脚本执行 | exit 0，无 crash；guard 路径生效（见 §3） |
| 文件变更 | 93 个（added 31 / modified 62 / removed 0），与 T3 示例一致 |
| 敏感区命中 | 25 个（`surfaces/gui` 20 + `docs/` 5，`docs/plans/` 已排除） |
| P0 | 16 个（全部 `surfaces/gui/src/` 下 modified） |
| L1 加密档 | `escalate=false`（两周内 1 个 release，无 breaking change） |
| 渲染器 | 端到端产出报告，四节齐全 |

**独立验证结论**：T3 示例报告的手工组装数字（93 文件 / 25 敏感 / P0 16 /
敏感区 additions 1640）与本次真实代码跑出的结果**完全一致**，示例可信。

## 3. 关键发现①：L2 降级还没触发（T2/T3 文档说早了几天）

- L2 最后推送 2026-07-25，距今 **83 天**，未达到 90 天阈值（`L2_STALE_DAYS=90`），
  本次**没有降级**（`degraded=false`）。
- T2/T3 文档写"已近 3 个月、首次运行大概率直接触发降级"——按 90 天硬阈值算，
  降级约在 **2026-10-24 前后**触发，比文档预期晚约一周。文档的"大概率"表述
  略乐观，特此校准（策略本身不用改）。
- guard 路径验证通过：`last_synced_sha=None` 时脚本没有调
  `compare/None...main`，而是告警"已跳过 L2 diff"并继续——T2 评审修的 bug
  确认修好。

## 4. 告警路径演练（只验逻辑，不真开 issue）

按 T2 §3.2（双周档标题 + 去重）/ §3.3（无 P0 不打扰）演练：

| 场景 | 输入 | 判定 | 结论 |
|---|---|---|---|
| A 真实数据 | 16 个 P0 | `should_alert=True`，标题 `上游同步 2026-10-17：L1 v0.3.1 新增 16 个 P0 待重翻` | 同标题 open issue 不存在 → 按规则应新建（演练到此为止，未真开） |
| B 无 P0 | `p0_files=[]` | `should_alert=False` | 走 §3.3 归档 `docs/updates/`，不打扰 |
| C 去重 | 同标题已存在时 | `dedup_check` 命中返回 issue 号 | 逻辑正确（本次无重复，未触发追加评论分支） |

另核：现有 open issue《上游同步需要人工解决冲突》与本次标题不撞车
（那个管"代码合并不上"，这个管"中文要重翻"），符合 T2 §3.2 的设计。

## 5. 工作量系数校准

T1 系数：每 50 字符串 ≈ 0.5 人日（T3 标注"T5 试运行后校准"）。

本次实测（真实 compare API 数据）：

| 口径 | 新增字符串数 | 粗估人日 |
|---|---|---|
| 真实 additions（敏感区求和） | 1640 | **16.4** |
| 回退口径（T2 JSON 无 additions，25 文件×50） | 1250 | 12.5 |

- **回退口径低估约 24%**（12.5 vs 16.4）。原因是 docs 类文件单文件 additions
  偏大（5 个 docs 文件 416 行，83 行/文件），50/文件的假设偏瘦。
- 诚实声明：样本只有 1 个窗口（n=1）；additions 计的是行数不是 UI 字符串数，
  一行可能含 0 个或多个字符串；测试文件会计入 P0/P1（见 §6）。
- **校准建议**：系数本身（50 字符串 ≈ 0.5 人日）暂时保留——它是"粗估"，
  诚实比精确重要；真正的校准需要 2–3 次真实运行后，对照实际投入工时回填。
  在此之前，先做 §6 的增强①（让估算永远走真实 additions 口径），
  消除已知的 24% 系统性低估。

## 6. "可选的 T2 增强"三条的决定建议

T3 文档列了 3 条留待 T5 复盘定。试运行证据如下：

1. **`files[]` 补 `additions`/`deletions` → 建议做。**
   证据：§5 的 24% 低估。改动小（`classify` 里多带两个字段，compare API
   本来就返回），渲染器已支持优先口径。做了之后不再需要回退口径。
2. **敏感区排除 `*.test.tsx` → 建议做。**
   证据：本次 P0 的 16 个里有 2 个是测试文件
   （`ApprovalCard.test.tsx`、`SettingsView.sandbox.test.tsx`），
   P1 的 4 个里也有 2 个测试文件。测试断言的英文不需要"重翻"，
   计入 P0 是噪音，会触发"当天开 issue"的误报感。
   在 `SENSITIVE_EXCLUDE` 加一条即可。
3. **L1 releases 过滤 prerelease → 暂缓。**
   证据：L1 当前 6 个 release 全是正式版，无 prerelease。等出现再做，
   现在做是过度工程。

另有两个小 polish（非 bug，不在本次 PR 动脚本，记入后续）：

- guard 跳过 L2 时（`degraded=false` 但 `l2.files` 为空），报告 4.1 的 L2 一节
  显示空矩阵、verdict 仍写"（L1+L2）"。建议：guard 跳过时 L2 一节也写一句话
  说明原因，verdict 层数如实写。
- 同上，属文案层面，不影响判断逻辑。

## 7. 下一步建议

1. 用户拍板 §6 的①②是否做 → 若做，开小 PR 改 `scripts/upstream-detect.py`
  （`classify` 带 additions；`SENSITIVE_EXCLUDE` 加测试文件），只开 PR 不合并。
2. L2 降级预计 2026-10-24 前后触发，届时可再跑一次验证降级路径
   （或等下次定时 workflow 自然触发）。
3. 系数真校准：下 2–3 次真实运行时记录实际投入工时，回填校准系数。
4. 本次试运行为干跑，基线未推进；正式启用时按 T2 §1.3 设定
   `last_synced_tag`/`last_synced_sha` 后再跑（`--update-state`）。

---
*试运行中间产物（检测 JSON、渲染报告、驱动脚本）保留在工作目录
`~/workspace/owzh-t2-029-t5/`，供复查。*
