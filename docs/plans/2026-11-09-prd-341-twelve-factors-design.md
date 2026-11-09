# PRD-341/T1：生产级 agent 十二原则——中文 skill 生产化 checklist 设计（每条带可检查的验收标准）

> trend issue #1620。对应 PRD-341（2026-11-09 日报，用户拍板「都做」）。
> 设计日：2026-11-09 · 目标仓库：zhanglunet/openworker-zh-localized
> 状态：T1 设计草案，待评审。仅设计文档（纯加法 .md），不含任何实现代码；checklist 数据与机检器（T2）、通过闸门（T3）、划界断言（T4）、全链验收（T5）按本设计后续落地。
> 示例全部虚构占位（`写周报` 沿用仓库既有文档占位风格），不出现真实主机名、IP、账号、密钥。

## 0. 红线（本 PRD 全程不可越，置顶声明）

| # | 红线 | 落地方式 |
|---|---|---|
| R1 | **每条原则带可机检的验收标准** | 十二条原则逐条映射到既有机检器（trigger_probe / zh_sources / skillpack_snapshot / consistency_check 既有能力）——**没有机检器的原则不硬造**：如实标注「人工评审项」并写明评审问题清单（T3 断言：每条原则的检查形态 ∈ {机检器名, 人工评审} 封闭词表） |
| R2 | **只借原则零复用** | 借鉴对象 NOASSERTION——零代码零文本复用，十二条原则按本仓中文 skill 场景自研表述（T4 断言：checklist 与借鉴仓零字符串重合抽样比对） |
| R3 | **checklist 是数据不是代码** | 十二原则落成声明式 JSON（每条 `{id, principle, check_kind, check_ref?, manual_questions?}`）——增补/修订原则改数据不改机检器（T4 断言：机检器零 checklist 硬编码） |
| R4 | **checklist 输出 honest** | 结果三态：pass / fail(带 reason) / manual(带评审问题清单)——零「视为通过」路径（T3 断言） |
| R5 | **示例全虚构；文档与示例不得出现真实内部主机名、IP、账号或密钥** | 占位符纪律，T5 检查覆盖本文件 |
| R6 | **实现类 PR 只开不合并** | T2–T5 叠加分支 PR，等用户 review |

## 1. 借鉴对象、许可证与不复用红线

借鉴对象：humanlayer/12-factor-agents，**NOASSERTION（实测——无 LICENSE 标准化文件）**。

- **复用**：**零复用**。只借鉴「生产化要点可以穷举成带编号的原则清单」的**方法论形态**。
- **零复用落地**：不逐条翻译原仓十二因素；本仓十二条从**中文 skill 的实际生产风险**出发自研（每条对应一个已发生/可预见的事故面），表述全部中文原创。借鉴关系在文档头声明即止。

## 2. 与既有机制划界

| 维度 | PRD-341（本条） | PRD-199 skill 标准对齐 | PRD-227 分层规范 | PRD-303 excel 重放包 |
|---|---|---|---|---|
| 管什么 | 中文 skill **生产化成熟度**（跨既有规范汇总+补盲区） | 格式规范 | 分层发行 | 单点可重放 |
| 检查语义 | checklist 汇总既有机检 + 人工评审项 | 格式机检 | 登记册校验 | 重放校验 |
| 关系 | checklist 的 `check_ref` **指向既有机检器**复用其结论 | 被指向 | 被指向 | 被（重放原则）借鉴 |

- checklist 不重复实现既有检查——`check_ref` 指向既有机检器复用其结论（零重复建设，T3 断言）。

## 3. 十二条原则（自研表述，每条带检查形态）

| # | 原则 | 检查形态 | check_ref / 人工问题 |
|---|---|---|---|
| P1 | 入册合规：技能必须过登记册校验 | 机检 | `skill_registry.validate_registry` |
| P2 | 触发词可辩护：每个触发词有收录依据与冲突处理记录 | 机检 | `zh_trigger_registry.check_conflicts` |
| P3 | 原文可溯源：规则/知识条目能回指原文 | 机检 | `zh_sources.trace_to_source` |
| P4 | 三层对齐：规则/知识/原文三方引用无悬空无环 | 机检 | `consistency_check.check_consistency` |
| P5 | 引用合法：@引用解析目标全部存在且无环 | 机检 | `zh_skill_ref.resolve` 全量预演 |
| P6 | 升级可逆：skillpack 有快照且可回滚 | 机检 | `skillpack_snapshot` 校验 |
| P7 | 快照同步：cn_skill_sync_check 漂移检出为零 | 机检 | `cn_skill_sync_check` |
| P8 | 触发探针零冲突：探针样本命中预期技能 | 机检 | `trigger_probe` |
| P9 | 敏感词闸门通过：入库词表无敏感形态 | 机检 | 既有 intake gate |
| P10 | 描述质量人工评审：description 是否「让人一眼知道边界」 | 人工 | 评审问题：给三个新用户读 description，能否不动手册说清何时用/何时不用？ |
| P11 | 失败模式人工评审：技能最常见的三种误用是什么、有什么护栏 | 人工 | 评审问题：误用演练记录是否在册？ |
| P12 | 中文措辞人工评审：触发词与示例是否口语自然 | 人工 | 评审问题：非作者本人朗读能否复述用途？ |

- P1–P9 机检（全部指向既有机检器，零新建判定逻辑）；P10–P12 人工评审项（问题清单固定，人工逐条回答留痕）。

## 4. checklist 数据形态（T2 预埋）

```json
[
  {"id": "P1", "principle": "入册合规…", "check_kind": "machine",
   "check_ref": "skill_registry.validate_registry"},
  {"id": "P10", "principle": "描述质量…", "check_kind": "manual",
   "manual_questions": ["…", "…"]}
]
```

- 数据驱动：机检器按 `check_ref` 反射调用既有函数，零硬编码（R3）。

## 5. 与后续任务的衔接

| 任务 | 消费本设计的部分 |
|---|---|
| T2 checklist 数据+机检器 | §3 表格数据化 + check_ref 反射 |
| T3 通过闸门 | R4 三态断言（无视为通过） |
| T4 零复用+数据驱动断言 | R2 抽样比对 + R3 机检器零硬编码 |
| T5 验收试运行 | 对真实 skill 跑全量 checklist + 文档无密钥 |

## 6. 开放问题（留待评审/T2）

1. checklist 对象粒度（每 skill 一份 vs 全库一份汇总——倾向每 skill 一份+全库汇总视图，待 T2 裁决）；
2. 人工评审项的留痕载体（JSON 附答 vs markdown 评审记录——倾向 JSON 附答保持机读，待 T2 裁决）。
