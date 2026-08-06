# OpenWorker 中文站周报

生成时间：2026-08-06T09:03:55Z

## 本周概览

- 2026-08-06 bb2f4dc fix(smoke): 冒烟测试认不出零冲突的模型声明路径，且漏掉类型错误
- 2026-08-06 066c17c docs: refresh generated site reports
- 2026-08-06 ceff7ae fix(verify): 实测暴露的两个误判——推理模型假阴性、超时当成不支持
- 2026-08-06 c08a31d docs: refresh generated site reports
- 2026-08-06 f432782 docs(deployment): 企业站部署改写成逐步操作指南
- 2026-08-06 e399187 docs: refresh generated site reports
- 2026-08-06 3ef062b feat(enterprise): 企业站模板 + Cloudflare 部署流水线
- 2026-08-06 00c2fd9 docs: refresh generated site reports

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
