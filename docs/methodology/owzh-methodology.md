# openworker-zh-localized 中文 skill 方法论包方法论包（owzh-methodology/v1）

- 命令入口：`/zh-skill`（按 workflow 顺序驱动，--step 可逐步执行）
- skill 集：中文 skill 集（收口本仓既有技能，不新增形态）

## workflow（5 步标准做法）

| # | 步骤 | 完成判据 |
|---|---|---|
| 1 | 选题 | 选题判据可验证（字段见包校验） |
| 2 | 翻译 | 翻译判据可验证（字段见包校验） |
| 3 | 对照 | 对照判据可验证（字段见包校验） |
| 4 | checklist | checklist判据可验证（字段见包校验） |
| 5 | 人工拍板 | 人工拍板判据可验证（字段见包校验） |

## 模式库

- JSONL append-only：docs/methodology/owzh-patterns.jsonl
- 条目四件：pattern / source_case / evidence / caliber_version（缺一在 T3 校验拦下）；首份条目取自本仓真实产物。

## 红线

- 无方法论包的技能不成套、不进上游审批（T3 校验拦截）。
- 方法论包不代行审批：只定做法，内容对不对仍由评审流水线与监督回路审。
- 模式库只追加、不改历史条目。
