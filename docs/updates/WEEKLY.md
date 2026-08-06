# OpenWorker 中文站周报

生成时间：2026-08-06T01:01:21Z

## 本周概览

- 2026-08-06 f2bcad5 feat(providers): 私有模型能力声明覆盖层 + 端点能力实测脚本（M1）
- 2026-08-06 5dd7db0 docs: refresh generated site reports
- 2026-08-06 dfd9907 feat(sheets): excel_ai 注册为内置工具（大表哥 L3）
- 2026-08-06 fa89654 docs: refresh generated site reports
- 2026-08-06 78a126d feat(gui): 表格助手入口（大表哥 L2）
- 2026-08-06 b9c6deb docs: refresh generated site reports
- 2026-08-06 068e1db docs(upstream): 归档调度器竞态的上游提交材料
- 2026-08-06 b09e893 test(automation): 补上 skip-on-overlap 竞态的确定性回归用例

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
