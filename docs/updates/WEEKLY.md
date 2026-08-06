# OpenWorker 中文站周报

生成时间：2026-08-06T12:06:36Z

## 本周概览

- 2026-08-06 b2d490d fix(release): 发布权限预检 —— 别在构建完 20 分钟后才发现 token 是只读的
- 2026-08-06 9d69dad docs: refresh generated site reports
- 2026-08-06 057bbea feat(release): 方式 B 补 R2 上传路径 + 新增更新源端到端验证流水线
- 2026-08-06 ec04f81 docs: refresh generated site reports
- 2026-08-06 c68e903 fix(site): 免责声明里企业名两侧的空格 —— "非 亚信 官方发布"
- 2026-08-06 3aaa1f1 docs: refresh generated site reports
- 2026-08-06 b299059 fix(release): $VAR 紧邻全角字符 / Windows cp1252，两处中文导致的 CI 崩溃
- 2026-08-06 cef62de docs: refresh generated site reports

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
