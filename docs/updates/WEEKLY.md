# OpenWorker 中文站周报

生成时间：2026-08-06T00:09:49Z

## 本周概览

- 2026-08-06 7347760 fix(automation): 定时任务在 skip-on-overlap 下仍可能重复执行
- 2026-08-05 3923f58 docs: refresh generated site reports
- 2026-08-05 5f790df feat(enterprise): 大表哥 excel-ai-analyst 技能包（PRD F4 的 L1 层）
- 2026-08-05 661dfe9 docs: refresh generated site reports
- 2026-08-05 6cbe8c2 docs(enterprise): 新增可直接执行的企业仓模板（建仓/同步/冒烟/发布）
- 2026-08-05 1647e48 docs: refresh generated site reports
- 2026-08-05 12a7c83 fix(windows): MSI 打包指定 zh-CN WiX 语言，修复中文产品名构建失败
- 2026-08-05 0394aa2 docs: refresh generated site reports

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
