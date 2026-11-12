# OpenWorker 中文站更新日志

更新时间：2026-11-13T07:44:03+08:00

## 最近提交

- 2026-11-13 3256bf3 Merge pull request #132 from zhanglunet/trend/prd-383-t5-checklist-failure-verify-bench-acceptance
- 2026-11-13 a30f15e Merge pull request #131 from zhanglunet/trend/prd-383-t4-checklist-failure-verify-bench-boundary
- 2026-11-13 130e998 Merge pull request #130 from zhanglunet/trend/prd-383-t3-checklist-failure-verify-bench-gate
- 2026-11-13 ee83f4e Merge pull request #129 from zhanglunet/trend/prd-383-t2-checklist-failure-verify-bench-impl
- 2026-11-13 30316f3 Merge pull request #128 from zhanglunet/trend/prd-383-t1-checklist-failure-verify-bench
- 2026-11-12 e630193 docs: refresh generated site reports
- 2026-11-13 319850e Merge pull request #127 from zhanglunet/docs/16-align-enterprise-release-tags
- 2026-11-13 fedef57 docs: clarify wording flagged by terminology checks
- 2026-11-12 3fcc22f test(prd-383): T5 验收试运行——验证台接入点全链演练（run_checklist 失败项→verify_failures→VERIFIED 转人工拍板来源形态→JSONL 落账→闸门全 pass）两遍逐字节一致+UNVERIFIED 拦截演练（误报失败拦在人工拍板外）落账留痕+checkers 变更二次验证关闭演练（STALE 拒绝复用）+零改写复验+append-only+链复跑子进程实测+文档无密钥（trend #1887 的 T5 环节，6 例全绿）
- 2026-11-12 044f925 test(prd-383): T4 checklist 失败验证台划界断言——验证台面与收件箱/机检引擎/解析器/重放双向模块隔离+零外部仓内耦合钉值（gates 只 import 同链 checkers_fingerprint）+R1/R2/R3/R4 红线钉值+借鉴仓零符号（仅代码标识符）+§3 引擎/收件箱面符号不变
- 2026-11-12 a7261df feat(prd-383): T3 checklist 失败验证台闸门——mark_baseline+append_only_gate 账本只增不删复核（LEDGER_DRIFT）+verdict_gate 结论与复现证据双向对账（BENCH_REPRO_MISMATCH/BENCH_INCOMPLETE）+stale_gate checkers 指纹复核（BENCH_STALE）+gate_summary 一票否决+ERROR_CODES 随模块导出（348 教训）+零改写词面 AST+闸门只读（trend #1887 的 T3 环节，15 例全绿，T2 回归 11 例仍绿）
- 2026-11-12 d92cc20 feat(prd-383): T2 checklist 失败验证台最小实现——verify_failure 逐条失败复跑验证（recheck_fn 注入重跑同一 checker 集经 run_checklist 引擎，复现=同 check_id+状态 fail 匹配；机检器已修复→复现不出 UNVERIFIED 防误报失败进人工拍板）+verify_failures 人工拍板来源包装（UNVERIFIED 拦下）+FailureBenchLedger JSONL append-only 真实落库+reverify checkers 变更二次验证（BENCH_STALE 拒绝复用）+checkers_fingerprint（checker 名清单 canonical JSON sha16）+零改写词面 AST（trend #1887 的 T2 环节，11 例全绿，devlog 落库）
