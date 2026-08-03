# OpenWorker 中文站周报

生成时间：2026-08-04T07:37:37+09:00

## 本周概览

- 2026-08-04 c6c4704 docs: refresh reports after Cloudflare deploy
- 2026-08-03 6aeb622 docs: refresh generated site reports
- 2026-08-04 f4fabd1 sync: merge upstream OpenWorker 01b6f83 (#2)
- 2026-08-03 7df3ca0 docs: refresh generated site reports
- 2026-08-04 a6b5334 docs: add source analysis and update reports pages
- 2026-08-04 f36b220 Update README download and site preview
- 2026-08-04 11fd242 Add localized macOS app download
- 2026-08-04 6a46c2a Distinguish Chinese macOS app bundle

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
