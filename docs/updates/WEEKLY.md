# OpenWorker 中文站周报

生成时间：2026-11-21T08:25:55+09:00

## 本周概览

- 2026-11-21 37f4bc05 fix: 链复跑放行 rc=5（unittest 空跑=pytest 原生文件） (#188)
- 2026-11-20 e7253da7 docs: refresh generated site reports
- 2026-11-21 67675343 fix: 单引号 pytest 复跑 unittest 化 (#187)
- 2026-11-20 3ae25399 docs: refresh generated site reports
- 2026-11-21 695dd27f fix: 复跑块括号修复（] 替代误写的 )） (#186)
- 2026-11-20 2471523d docs: refresh generated site reports
- 2026-11-21 fd86ead0 fix: 剩余 pytest 复跑（TESTS 变量多行形态）unittest 化 (#185)
- 2026-11-20 95d0ee23 docs: refresh generated site reports

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
