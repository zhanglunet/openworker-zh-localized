# OpenWorker 中文站周报

生成时间：2026-08-05T15:27:05Z

## 本周概览

- 2026-08-05 8546ba0 ci: 测试版 Windows 只出 NSIS，并加 MSI 中文代码页诊断实验
- 2026-08-05 fb1b810 docs: refresh generated site reports
- 2026-08-05 fc875a3 ci: 测试版流水线支持手动触发发布并修正校验和生成
- 2026-08-05 ab204cf docs: refresh generated site reports
- 2026-08-05 5f4e397 ci: 新增未签名测试版发布流水线
- 2026-08-05 5279588 sync: 记录上游 OpenWorker 01b6f83 已并入（修复祖先链）
- 2026-08-05 1dbebca docs: refresh generated site reports
- 2026-08-05 41b32bd ci: 新增中文站 Cloudflare 自动部署流水线

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
