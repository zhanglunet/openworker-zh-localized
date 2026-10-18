# 上游周报模板（PRD-068/T3）

> 本文件是周报 issue 的正文模板，由 `scripts/upstream-weekly.py`（T2）自动填充
> `{{ }}` 占位符后发布为 issue。标题前缀固定为《上游周报 YYYY-MM-DD》
> （与 PRD-029 的《上游同步》区分，见 T1 §4.1）。
>
> 占位符与脚本输出的对应关系见文末"字段来源"。

---

# 《上游周报 {{report_date}}》

## 1. 本周上游动态概览

| 上游 | 本周 commit 数 | 涉及文件数 |
|---|---|---|
| L1 `andrewyng/openworker`（`{{l1_branch}}`） | {{l1_commit_count}} | {{l1_file_count}} |
| L2 `Lenovo202409/openworker-zh`（`{{l2_branch}}`） | {{l2_commit_count}} | {{l2_file_count}} |

- 监控窗口：{{window_start}} → {{window_end}}（上次 `checked_at` 到本次）。
- 影响中文版的 commit：**{{impacting_commit_count}}** 个。
- 水位：L1 tip `{{l1_tip_short}}`，L2 tip `{{l2_tip_short}}`。
{{warnings_block}}

## 2. 影响中文版的变更

> 分类口径 = T2 `classify_impact` 四类（`{{classify_version}}`）。
> `needs_translation`（新增文件 + 修改已汉化文件）单列为待办，走 PRD-029 流程跟进翻译；
> 哨兵本身只提醒、不动手。

### 2.1 新增文件（{{new_files_count}}）——需翻译

{{new_files_list}}
<!-- 格式示例：- `surfaces/gui/src/windowDrag.ts`（{{commit_sha_short}} {{commit_msg_short}}） -->

### 2.2 修改已汉化文件（{{modified_zh_count}}）——需对照更新

{{modified_zh_list}}
<!-- 格式示例：- `surfaces/gui/src/components/Composer.tsx`（{{commit_sha_short}} {{commit_msg_short}}） -->

### 2.3 修改未汉化文件（{{modified_other_count}}）——暂不跟进

{{modified_other_list}}
<!-- 非敏感区被改动的文件；确实没翻过，记一笔备查 -->

### 2.4 待办：需跟进翻译清单

{{todo_list}}
<!-- = 2.1 + 2.2 的文件去重清单，格式：- [ ] `路径`（来源 commit） -->

## 3. 无需跟进的变更

{{no_action_summary}}
<!-- 一句话带过，例如：其余 {{non_impacting_commit_count}} 个 commit 未命中汉化敏感区
     （多为 provider 模型 id / context window 参数、测试文件、后端非 UI 逻辑），无需跟进。 -->

## 4. 下周关注

{{watch_items}}
<!-- 人工填写的观察点，例如：上游 zh.json 本周有更新，对照官方译法有无变化；
     某文件被多个 commit 反复改动，汉化 diff 需重点看。无则写"无"。 -->

---

## 5. "本周无事"极简版式（T1 §4.2）

当"影响中文版的 commit 数"为 0 时，**不开新 issue**，改为在上期周报 issue 下追加一条评论，
正文用下面这一段（`{{ }}` 照样由脚本填充）：

> 本周（{{report_date}}）无事：上游 {{total_commit_count}} 个 commit，
> 均未命中汉化敏感区。`quiet_weeks` 已累计到 {{quiet_weeks}} 周。
> 水位：L1 `{{l1_tip_short}}`，L2 `{{l2_tip_short}}`。

边界：若历史上从无周报 issue（首次运行即无事），开一条极简 issue，
标题仍为《上游周报 {{report_date}}》，正文只放上面这一段，
并注明"哨兵已上线，本周无事"。

---

## 附：字段来源

| 占位符 | 来源 |
|---|---|
| `{{report_date}}` / `{{window_start}}` / `{{window_end}}` | 脚本运行时钟 / 水位 `checked_at` |
| `{{l1_branch}}` / `{{l2_branch}}` | `GET /repos/{repo}` 的 `default_branch`（不硬编码） |
| `{{l1_commit_count}}` / `{{l2_commit_count}}` / `{{l1_file_count}}` / `{{l2_file_count}}` | `detect_new_commits` 输出 |
| `{{impacting_commit_count}}` / 四类清单 / `{{todo_list}}` | `classify_impact` 输出 |
| `{{non_impacting_commit_count}}` / `{{no_action_summary}}` | `impacts_zh=false` 的 commit 汇总 |
| `{{l1_tip_short}}` / `{{l2_tip_short}}` | 分支 tip 短 SHA |
| `{{warnings_block}}` | `warnings` 数组（force-push 回退、首次基线等；无则整段省略） |
| `{{quiet_weeks}}` | `watch-state.json` 计数器 |
| `{{watch_items}}` | 人工填写（脚本留空由人补） |
