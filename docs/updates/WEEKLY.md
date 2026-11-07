# OpenWorker 中文站周报

生成时间：2026-11-08T02:30:09+09:00

## 本周概览

- 2026-11-08 184bb22 test: PRD-313/T5 验收试运行——全链两遍逐字节一致+拒绝零写盘+红线终检+文档无密钥（trend #1580） (#104)
- 2026-11-07 3ead2ab docs: refresh generated site reports
- 2026-11-08 50a969d fix(tests): T4 断言文件重生成——补占位符漏替换 (#103)
- 2026-11-07 d3a7538 docs: refresh generated site reports
- 2026-11-08 7434add feat: PRD-313/T3 重放校验闸门——replay_gate 一票否决+require_gate 异常形态+错误码扩 REPLAY_GATE_REFUSED（trend #1578） (#102)
- 2026-11-07 b2f3329 docs: refresh generated site reports
- 2026-11-07 189ef7f feat: PRD-313/T2 中文 skill 调用重放包最小实现——replay-pack/v1+登记册指纹+append-only 账本+verify_zh_replay 二值校验（11 例，trend #1577） (#101)
- 2026-11-07 dcb5d51 docs: refresh generated site reports

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
