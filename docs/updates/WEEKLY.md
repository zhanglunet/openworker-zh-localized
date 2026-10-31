# OpenWorker 中文站周报

生成时间：2026-10-31T22:46:24+09:00

## 本周概览

- 2026-10-31 a4132cf Merge pull request #81 from zhanglunet/trend/prd-212-t3-probe
- 2026-10-31 ad404a1 Merge pull request #80 from zhanglunet/trend/prd-211-t3-templates
- 2026-10-31 f5136c4 feat: PRD-212/T3 中文触发词可用性抽查（14 条样本集/注入式唤起/三层通过标准/probe CSV 记录完整可回溯，8 例）（trend #1062）
- 2026-10-31 8e57f36 feat: PRD-211/T3 中文模板库（配置/首任务/角色包/会话续跑/纠正反馈五类，TOML 实测解析+键名对齐仓库样例+占位符规范+零密钥形态，6 例）（trend #1057）
- 2026-10-31 891d4f4 docs: refresh generated site reports
- 2026-10-31 fedc5ab Merge pull request #79 from zhanglunet/trend/prd-212-t2-sync-checklist
- 2026-10-31 af87a22 feat: PRD-212/T2 中文技能包跨工具同步检查脚本（CN-SYNC-01~09，只读）（trend #1061）
- 2026-10-31 4ddc3b6 docs: refresh generated site reports

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
