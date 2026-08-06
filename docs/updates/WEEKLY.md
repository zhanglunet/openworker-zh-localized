# OpenWorker 中文站周报

生成时间：2026-08-06T10:12:03Z

## 本周概览

- 2026-08-06 c68e903 fix(site): 免责声明里企业名两侧的空格 —— "非 亚信 官方发布"
- 2026-08-06 3aaa1f1 docs: refresh generated site reports
- 2026-08-06 b299059 fix(release): $VAR 紧邻全角字符 / Windows cp1252，两处中文导致的 CI 崩溃
- 2026-08-06 cef62de docs: refresh generated site reports
- 2026-08-06 5335f70 feat(site): 版本说明页 —— 原版 / 中文版 / 企业版的关系、对照表与信息图
- 2026-08-06 90cdee3 docs: refresh generated site reports
- 2026-08-06 f8811f9 fix(gui): 设置页「侧边栏」卡片被渲染了两次
- 2026-08-06 2c4e572 docs: refresh generated site reports

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
