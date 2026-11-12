# OpenWorker 中文站周报

生成时间：2026-11-13T06:23:17+08:00

## 本周概览

- 2026-11-13 319850e Merge pull request #127 from zhanglunet/docs/16-align-enterprise-release-tags
- 2026-11-13 fedef57 docs: clarify wording flagged by terminology checks
- 2026-11-13 797f86e docs: align enterprise release tags and version examples
- 2026-11-11 5e9deda docs: refresh generated site reports
- 2026-11-11 c524679 Merge pull request #126 from zhanglunet/trend/baseline-fix-owzh
- 2026-11-11 1e1090a fix: owzh main baseline — read PRD-341 design doc from local main copy instead of un-fetched branch
- 2026-11-11 2055054 docs: refresh generated site reports
- 2026-11-11 9d33f91 Merge pull request #125 from zhanglunet/trend/prd-369-t5-decision-inbox-acceptance

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
