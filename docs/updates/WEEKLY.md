# OpenWorker 中文站周报

生成时间：2026-11-07T20:28:54+09:00

## 本周概览

- 2026-11-07 02ab6be PRD-240/T5 验收试运行：抽样知识问答溯源 (#94)
- 2026-11-07 2348e77 PRD-239/T5 验收试运行：中文口语指令抽样 (#93)
- 2026-11-07 71321c8 docs: refresh generated site reports
- 2026-11-07 ff4eb47 feat: PRD-240/T4 一致性校验——consistency_check.py check_consistency 三方对齐（E-DANGLING-REF 悬空引用规则 kb_refs/知识回指原文、E-CIRCULAR-REF 知识→规则反向引用禁止、E-ORPHAN-SOURCE 孤儿原文提示级）+ issues 机读清单（code/location/detail）+ summary errors/warnings/aligned（5 例，trend #1203） (#92)
- 2026-11-07 bfaf6bc feat: PRD-239/T4 按包加载与检索适配——pack_loader.py load_skills_for_runtime（目录形态加载 role-packs/*/skills/*/SKILL.md 与既有 store.py 同构，现有使用方式不断链不依赖登记资产）+ search_skills 检索（description/name 子串 OR/短词拒绝/确定性）（4 例，trend #1198） (#91)
- 2026-11-07 eefaa32 docs: refresh generated site reports
- 2026-11-07 b64c3b6 feat: PRD-240/T3 规则层计算接口——validate_rule §5 全字段（id 格式/词表/封闭类型/kb_refs 非空不悬空 §6.3/strict）+ evaluate_rule 可算执行（§5.1 四条钉死：纯函数/类型封闭/precondition 不满足统一 not_applicable/可重放）+ 三形态 expr（ast 白名单求值：算术/比较/逻辑/条件/min-max-abs 其余拒绝）/table 判定表/formula 算术，script 拒绝执行须沙箱评审 + 回指原文依据（evidence.sources 经 T2 trace_to_source 到 raw_text）（18 例，trend #1202） (#90)
- 2026-11-07 380fbac feat: PRD-239/T3 中文触发词登记册——§5.2 字段全量（19 条种子逐句入册+P0 产物名示范+2 条场景词同包多技能冲突示范）、收录冲突处理（check_conflicts：未标注跨技能同词拒绝并列出双方人工消歧，已标注放行）、lookup 口语命中（归一消形差/整句精确/条目短语嵌句、§5.4 裁决 P0→P3 排序、同级跨技能 ambiguous 待澄清可解释、停用留痕不删行）、coverage 三包覆盖检查、诚实边界声明（发行侧登记资产非运行时引擎）（14 例，trend #1197） (#89)

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
