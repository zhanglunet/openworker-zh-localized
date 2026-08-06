# OpenWorker 中文站周报

生成时间：2026-08-06T09:36:39Z

## 本周概览

- 2026-08-06 5335f70 feat(site): 版本说明页 —— 原版 / 中文版 / 企业版的关系、对照表与信息图
- 2026-08-06 90cdee3 docs: refresh generated site reports
- 2026-08-06 f8811f9 fix(gui): 设置页「侧边栏」卡片被渲染了两次
- 2026-08-06 2c4e572 docs: refresh generated site reports
- 2026-08-06 3aec7d6 fix(release): macOS 打包失败被吞成 exit 0；补签名断言；站点加免责声明
- 2026-08-06 364a7da docs: refresh generated site reports
- 2026-08-06 bb2f4dc fix(smoke): 冒烟测试认不出零冲突的模型声明路径，且漏掉类型错误
- 2026-08-06 066c17c docs: refresh generated site reports

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
