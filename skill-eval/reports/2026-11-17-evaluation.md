# 技能评估报告（首份，2026-11-17）

- PRD：PRD-488（openworker-zh-localized）
- 设计依据：docs/plans/2026-11-17-prd-488-owzh-skill-evaluation-design.md
- 评估清单版本：v1，技能 12 个
- 阈值：`{"min_sample_tasks": 20, "min_relative_error_drop": 0.2, "max_new_error_types": 0, "overlap_similarity": 0.8}`（设计稿草稿阈值，待评审定稿、实测后复核）

## 一、质量门

| 技能 | 结论 | 原因 |
|---|---|---|
| security-fix-pr | 证据不足 | 样本量 0 < 20，不判通过 |
| semgrep-review | 证据不足 | 样本量 0 < 20，不判通过 |
| aws-posture | 证据不足 | 样本量 0 < 20，不判通过 |
| iac-scan | 证据不足 | 样本量 0 < 20，不判通过 |
| dependency-audit | 证据不足 | 样本量 0 < 20，不判通过 |
| safe-upgrade-pr | 证据不足 | 样本量 0 < 20，不判通过 |
| aws-posture@posture-worker | 证据不足 | 样本量 0 < 20，不判通过 |
| iac-scan@posture-worker | 证据不足 | 样本量 0 < 20，不判通过 |
| secret-scan | 证据不足 | 样本量 0 < 20，不判通过 |
| secret-scan@security | 证据不足 | 样本量 0 < 20，不判通过 |
| security-fix-pr@security | 证据不足 | 样本量 0 < 20，不判通过 |
| semgrep-review@security | 证据不足 | 样本量 0 < 20，不判通过 |

## 二、重叠检测

全量两两比对 66 对；疑似重叠（相似度 ≥ 阈值）5 对。
相似度为词元集合 Jaccard（设计稿嵌入余弦的最小可用代理，T2 不引入外部 embedding 服务）。

| 技能 A | 技能 B | 相似度 | 疑似重叠 |
|---|---|---|---|
| aws-posture | aws-posture@posture-worker | 1.000 | 是 |
| iac-scan | iac-scan@posture-worker | 1.000 | 是 |
| secret-scan | secret-scan@security | 1.000 | 是 |
| security-fix-pr | security-fix-pr@security | 1.000 | 是 |
| semgrep-review | semgrep-review@security | 1.000 | 是 |
| dependency-audit | safe-upgrade-pr | 0.226 | 否 |
| iac-scan | semgrep-review@security | 0.223 | 否 |
| iac-scan@posture-worker | semgrep-review@security | 0.223 | 否 |
| semgrep-review | iac-scan | 0.223 | 否 |
| semgrep-review | iac-scan@posture-worker | 0.223 | 否 |
| iac-scan | secret-scan | 0.213 | 否 |
| iac-scan | secret-scan@security | 0.213 | 否 |
| iac-scan@posture-worker | secret-scan | 0.213 | 否 |
| iac-scan@posture-worker | secret-scan@security | 0.213 | 否 |
| aws-posture | iac-scan | 0.211 | 否 |
| aws-posture | iac-scan@posture-worker | 0.211 | 否 |
| aws-posture@posture-worker | iac-scan@posture-worker | 0.211 | 否 |
| iac-scan | aws-posture@posture-worker | 0.211 | 否 |
| secret-scan | semgrep-review@security | 0.211 | 否 |
| secret-scan@security | semgrep-review@security | 0.211 | 否 |
| semgrep-review | secret-scan | 0.211 | 否 |
| semgrep-review | secret-scan@security | 0.211 | 否 |
| safe-upgrade-pr | security-fix-pr@security | 0.210 | 否 |
| security-fix-pr | safe-upgrade-pr | 0.210 | 否 |
| security-fix-pr | semgrep-review | 0.201 | 否 |
| security-fix-pr | semgrep-review@security | 0.201 | 否 |
| security-fix-pr@security | semgrep-review@security | 0.201 | 否 |
| semgrep-review | security-fix-pr@security | 0.201 | 否 |
| dependency-audit | semgrep-review@security | 0.181 | 否 |
| semgrep-review | dependency-audit | 0.181 | 否 |
| iac-scan | security-fix-pr@security | 0.171 | 否 |
| iac-scan@posture-worker | security-fix-pr@security | 0.171 | 否 |
| security-fix-pr | iac-scan | 0.171 | 否 |
| security-fix-pr | iac-scan@posture-worker | 0.171 | 否 |
| dependency-audit | iac-scan@posture-worker | 0.158 | 否 |
| iac-scan | dependency-audit | 0.158 | 否 |
| aws-posture | secret-scan | 0.150 | 否 |
| aws-posture | secret-scan@security | 0.150 | 否 |
| aws-posture@posture-worker | secret-scan | 0.150 | 否 |
| aws-posture@posture-worker | secret-scan@security | 0.150 | 否 |
| dependency-audit | secret-scan | 0.147 | 否 |
| dependency-audit | secret-scan@security | 0.147 | 否 |
| aws-posture | semgrep-review@security | 0.137 | 否 |
| aws-posture@posture-worker | semgrep-review@security | 0.137 | 否 |
| semgrep-review | aws-posture | 0.137 | 否 |
| semgrep-review | aws-posture@posture-worker | 0.137 | 否 |
| safe-upgrade-pr | semgrep-review@security | 0.136 | 否 |
| secret-scan | security-fix-pr@security | 0.136 | 否 |
| secret-scan@security | security-fix-pr@security | 0.136 | 否 |
| security-fix-pr | secret-scan | 0.136 | 否 |
| security-fix-pr | secret-scan@security | 0.136 | 否 |
| semgrep-review | safe-upgrade-pr | 0.136 | 否 |
| aws-posture | security-fix-pr@security | 0.130 | 否 |
| aws-posture@posture-worker | security-fix-pr@security | 0.130 | 否 |
| security-fix-pr | aws-posture | 0.130 | 否 |
| security-fix-pr | aws-posture@posture-worker | 0.130 | 否 |
| dependency-audit | security-fix-pr@security | 0.120 | 否 |
| security-fix-pr | dependency-audit | 0.120 | 否 |
| safe-upgrade-pr | secret-scan | 0.119 | 否 |
| safe-upgrade-pr | secret-scan@security | 0.119 | 否 |
| aws-posture | dependency-audit | 0.115 | 否 |
| dependency-audit | aws-posture@posture-worker | 0.115 | 否 |
| iac-scan | safe-upgrade-pr | 0.110 | 否 |
| safe-upgrade-pr | iac-scan@posture-worker | 0.110 | 否 |
| aws-posture | safe-upgrade-pr | 0.109 | 否 |
| safe-upgrade-pr | aws-posture@posture-worker | 0.109 | 否 |

## 三、待核查清单（疑似重叠）

- aws-posture ↔ aws-posture@posture-worker（相似度 1.000）：只进待核查清单，不自动合并；行为层确认与合并/拆分/保留分工由人决定。
- iac-scan ↔ iac-scan@posture-worker（相似度 1.000）：只进待核查清单，不自动合并；行为层确认与合并/拆分/保留分工由人决定。
- secret-scan ↔ secret-scan@security（相似度 1.000）：只进待核查清单，不自动合并；行为层确认与合并/拆分/保留分工由人决定。
- security-fix-pr ↔ security-fix-pr@security（相似度 1.000）：只进待核查清单，不自动合并；行为层确认与合并/拆分/保留分工由人决定。
- semgrep-review ↔ semgrep-review@security（相似度 1.000）：只进待核查清单，不自动合并；行为层确认与合并/拆分/保留分工由人决定。

## 四、整改清单候选（质量门未过关）

无。质量门结论为“证据不足”的技能不在此列——证据不足不是失效，待对照跑分补测。

## 五、方法与诚实声明

- 本报告由评估脚本按评估清单自动生成；清单里的技能文本取自仓库 main 上的真实技能文件（路径见清单）。
- 质量门样本量为 0 的技能判“证据不足”：T2 只跑门逻辑与重叠检测，真实对照跑分（A/B）在后续实测试运行；不编造跑分数据。
- 评估结论只进整改清单/待核查清单；技能下线另走审批，绝不因评估未过关直接删技能。
