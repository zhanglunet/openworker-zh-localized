# OpenWorker 中文站周报

生成时间：2026-11-14T00:25:30+08:00

## 本周概览

- 2026-11-14 6aff67a Merge pull request #137 from zhanglunet/trend/prd406-t5-collab-session-acceptance
- 2026-11-14 49d0251 Merge pull request #136 from zhanglunet/trend/prd406-t4-collab-session-boundary
- 2026-11-14 be21c66 Merge pull request #135 from zhanglunet/trend/prd406-t3-collab-session-gates
- 2026-11-14 0599c0a Merge pull request #134 from zhanglunet/trend/prd406-t2-collab-session-impl
- 2026-11-14 0b0a48f Merge pull request #133 from zhanglunet/trend/prd406-t1-collab-session
- 2026-11-14 89c42e3 test(prd-406): T5 验收试运行——全链两遍逐字节一致+失败演练+链复跑+文档无密钥
- 2026-11-14 1def4bd test(prd-406): T4 划界断言——下游载体零导入+借鉴仓零符号+标准库-only+R1~R4 红线钉值
- 2026-11-14 655b9a3 feat(prd-406): T3 会话闸门——append_only LEDGER_DRIFT + accept 双向对账 + outlet 拦截 + gate_summary 一票否决

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
