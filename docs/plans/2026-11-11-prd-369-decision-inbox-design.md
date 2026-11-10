# PRD-369/T1：人工拍板收件箱设计（manual 项收口成一张桌子上的待办）

> trend issue #1648。对应 PRD-369（2026-11-11 日报第 12 条，用户「继续」按既定流水线立项）。
> 设计日：2026-11-11 · 目标仓库：zhanglunet/openworker-zh-localized
> 状态：T1 设计草案，待评审。仅设计文档（纯加法 .md）；收件箱内核（T2）、批阅闸门（T3）、划界断言（T4）、全链验收（T5）按本设计后续落地。
> 示例全部虚构占位，不出现真实主机名、IP、账号、密钥。

## 0. 红线

| # | 红线 | 落地方式 |
|---|---|---|
| R1 | **收件箱零自动执行** | approve/reject 只改条目状态留痕——零 checklist 状态改写（manual 仍是 manual，PRD-341 TAMPERED 红线继续）、零注册表写、零附答代填；INBOX_AUTO_EXEC_ATTEMPT 拒绝动作载荷 |
| R2 | **只读汇聚** | 统一收口三类人工项：checklist P10–P12 人工评审项（PRD-341 荐人工拍板零替人拍板）、附答后的人工确认、中文歧义候选（zh_skill_ref/trigger_registry 候选）——机检继续各判各的 |
| R3 | **每项带证据** | 逐条 `{item_id, kind, source_ref, fingerprint, questions?/candidates?, answers_ref?, state}` 缺一拒绝入箱——manual JSON 附答已留痕（PRD-341 §6.2），本条收口引用 |
| R4 | **账本 append-only + 拒绝留痕** | reject 留 by/at/reason |
| R5 | 占位符纪律 | T5 检查覆盖本文件 |
| R6 | 实现类 PR 只开不合并 | 等用户 review |

## 1. 借鉴对象、许可证与不复用红线

backnotprop/plannotator（Apache-2.0，实测）+ pingdotgg/t3code（MIT，实测）——只借鉴「人工拍板收件箱」控制面形态；条目 schema 按本仓中文 skill 域自研，零代码复用，不引入原仓依赖。

## 2. 与既有机制划界

| 维度 | PRD-369（本条） | PRD-341 checklist | PRD-299 zh_skill_ref |
|---|---|---|---|
| 管什么 | 人工侧**工作台** | 三态判定引擎 | 解析与候选 |
| 操作语义 | 人批/拒（零自动） | honest 三态 | 二值返回 |
| manual 语义 | 收口引用零改写（R1） | 荐拍板零替拍 | — |

## 3. 收件箱设计

### 3.1 schema（T2 预埋）

```json
{"schema": "decision-inbox/v1",
 "items": [{"item_id": "item-001",
   "kind": "manual_review|answer_confirm|zh_disambiguation",
   "source_ref": "skill-checklist-report/v1#P10（占位）",
   "fingerprint": "sha16:…", "questions": ["…（占位）"],
   "candidates": [], "answers_ref": null,
   "state": "pending|approved|rejected", "decided_by": null, "decided_at": null}]}
```

### 3.2 状态机（确定性）

collect（三源只读汇聚）→ pending；人 approve/reject 留痕（歧义项 approve 必带选中候选）；重复裁决/未知 id 显形拒绝。approved 是「人已拍板」记录——checklist 状态由 PRD-341 引擎按其规则流转，收件箱零代改。

## 4. 失败闸门（T3 落地）

| 错误码 | 触发 | 行为 |
|---|---|---|
| INBOX_ITEM_INCOMPLETE | 证据缺一 | 拒绝入箱 |
| INBOX_DOUBLE_DECIDE | 重复裁决 | 显形拒绝 |
| INBOX_AUTO_EXEC_ATTEMPT | 条目携带 checklist 写/注册表写/附答代填载荷 | 拒绝（R1） |
| INBOX_CHOICE_REQUIRED | 歧义项 approve 未带候选 | 显形拒绝 |

- kind 词表封闭三项。

## 5. 衔接

T2 内核；T3 闸门（四码+R1 零改写 AST）；T4 划界（与 341 TAMPERED 钉值联动+与 299 划界）；T5 样例回放+文档无密钥。

## 6. 开放问题

1. 与 PRD-341 manual_answers 的关系（收件箱 approve 后是否自动回填 answers——倾向零代填：人再走 run_checklist 附答或收件箱仅引用 answers_ref，待 T2 裁决）；
2. 汇总视图形态（全库待办一张桌+kind 过滤，待 T2）。
