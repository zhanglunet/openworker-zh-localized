# OpenWorker 中文站周报

生成时间：2026-08-06T06:38:59Z

## 本周概览

- 2026-08-06 f432782 docs(deployment): 企业站部署改写成逐步操作指南
- 2026-08-06 e399187 docs: refresh generated site reports
- 2026-08-06 3ef062b feat(enterprise): 企业站模板 + Cloudflare 部署流水线
- 2026-08-06 00c2fd9 docs: refresh generated site reports
- 2026-08-06 b26c4c8 fix(enterprise): 镜像前必须先关掉企业仓的 Actions
- 2026-08-06 209c7e8 docs: refresh generated site reports
- 2026-08-06 d477518 docs(upstream): 记录 PR #458 已提交
- 2026-08-06 81ac2d8 docs: refresh generated site reports

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
