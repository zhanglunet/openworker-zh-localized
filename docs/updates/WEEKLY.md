# OpenWorker 中文站周报

生成时间：2026-11-07T22:46:07+09:00

## 本周概览

- 2026-11-07 7248db7 fix(prd299): 补回被合并覆盖的 T3 错误码封闭词表——zh_skill_ref 增加 ERROR_CODES 三码（修复 #97 合并事故，trend #1198） - 根因：PRD-299/T3（#97）合并时 -X theirs 吞掉词表，T3/T4 测试导入失败 → main CI 红 - 验证：PRD-299 链 T2/T3/T4/T5 共 33 例全过
- 2026-11-07 c2340ce docs: refresh generated site reports
- 2026-11-07 ce720cc docs: PRD-313/T1 openworker-zh-localized 重放包设计——replay-pack/v1（输入指纹+决策+输出、二值重放结论、重放面只读）（trend #1576） (#100)
- 2026-11-07 992fd0f docs: refresh generated site reports
- 2026-11-07 02ab6be PRD-240/T5 验收试运行：抽样知识问答溯源 (#94)
- 2026-11-07 2348e77 PRD-239/T5 验收试运行：中文口语指令抽样 (#93)
- 2026-11-07 71321c8 docs: refresh generated site reports
- 2026-11-07 ff4eb47 feat: PRD-240/T4 一致性校验——consistency_check.py check_consistency 三方对齐（E-DANGLING-REF 悬空引用规则 kb_refs/知识回指原文、E-CIRCULAR-REF 知识→规则反向引用禁止、E-ORPHAN-SOURCE 孤儿原文提示级）+ issues 机读清单（code/location/detail）+ summary errors/warnings/aligned（5 例，trend #1203） (#92)

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
