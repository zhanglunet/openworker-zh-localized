# PRD-268/T5：验收试运行——模拟故障切换

- 日期：2026-10-28
- 来源：`docs/plans/2026-10-28-prd-268-zh-sources.md`（T1 设计稿 §6 T5 验收标准）
- trend issue：[zhanglunet/trend#1344](https://github.com/zhanglunet/trend/issues/1344)
- 中央 PRD：`trend/adopted/PRD-268-owzh-agent-reach-zh-sources.md`
- 全链：T1 #64（设计）→ T2 #66（zh_sources 13 例）→ T3 #68（failover 7 例）→ T4 #70（boundary 7 例）→ **本任务 T5 #1344**
- 状态：T5 验收试运行，只开 PR 不合并，等用户 review

## 验收结论

**通过。** 验收测试 `tests/test_prd268_acceptance.py` 共 12 例全绿；前序链（T2 13 例 + T3 7 例 + T4 7 例）回归全绿，零回归。

## 试运行剧情（全虚构，example.com 占位）

对 bilibili 平台主源 `bili-primary`（备源 `bili-backup`）注入故障时间线：连续错误 1→5 次，观察 healthy→degraded→failed 状态机推进，failed 触发自动切备并留审计事件；恢复探测通过后切回留痕。

## 试运行步骤 × 结果

| # | 验收项 | 结果 | 证据 |
|---|---|---|---|
| 1 | 注入故障→degraded→failed→failover 切备（事件断言） | 通过 | 故障时间线逐步断言（1 错 healthy / 2 错 degraded / 5 错 failed）；failover 事件 type/at/source_id/from/to/reason/seq 齐全；active_source 切至备源；切换不清零计数（consecutive_failures=5 保留）；事件 JSON 可序列化 |
| 2 | 429 throttled 分列 | 通过 | 429 → state=throttled、doctor.throttled=true；与 degraded 在 summary 中分列计数（throttled=1 / degraded=1） |
| 3 | disallowed 停用 | 通过 | disallowed 备源不参与切换（跳过取下一合规备源）；全部备源停用 → failover no-op 返回 None 且零事件（不对抗平台处置/登录墙） |
| 4 | 恢复切回 | 通过 | 主源未恢复时 restore no-op；恢复探测 ok → healthy → zh_source_restore 事件（from=备/to=主）；事件流 [failover, restore] 顺序正确 |
| 5 | 违规条目拒载（auth≠none/robots≠true/缺 tos_url） | 通过 | auth=cookie/basic/token 均拒（reason 含 none，不绕登录墙）；robots_respected=False 拒；缺 tos_url 拒；混合注册表部分加载：合规 1 条入层、违规 2 条拒载且 source_id 可对账 |
| 6 | 平台预算叠加不超 | 通过 | 同平台双源默认预算 2：a、b 各取 1 后第三次取拒绝（叠加不超）；跨平台互不影响；预算可显式配置（3 时三取通过、第四取拒绝） |
| 7 | doctor JSON+中文文本 | 通过 | JSON：schema=zh-doctor-report-v1、summary 四态计数精确（healthy/failed/throttled/disallowed=1/1/1/1）、字段名全英文（机读纪律）；中文文本：健康/故障/来源ID 等中文态在场 |
| 8 | 零网络 | 通过 | AST import 断言：zh_sources.py 仅 json/pathlib/typing，socket/urllib/http/requests/selenium/playwright 等零命中（只消费调用方喂入的结果码） |
| 9 | 无登录墙绕过（代码路径断言） | 说明 | 源条目强制 auth=none + robots_respected=true（校验在场）；模块源码无 cookie/login/password/session_token 代码路径 |
| 10 | 零密钥 | 通过 | 模块/本测试/本验收记录：密钥形态与内网主机名形态 0 命中；示例 URL 全 example.com 占位 |

## 运行记录

```
$ .venv/bin/python -m pytest tests/test_prd268_acceptance.py -q
12 passed

$ .venv/bin/python -m pytest tests/test_prd268_zh_sources.py tests/test_prd268_t3_failover.py tests/test_prd268_t4_boundary.py tests/test_prd268_acceptance.py -q
39 passed
```

前序链回归：T2 13 例 + T3 7 例 + T4 7 例全绿，零回归。

## 偏差披露

- 无。模拟故障只经 `record_result` 喂入结果码，零真实网络请求；示例全虚构（example.com / 示例审核人形态）；不绕登录墙（auth=none 强制 + 无登录代码路径断言）；无密钥。
