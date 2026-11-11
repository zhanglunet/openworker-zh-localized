# PRD-355/T1：中文 skill 调用重放包设计（中文名解析稳定性的可重放验证）

> trend issue #1634。对应 PRD-355（2026-10-30 日报遗留第 11 条，用户「继续」按既定流水线立项）。
> 设计日：2026-11-11 · 目标仓库：zhanglunet/openworker-zh-localized
> 状态：T1 设计草案，待评审。仅设计文档（纯加法 .md）；重放账本内核（T2）、重放闸门（T3）、划界断言（T4）、全链验收（T5）按本设计后续落地。
> 示例全部虚构占位（`写周报` 占位风格），不出现真实主机名、IP、账号、密钥。

## 0. 红线

| # | 红线 | 落地方式 |
|---|---|---|
| R1 | **重放包三件套齐备** | `{input_fingerprint（中文指令原文 digest+注册表版本指纹）, decisions（解析到的技能包+歧义候选处理+触发词优先级）, output（结果摘要）}` 缺一拒绝入账（T3） |
| R2 | **重放零 skill 执行** | 重放只复算解析层（zh_trigger_registry.lookup / zh_skill_ref.resolve 注入式）——零 skill 实际执行零网络（T4 AST） |
| R3 | **对不上即报账本失败** | 重放解析结果与包内不一致 → REPLAY_MISMATCH 显形落失败证据（含 normalize 归一化差异线索），零静默换新解析 |
| R4 | **账本 append-only** | ReplayLedger 只增不删 |
| R5 | 占位符纪律 | T5 检查覆盖本文件 |
| R6 | 实现类 PR 只开不合并 | 等用户 review |

## 1. 借鉴对象、许可证与不复用红线

beenuar/AiSOC（MIT，2026-11-11 实测）+ CopilotKit/OpenBot（MIT，实测）——只借鉴「可重放决策账本」形态；包 schema 按本仓中文 skill 域自研，零代码复用，不引入原仓依赖。

## 2. 与既有机制划界

| 维度 | PRD-355（本条） | PRD-285 升级快照 | PRD-267 实操转技能 | PRD-341 checklist |
|---|---|---|---|---|
| 管什么 | 中文调用**可重放** | 升级可逆 | 技能来源 | 生产化成熟度 |
| 重放 | 解析层复算 | 版本回滚 | 无 | 无 |
| 执行语义 | 零 skill 执行（R2） | 回滚写 | 采集 | 机检 |

## 3. 重放包设计

### 3.1 schema（T2 预埋）

```json
{"schema": "zh-call-replay-pack/v1",
 "input_fingerprint": {"utterance": "写周报（占位）", "utterance_digest": "sha16:…",
   "normalized_digest": "sha16:…", "registry_version": "vN", "registry_digest": "sha16:…"},
 "decisions": [{"resolved_skill": "weekly-report（占位）",
   "trigger_hit": "写周报（占位）", "priority_rule": "priority 最高唯一（占位）",
   "ambiguous_candidates": []}],
 "output": {"result_digest": "sha16:…", "summary": "结果摘要（占位）"}}
```

### 3.2 流程（确定性）

指纹复核（utterance/normalized/registry digest 不符 → REPLAY_INPUT_DRIFT 拒绝）→ 注入同注册表快照重放 lookup/resolve → 解析结果与候选逐字节比对 → REPLAY_OK / REPLAY_MISMATCH。

## 4. 失败闸门（T3 落地）

| 错误码 | 触发 | 行为 |
|---|---|---|
| REPLAY_INPUT_DRIFT | 指令/归一化/注册表指纹不符 | 拒绝重放 |
| REPLAY_MISMATCH | 解析结果不一致 | 显形+失败证据入账（含归一化差异线索） |
| PACK_INCOMPLETE | 三件套缺一 | 拒绝入账 |

## 5. 衔接

T2 内核；T3 闸门（三码+R2 零执行 AST）；T4 划界（与 285/267/341 划界钉值）；T5 样例回放+MISMATCH 演练+文档无密钥。

## 6. 开放问题

1. normalized_digest 的价值（繁简/全半角归一化是解析前置——入指纹可在 MISMATCH 时区分「原文同但归一化变」vs「注册表变」，待 T2 校验）；
2. 注册表快照缺档策略（同 PRD-349 §6.1——拒绝显形，待 T2）。
