# OpenWorker 中文站周报

生成时间：2026-11-21T02:01:44+09:00

## 本周概览

- 2026-11-21 496311d4 fix: 老链 T5 复跑 pytest→unittest discover（CI 裸 python 无 pytest） (#182)
- 2026-11-20 f8c75e01 docs: refresh generated site reports
- 2026-11-20 6171c17f fix: 准入批遗留测试路径修正（MODULE_DIR/复跑/doc glob） (#180)
- 2026-11-19 b9510cd6 docs: refresh generated site reports
- 2026-11-20 15b2fe17 test(prd-558): T5 验收试运行 (#178)
- 2026-11-20 1e576757 test(prd-558): T4 划界断言 (#177)
- 2026-11-20 60cc1a59 feat(prd-558): T3 准入检查校验闸门 (#176)
- 2026-11-20 90c41586 feat(prd-558): T2 准入检查最小实现 (#175)

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
