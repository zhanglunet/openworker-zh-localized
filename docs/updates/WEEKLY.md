# OpenWorker 中文站周报

生成时间：2026-11-16T07:42:51Z

## 本周概览

- 2026-11-16 28eafe7f chore: 更新上游哨兵水位（PRD-068）
- 2026-11-14 b72a1196 docs: refresh generated site reports
- 2026-11-14 fd713c85 Merge pull request #152 from zhanglunet/fix/sync-fail-loud
- 2026-11-15 3aeb47bf ci(sync): 拆假绿——合并失败让运行变红
- 2026-11-14 940d7265 docs: refresh generated site reports
- 2026-11-14 0c929a67 Merge upstream OpenWorker ecb44549 (#151)
- 2026-11-14 8acfb16b Merge remote-tracking branch 'upstream/main' into codex/sync-upstream-20261114
- 2026-11-14 795dd7df docs: refresh generated site reports

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
