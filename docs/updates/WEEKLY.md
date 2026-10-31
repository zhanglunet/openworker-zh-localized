# OpenWorker 中文站周报

生成时间：2026-11-01T01:36:14+09:00

## 本周概览

- 2026-11-01 a6ac61a Merge pull request #82 from zhanglunet/trend/prd-211-t4-crosslink
- 2026-10-31 2950a26 feat: PRD-211/T4 与 PRD-121 开箱叙事互链（叙事页与手册页双向可达/链接不悬空/术语预检零失败，4 例）（trend #1058）
- 2026-10-31 cc33ad8 docs: refresh generated site reports
- 2026-11-01 d920ddc Merge pull request #83 from zhanglunet/trend/prd-212-t4-remediation-guide
- 2026-10-31 d699329 feat: PRD-212/T4 漂移修复指引（CN-SYNC-01~12 全编号覆盖/状态枚举对齐 T2/诊断命令引真实脚本/术语预检零失败，4 例）（trend #1063）
- 2026-10-31 8035b12 docs: refresh generated site reports
- 2026-10-31 a4132cf Merge pull request #81 from zhanglunet/trend/prd-212-t3-probe
- 2026-10-31 ad404a1 Merge pull request #80 from zhanglunet/trend/prd-211-t3-templates

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
