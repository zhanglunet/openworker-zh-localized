# OpenWorker 中文站周报

生成时间：2026-08-05T14:30:50Z

## 本周概览

- 2026-08-05 41b32bd ci: 新增中文站 Cloudflare 自动部署流水线
- 2026-08-05 aaeec98 docs: refresh generated site reports
- 2026-08-04 255da25 docs: 并入完整性检查发现的关键事实
- 2026-08-04 ed541e8 docs: 补充 sidecar 企业包打包与 updater 密钥切换断链说明
- 2026-08-04 726b11a docs: 企业定制版全套准备文档 + 站点企业定制扩展点章节
- 2026-08-04 614f87e docs: refresh generated site reports
- 2026-08-04 60c2e76 site: update Cloudflare compatibility date
- 2026-08-04 826d5c3 docs: refresh generated site reports

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
