# OpenWorker 中文站周报

生成时间：2026-11-07T20:21:23+09:00

## 本周概览

- 2026-11-07 b64c3b6 feat: PRD-240/T3 规则层计算接口——validate_rule §5 全字段（id 格式/词表/封闭类型/kb_refs 非空不悬空 §6.3/strict）+ evaluate_rule 可算执行（§5.1 四条钉死：纯函数/类型封闭/precondition 不满足统一 not_applicable/可重放）+ 三形态 expr（ast 白名单求值：算术/比较/逻辑/条件/min-max-abs 其余拒绝）/table 判定表/formula 算术，script 拒绝执行须沙箱评审 + 回指原文依据（evidence.sources 经 T2 trace_to_source 到 raw_text）（18 例，trend #1202） (#90)
- 2026-11-07 380fbac feat: PRD-239/T3 中文触发词登记册——§5.2 字段全量（19 条种子逐句入册+P0 产物名示范+2 条场景词同包多技能冲突示范）、收录冲突处理（check_conflicts：未标注跨技能同词拒绝并列出双方人工消歧，已标注放行）、lookup 口语命中（归一消形差/整句精确/条目短语嵌句、§5.4 裁决 P0→P3 排序、同级跨技能 ambiguous 待澄清可解释、停用留痕不删行）、coverage 三包覆盖检查、诚实边界声明（发行侧登记资产非运行时引擎）（14 例，trend #1197） (#89)
- 2026-11-07 df71490 docs: refresh generated site reports
- 2026-11-07 7f6ae90 PRD-299/T4 与 PRD-267/285 及 239 双路径划界断言 (#98)
- 2026-11-07 4df6157 PRD-299/T3 引用解析歧义闸门：候选列表请用户选，人工消歧留痕 (#97)
- 2026-11-07 d101d6f docs: refresh generated site reports
- 2026-11-07 34b6080 feat: PRD-299/T5 验收试运行——中文口语指令 @引用 全链回放（6 例，trend #1500） (#99)
- 2026-11-07 782113b docs: refresh generated site reports

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
