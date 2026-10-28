# PRD-267/T5：验收试运行——虚构中文任务→技能

- 日期：2026-10-28
- 来源：`docs/plans/2026-10-28-prd-267-zh-skill-recorder.md`（T1 设计稿 §5 T5 验收）
- trend issue：[zhanglunet/trend#1339](https://github.com/zhanglunet/trend/issues/1339)
- 中央 PRD：`trend/adopted/PRD-267-owzh-skill-recorder-zh-skills.md`
- 全链：T1 #63（设计）→ T2 #65（zh_skill_recorder 12 例）→ T3 #67（zh_skill_draft 17 例）→ T4 #69（intake 9 例）→ **本任务 T5 #1339**
- 状态：T5 验收试运行，只开 PR 不合并，等用户 review

## 验收结论

**通过。** 验收测试 `tests/test_prd267_acceptance.py` 共 12 例全绿；前序链（T2 12 例 + T3 17 例 + T4 9 例）回归全绿，零回归。

## 试运行剧情（全虚构演示任务："把示例周报按周归档"）

录制三步时间线（每步 say_zh 口语原句在场）→ T3 生成草稿（canonical=把示例周报按周归档；colloquial=3 条，全部来自 say_zh 原句截取）→ T4 入库门三条件判定。

## 试运行步骤 × 结果

| # | 验收项 | 结果 | 证据 |
|---|---|---|---|
| 1 | 虚构中文任务回放时间线（say_zh 在场） | 通过 | 时间线 3 步 seq 有序回放、say_zh 逐字一致；`dump_capture` 落盘形态与 `render_markdown` 成稿均含 say_zh 原句 |
| 2 | Z-1 全角手机号阻断 | 通过 | `１３９１２３４５６７８`（全角）与 `13912345678`（半角）均 CaptureBlocked rule=Z-1（NFKC 归一覆盖）；say_zh 字段内全角手机号同拒 |
| 3 | 草稿 triggers canonical+colloquial>=3 | 通过 | canonical 恰 1 条（把示例周报按周归档）；colloquial 3 条且逐条可溯源到 say_zh 原句（不编造口语）；required_review=true + review.state=draft 在场 |
| 4 | 触发演示 | 通过 | `trigger_match` 命中 canonical（"帮我把示例周报按周归档"）与一条 colloquial；"今天中午吃什么好"/"帮我订个示例会议室"不命中 |
| 5 | 未 review 入库拒 | 通过 | draft 态 → admitted=False（reason 含 approved 指引）；approved 缺 reviewer 签字同样拒 |
| 6 | 触发词冲突复检拒 | 通过 | 同任务双草稿（重叠率>0.5）→ admitted=False，reason 含"冲突" |
| 7 | 三条件过收 | 通过 | approved 签字齐全 + 无冲突 + Z 复扫干净 → admitted=True，version=0.1.0 |
| 8 | 本地零网络断言 | 通过 | AST import 断言：三模块（recorder/draft/intake）仅标准库+本地互引，socket/urllib/http/requests/subprocess 等零命中 |
| 9 | 密钥扫描 | 通过 | 三模块 + 本测试 + 本验收记录 + 渲染成稿：密钥形态与内网主机名形态 0 命中 |
| 10 | 确定性 | 通过 | `render_markdown` 两次渲染字节一致 |

## 说明（如实披露）

- 触发演示的口语命中取 colloquial 首条做包含断言；无关话术取两条语义无关样例，均不命中（无泛匹配误触发）。
- 入库门的三条件顺序为 review 签字 → 冲突复检 → Z 复扫，任一失败硬拒且 reason 可读；验收逐条断言。

## 运行记录

```
$ .venv/bin/python -m pytest tests/test_prd267_acceptance.py -q
12 passed

$ .venv/bin/python -m pytest tests/test_prd267_zh_skill_recorder.py tests/test_prd267_t3_draft.py tests/test_prd267_t4_intake.py tests/test_prd267_acceptance.py -q
50 passed
```

前序链回归：T2 12 例 + T3 17 例 + T4 9 例全绿，零回归。

## 偏差披露

- 无。任务/话术/审核人全虚构；本地处理零网络；无密钥；触发词可用（canonical+colloquial 双层演示在场）。
