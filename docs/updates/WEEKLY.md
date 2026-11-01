# OpenWorker 中文站周报

生成时间：2026-11-01T14:18:24+09:00

## 本周概览

- 2026-11-01 45cd15f fix: brace $date before the fullwidth title bracket (#41)
- 2026-10-31 c3d23dc docs: refresh generated site reports
- 2026-11-01 5d8853f Merge pull request #85 from zhanglunet/trend/prd-211-t5-acceptance
- 2026-10-31 65621f6 test: PRD-211/T5 验收——真人 15 分钟上手实测（手册四页齐全/全路径/导航/模板实测/术语干净，5 例）（trend #1059）
- 2026-10-31 8ea0da4 docs: refresh generated site reports
- 2026-11-01 5140b32 Merge pull request #84 from zhanglunet/trend/prd-212-t5-acceptance
- 2026-10-31 97db0dc test: PRD-212/T5 验收试运行——多工具环境记录完整（四工具 fixture/全量状态表/probe CSV/修复指引可达，3 例）（trend #1064）
- 2026-10-31 c3ba05a docs: refresh generated site reports

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
