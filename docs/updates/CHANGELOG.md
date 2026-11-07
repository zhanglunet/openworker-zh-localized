# OpenWorker 中文站更新日志

更新时间：2026-11-07T20:21:23+09:00

## 最近提交

- 2026-11-07 b64c3b6 feat: PRD-240/T3 规则层计算接口——validate_rule §5 全字段（id 格式/词表/封闭类型/kb_refs 非空不悬空 §6.3/strict）+ evaluate_rule 可算执行（§5.1 四条钉死：纯函数/类型封闭/precondition 不满足统一 not_applicable/可重放）+ 三形态 expr（ast 白名单求值：算术/比较/逻辑/条件/min-max-abs 其余拒绝）/table 判定表/formula 算术，script 拒绝执行须沙箱评审 + 回指原文依据（evidence.sources 经 T2 trace_to_source 到 raw_text）（18 例，trend #1202） (#90)
- 2026-11-07 380fbac feat: PRD-239/T3 中文触发词登记册——§5.2 字段全量（19 条种子逐句入册+P0 产物名示范+2 条场景词同包多技能冲突示范）、收录冲突处理（check_conflicts：未标注跨技能同词拒绝并列出双方人工消歧，已标注放行）、lookup 口语命中（归一消形差/整句精确/条目短语嵌句、§5.4 裁决 P0→P3 排序、同级跨技能 ambiguous 待澄清可解释、停用留痕不删行）、coverage 三包覆盖检查、诚实边界声明（发行侧登记资产非运行时引擎）（14 例，trend #1197） (#89)
- 2026-11-07 df71490 docs: refresh generated site reports
- 2026-11-07 7f6ae90 PRD-299/T4 与 PRD-267/285 及 239 双路径划界断言 (#98)
- 2026-11-07 4df6157 PRD-299/T3 引用解析歧义闸门：候选列表请用户选，人工消歧留痕 (#97)
- 2026-11-07 d101d6f docs: refresh generated site reports
- 2026-11-07 34b6080 feat: PRD-299/T5 验收试运行——中文口语指令 @引用 全链回放（6 例，trend #1500） (#99)
- 2026-11-07 782113b docs: refresh generated site reports
- 2026-11-07 adb4059 PRD-299/T2 引用解析最小实现：@中文技能名（归一/歧义候选/人工消歧留痕） (#96)
- 2026-11-07 182be98 docs: refresh generated site reports
- 2026-11-07 1ac0d58 docs: PRD-299/T1 中文指令 @中文技能名引用解析设计——中文 @语法与禁止形态（版本后缀/通配/中间空白不归一）/ref-resolution/v1 schema（meta_summary 定位+触发词计数零正文读取）/确定性归一四规则显形（全半角/繁简固定映射/去首尾空白——归一是规范化不是模糊匹配）/四错误码封闭词表（歧义列候选含一句话定位请用户选不按频次挑；chosen_from_candidates 人工消歧留痕）/与 239/T3 触发词登记册双路径划界（显式 @ 引用优先级高于口语命中，T4 断言预埋）/与 PRD-267/285 划界表（trend #1496） (#95)
- 2026-11-02 7034f06 docs: refresh generated site reports
