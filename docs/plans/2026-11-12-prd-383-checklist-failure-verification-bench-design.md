# PRD-383/T1：checklist 失败验证台设计（失败复跑验证过才进人工拍板）

> trend issue #1887。来源：2026-11-12 GitHub 趋势日报（digests/2026-11-12.md）第 11 条，用户 2026-11-13 指令「拍板」采纳。
> 设计日：2026-11-12 · 目标仓库：zhanglunet/openworker-zh-localized
> 状态：T1 设计草案，待评审。仅设计文档（纯加法 .md）；验证台内核（T2）、闸门（T3）、划界断言（T4）、验收试运行（T5）按本设计后续落地。
> 示例全部虚构占位，不出现真实内部主机名、IP、账号或密钥。

## 0. PR 门槛自查（repos.yaml default_pr_gate）

| 门槛 | 落实 |
|---|---|
| require_integration_point | **接入点：`scripts/skill_checklist.py::run_checklist` 产出失败项（P10–P12 人工评审项）之后、`scripts/decision_inbox.py::collect(manual_reviews=…)`（PRD-369 收件箱）之前**——T2 验证台以注入式函数 `verify_failure(failure, checkers, recheck_fn)` 供机检流程在 collect 前调用；只把 VERIFIED 的失败项喂给 manual_reviews |
| no_missing_channel | 只消费 run_checklist 既有失败结构（checkers 注入）；复算=对同一 checker 集重跑机检（recheck_fn 注入，复用 run_checklist 既有机检器）；验证结论写本地 JSONL 账本（文件落库），零新外部渠道 |
| no_duplicate_module | main 上同类模块盘点：skill_checklist.py（机检本体）/ zh_call_replay.py（355 重放——管"中文调用可重放"，本条管"失败可复跑"，粒度不同）/ decision_inbox.py（369 收件箱）。**本条不另起机检器**：复算=注入式重跑同一 checker，复跑结果与失败项一致才 VERIFIED |
| impl_requires_devlog | T2~T5 实现 PR 各附 docs/devlog/2026-11-13-prd-383-*.md 开发记录+合规核对；账本落 JSONL 文件（路径注入），不只存内存 |

## 1. 红线

| # | 红线 | 落地方式 |
|---|---|---|
| R1 | **失败复跑验证过才进人工拍板** | 每条 checklist 失败先复跑既有机检器验证（防机检器本身误报）；复跑结果与失败项一致 → VERIFIED；复现不出 → UNVERIFIED——误报失败拦在人工拍板外（不进 369 收件箱） |
| R2 | **验证不产生新失败** | 复算=重跑注入的同一机检器（checker 状态只读），零新增检查规则；复现不出=UNVERIFIED 不猜不补 |
| R3 | **机器可读落账** | 每次验证 `{failure_id, check_id, kind, source_ref, checkers_fingerprint, failure, reproduce, verdict}` 八件套落 JSONL 账本；缺任一 BENCH_INCOMPLETE 拒绝入账 |
| R4 | **账本 append-only + 修复二次验证才关闭** | 验证账本只增不删；checkers 变更后二次验证落新记录，关闭以最新 VERIFIED 为准 |
| R5 | 占位符纪律 | T5 检查覆盖本文件 |
| R6 | 实现 PR 只开不合并 | 等用户 review |

## 2. 借鉴对象、许可证与不复用红线

openai/codex-security（Apache-2.0，实测）+ cloudflare/security-audit-skill（MIT，实测）——只借鉴「发现→验证→修复→再验证」控制面形态；条目 schema 按本仓机检域自研，零代码复用，不引入原仓依赖。

## 3. 与既有机制划界

| 维度 | PRD-383（本条） | PRD-341 checklist 引擎 | PRD-299 zh_skill_ref | PRD-355 重放包 | PRD-369 收件箱 |
|---|---|---|---|---|---|
| 管什么 | 逐条 **失败可复跑** | 三态判定产出 | 解析与候选 | 中文调用可重放 | 等人拍板 |
| 比对 | 失败 vs 重跑机检器 | 无 | 无 | 决策序列 vs 重演 | 无 |
| 关系 | run_checklist 之后、collect 之前 | 被消费 | 被区分 | 被区分 | 下游：验证过才可进 |

- TAMPERED 红线不变（验证台零 checklist 状态改写零注册表写）。

## 4. 验证台设计

### 4.1 条目 schema（T2 预埋）

```json
{"schema": "checklist-failure-verify-bench/v1",
 "items": [{"failure_id": "f-001",
   "check_id": "P10",
   "kind": "manual_review",
   "source_ref": "skill-checklist-report/v1#P10（占位）",
   "checkers_fingerprint": "sha16:…（checker 集快照）",
   "failure": {"check_id": "P10", "status": "failed（占位）"},
   "reproduce": {"rerun_match": true, "detail": "…（占位）"},
   "verdict": "VERIFIED|UNVERIFIED"}]}
```

### 4.2 流程（确定性）

run_checklist 失败项 → 逐条重跑同一 checker（注入 recheck_fn）→ 复跑结果与失败项一致（同 check_id+状态）→ VERIFIED / 否则 UNVERIFIED → 落账 → manual_reviews 只收 VERIFIED。

## 5. 失败闸门（T3 落地）

| 错误码 | 触发 | 行为 |
|---|---|---|
| BENCH_INCOMPLETE | 八件套缺一/词表外 | 拒绝入账 |
| BENCH_REPRO_MISMATCH | 声称 VERIFIED 但复跑不含同 check_id+状态（或反之） | 显形拒绝 |
| BENCH_STALE | checkers 快照指纹与当前不符 | 拒绝复用旧验证 |

## 6. 衔接

T2 内核（verify_failure + JSONL 账本）；T3 闸门（三码+零 checklist 写零注册表写 AST）；T4 划界（与 341/355/369 划界钉值+机检器零 import 注入重跑）；T5 样例全链回放+UNVERIFIED 拦截演练+文档无密钥。

## 7. 开放问题（留待评审/T2）

1. checkers_fingerprint 口径（倾向 checker 名清单 canonical JSON sha16——待 T2）；
2. 收件箱侧接入的强制方式（倾向 verify_failures 包装供 collect 调用方显式接入——待 T2）。
