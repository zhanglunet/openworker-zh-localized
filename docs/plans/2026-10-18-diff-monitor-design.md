# PRD-068/T1：上游 diff 监控脚本设计（哨兵方案）

> trend #295。PRD：`trend/adopted/PRD-068-owzh-diff-report.md`。
> 本稿是设计稿（T1），只定"怎么做"，不写实现代码；T2 按本稿实现。
> 相关仓库：zhanglunet/openworker-zh-localized（OpenWorker 全量汉化版）。

## 0. 与 PRD-029 的关系（一句话）

打个比方：PRD-029 是"每月一次大扫除"（release 级、双周/月、深度同步，出汉化 diff 报告）；
本 PRD 是给门口装"门铃"（commit 级、每周、轻量提醒）。门铃响了只告诉"有动静、要不要看"，
真正动手跟进翻译仍走 029 的流程——哨兵不代替大扫除。

## 1. 决策：新脚本 + 共享常量模块

**结论：新写 `scripts/upstream-weekly.py`，不扩展 `scripts/upstream-detect.py`。**

理由：

1. **节奏、粒度、输出都不同**：老脚本是 release 级输入（tag/release）、双周人工触发、
   输出汉化 diff JSON（喂 T3 报告模板）；哨兵是 commit 级输入、每周自动触发、
   输出周报 issue。硬塞一个 `--mode` 开关会让老脚本逻辑分叉，越改越难维护。
2. **故障隔离**：哨兵每周自动跑，难免偶发失败；老脚本是 029 深度同步的入口，
   必须保持稳定。两个独立入口，互不阻塞。
3. **演进方向不同**：老脚本以后只会做"更深"（冲突分析、工作量估算）；
   哨兵以后只会做"更轻更快"（推送、降噪）。

**但汉化敏感区定义必须只有一份源头**（评审硬要求）：

- 抽取共享模块 `scripts/upstream_common.py`（纯标准库，无第三方依赖），放：
  `SENSITIVE_PREFIXES` / `SENSITIVE_EXCLUDE` / `SENSITIVE_EXCLUDE_SUFFIXES` /
  `P0_PREFIXES`，以及 `is_sensitive()` / `is_p0()` 两个函数
  （即老脚本第 29–57 行原样搬移）。
- 老脚本改 `from upstream_common import ...`（行为零变化，py_compile + 冒烟验证），
  新脚本同样 import 这一份。**口径变更只改 `upstream_common.py` 一处**，
  不会出现两套敏感区打架。
- 抽取动作放在 T2 做（小重构，老脚本先行验证无回归再合）。
- 常量之外不共享逻辑：`classify()` 的 additions 透出等是 029 报告链专用的，
  哨兵的影响面分析（T2）自己定，不复用。

## 2. 检测逻辑设计

### 2.1 拉取什么

- 监控对象：L1=`andrewyng/openworker`、L2=`Lenovo202409/openworker-zh` 的默认分支。
  **T2 实现时先调 `GET /repos/{repo}` 取 `default_branch`，不硬编码 `"main"`**
  （L1 老脚本里 L2 写死了 `"main"`，哨兵不重蹈）。
- API：`GET /repos/{repo}/commits?sha={branch}&since={水位时间}&per_page=100`
  （按时间倒序）；另取分支 tip：`GET /repos/{repo}/commits/{branch}`。
- 调用量：每周约 4–6 次（tip×2 + compare/列表×2 + 容错），
  远低于 token 下 5000 次/小时的限流——PRD 说的"周级低频"成立。

### 2.2 水位与双保险（防 force-push）

每个上游记两个值：`sha`（上次见到的分支 tip）+ `checked_at`（上次检查时间）。

- **正常路径**：`GET /repos/{repo}/commits/{水位sha}` 返回 200（说明水位还在历史里），
  用 compare `{水位sha}...{当前tip}` 取新增 commit 列表——精确、无遗漏、无重复。
- **force-push 路径**：水位 sha 返回 404（上游重写了历史，水位已不在祖先链里），
  回退到时间窗口：`since={水位checked_at}` 拉取 commit 列表；同时输出 warning：
  "水位 SHA 失效（疑似上游 force-push），已按时间回退补拉，请人工核对有无遗漏/重复"。
  这就是 PRD 要求的"SHA 对不上时按时间回退补拉"。
- **首次运行**：水位为空 → 只记录当前 tip 和时间，**不产出"新增"**
  （避免把整部历史当新增刷屏），打 warning 说明"哨兵已上线，基线已建立"。
- **漏跑一周**：窗口天然是"上次 checked_at → 本次"，下次自动拉长补上，不丢数据。

### 2.3 失败与限流

- 重试：HTTP 5xx / 429 / 网络超时，按 1s → 4s → 16s 指数退避重试 3 次；
  仍失败则退出码非零（让 cron 标失败、人工可见），**水位不写回**
  （下次窗口自动拉长补上，不丢数据；写回一个没跑完的水位才会丢数据）。
- token：GitHub Actions 的 `secrets.GITHUB_TOKEN`（读公仓 commit 足够），
  不引入额外凭据。

### 2.4 输出（给 T2/T3 的接口约定）

```json
{
  "generated_at": "2026-10-19T01:00:00+00:00",
  "l1": {"new_commits": [{"sha": "abc…", "date": "2026-10-18", "message": "…", "author": "…"}]},
  "l2": {"new_commits": []},
  "warnings": []
}
```

影响面分析（T2）在这份 JSON 之上做；本 T1 不定其细节。

## 3. 水位记录位置：另起 `docs/upstream/watch-state.json`

**结论：不复用 `sync-state.json`，另起 `watch-state.json`（同目录 `docs/upstream/`）。**

理由：两个水位语义根本不同——

| | `sync-state.json`（029） | `watch-state.json`（068 哨兵） |
|---|---|---|
| 语义 | 汉化**跟进到哪了** | 哨兵**看到哪了** |
| 推进节奏 | 人工、双周 | 自动、每周 |
| 回退 | 回退时要往回调（PRD-029/T4 §3） | 永远只往前，不能回退 |

混在一个文件里，哨兵每周的自动写回会干扰 029 的人工基线：
最典型的是回退场景——029 回退时把 `last_synced_sha` 往回调，
哨兵水位要是跟着回退，下周会把已看过的 commit 重新报一遍（噪音）；
不跟着回退，两个字段在一个文件里各走各的方向，迟早有人改错。
分开存，各管各的水位，互不干扰。

格式：

```json
{
  "l1": {"sha": "abc…", "checked_at": "2026-10-19T01:00:00+00:00"},
  "l2": {"sha": "def…", "checked_at": "2026-10-19T01:00:00+00:00"},
  "quiet_weeks": 0,
  "last_run": "2026-10-19T01:00:00+00:00"
}
```

注：`sync-state.json` 目前 main 上尚不存在（029 正式启用时按 T2 §1.3 建立）；
`watch-state.json` 同理首次运行时创建。`quiet_weeks` 含义见 §4.2。

## 4. 周报 issue 规范

### 4.1 标题与去重

- 标题：**《上游周报 YYYY-MM-DD》**（日期=报告生成日）。
  与 029 的《上游同步 YYYY-MM-DD》前缀不同——两份 issue 流一眼区分，
  搜 `上游周报` / `上游同步` 各得其所。
- 幂等去重：同标题 issue 已存在 → 跳过不重发（防 cron 重跑、手动重跑发重复）。
- 正文结构（T3 定模板，本稿只定骨架）：
  本周上游 commit 数 → 影响中文版的 commit 数 → 需跟进翻译的文件清单 →
  无需跟进的变更一句话带过。

### 4.2 "本周无事"合并规则

- **判定**："影响中文版"的 commit 数为 0。注意是"无影响中文版的变更"，
  不是"上游无 commit"——上游可能每周都有几十个 commit，但一个都不碰敏感区，
  这也算"无事"。
- **动作**：不开新 issue；在**上期周报 issue 下追加一条评论**：
  "本周（YYYY-MM-DD）无事：上游 N 个 commit，均未命中汉化敏感区"。
- **计数器**：`watch-state.json` 的 `quiet_weeks`：impact=0 则 +1，否则清零。
  连续"无事"时一直追加评论、不开新 issue，避免产生垃圾 issue。
- **边界**：若历史上从无周报 issue（首次运行即无事）：开一条极简 issue
  说明"哨兵已上线，本周无事"，之后按追加评论走。

## 5. 给 T2–T5 的衔接

- **T2（影响面分析）**：在 §2.4 的 JSON 上做；敏感区匹配必须走
  `upstream_common.py`（§1），不许自立口径。
- **T3（周报模板）**：按 §4.1 骨架写全文模板；附一条**真实示例**
  （用已发生的真实 commit 回放生成，不伪造数据）。
- **T4（cron 调度）**：GitHub Actions `schedule: cron: '0 1 * * 1'`
  （= 周一 09:00 CST）；issue 推送用 `GITHUB_TOKEN`；失败重试按 §2.3；
  "无事"合并逻辑按 §4.2 实现。
- **T5（试运行两周）**：输出 2 份真实周报；PRD 验收项"人为构造一个影响中文版的
  上游 commit"——**诚实声明**：我们不能往 `andrewyng/openworker` 推 commit，
  该项改为"用历史真实 commit 回放验证标红逻辑"，或在自有 fork 里构造。
  不向任何上游仓库推送测试数据。

## 6. 不越界

- 本稿不写实现代码；不动 `scripts/upstream-detect.py` / `scripts/upstream-report.py`；
  不建 `watch-state.json`（首次运行时建）；不动 `sync-state.json`（它还不存在）。
- T2 的影响面分类细节、T3 的模板全文，本稿不定，留给对应任务。
