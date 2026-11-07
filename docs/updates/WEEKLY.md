# OpenWorker 中文站周报

生成时间：2026-11-07T21:41:12+09:00

## 本周概览

- 2026-11-07 ce720cc docs: PRD-313/T1 openworker-zh-localized 重放包设计——replay-pack/v1（输入指纹+决策+输出、二值重放结论、重放面只读）（trend #1576） (#100)
- 2026-11-07 992fd0f docs: refresh generated site reports
- 2026-11-07 02ab6be PRD-240/T5 验收试运行：抽样知识问答溯源 (#94)
- 2026-11-07 2348e77 PRD-239/T5 验收试运行：中文口语指令抽样 (#93)
- 2026-11-07 71321c8 docs: refresh generated site reports
- 2026-11-07 ff4eb47 feat: PRD-240/T4 一致性校验——consistency_check.py check_consistency 三方对齐（E-DANGLING-REF 悬空引用规则 kb_refs/知识回指原文、E-CIRCULAR-REF 知识→规则反向引用禁止、E-ORPHAN-SOURCE 孤儿原文提示级）+ issues 机读清单（code/location/detail）+ summary errors/warnings/aligned（5 例，trend #1203） (#92)
- 2026-11-07 bfaf6bc feat: PRD-239/T4 按包加载与检索适配——pack_loader.py load_skills_for_runtime（目录形态加载 role-packs/*/skills/*/SKILL.md 与既有 store.py 同构，现有使用方式不断链不依赖登记资产）+ search_skills 检索（description/name 子串 OR/短词拒绝/确定性）（4 例，trend #1198） (#91)
- 2026-11-07 eefaa32 docs: refresh generated site reports

## 维护建议

- 每次发布前运行 `npm test`，确保首页、信息图、源码分析和日志页都能渲染。
- DMG 更新后同步校验 README、网站下载入口和 Release 说明。
- 上游同步前保持 PR 范围清晰，避免把中文站部署物和二进制文件混入不适合上游的改动。
