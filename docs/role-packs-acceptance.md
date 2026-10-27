# 中文职业角色包 T5 验收记录（PRD-183/T5，trend #919）

> 验收日期：2026-10-26（T5 分支 `trend/prd-183-t5-acceptance`）
> 验收对象：T2 三包最小集（PR #50/#52）+ T3 发行门（PR #54 已含）+ T4 开箱指南（PR #54 已含）
> 验收标准（PRD-183 T5 行）：**三包演示；质量门报告齐全；无密钥**
> 验收形态：按开箱指南 `docs/role-packs-onboarding.md` 真实走一遍（安装 → 触发 → 质量门），
> 全程只走产品真实代码路径；自动化验收测试 `tests/test_role_packs_acceptance_t5.py`（10 例）钉住可重放。

## 结论

**通过。** 三包（hr / legal / sales）按开箱指南动线走通「取包 → 安装 → 验证 → 迭代/卸载 → 发版前门」全链路；
发行门报告要素齐全、结论「可发行」；角色包与开箱指南、验收记录密钥/内网扫描零命中。
走查发现开箱指南 3 处文档问题（见「勘误与收尾」），已随本 PR 修复。

## 三包演示（开箱指南 5 步 × 实测）

走查环境：本仓库工作副本；角色安装与技能拷入均落在系统临时目录的独立状态区
（`PersonaRegistry` 状态文件与技能目录都指向临时目录），
不触碰真实用户状态目录；质量门直接对本仓库真实运行。

| 指南步骤 | 操作（真实代码路径） | 实测结果 |
|---|---|---|
| 1. 取包 | 核对包根硬约束：`role-packs/<pack>/` 根仅 `persona.md` 一个 `.md`（`install_from_dir` 严格解析约束） | 通过：hr / legal / sales 三包均只有 `persona.md`，成员技能各 2 个，共 6 个 |
| 2. 安装 | `PersonaRegistry.install_from_dir(<仓库>/role-packs/<pack>)`（本地目录动线）+ 包内技能整目录拷入全局技能目录（`role-packs/README.md` 安装动线第 2 步） | 通过：三包授权摘要为中文（人力数字同事 / 法务数字同事 / 销售数字同事）；工具最小集 `[files, search, todo(, sheets)]`，`mcp=[]`、`messaging=False`、风险面仅 `read/write_local`；三包均默认 `enabled=False`、`surfaced=False`（等用户确认，不自动启用）；快照进托管区且可重新解析 |
| 3. 验证 | 技能列表（`SkillLoader` 目录发现 + `skill_catalog_text`）→ 用户确认启用（`set_enabled`，核对中文授权摘要后）→ 逐包触发一次角色技能 | 通过：6 个技能全部出现在技能列表，中文 description 均含触发话术；启用后三角色出现在新建会话选择器，persona 中文提示词生效（正文 680–713 字，含「始终用中文回复」）；触发走 `load_skill` 真实工具路径，三次调用均返回中文指令（540–585 字），正文含「红线 / 占位符 / 不可信数据」：hr「帮我写个 JD」→ `zh-hr-jd-draft`；legal「看看这份合同有什么风险」→ `zh-contract-risk-list`；sales「做个客户速览」→ `zh-sales-lead-brief` |
| 4. 迭代/卸载 | `PersonaRegistry.uninstall("zh-legal")`；删除技能目录后 `rescan` | 通过：zh-legal 从选择器消失、托管区快照被清除；`zh-contract-risk-list` 从技能列表消失 |
| 5. 发版前门 | 对本仓库真实运行 `python3 scripts/release-gate-role-packs.py` | 通过：退出码 0，结论「可发行」（报告全文见下节） |

## 质量门报告齐全（验收标准第二条）

三份报告本次验收全部真实运行、结论如下：

1. **质量门自测**（`python3 scripts/quality-gate.py --self-test`）：**20 通过 / 0 失败（共 20 项）**——
   漏翻检查 / 术语一致性 / 模板完整性 / 方案 B 口径四类检查的正反用例齐全，含「测试能失败」验证（门本身没坏）。
2. **发行门**（`python3 scripts/release-gate-role-packs.py`，PRD-183/T3 交付）：
   - `== 判据 1/2：quality-gate 自测 ==` → 通过；
   - `== 判据 2/2：role-packs/**/*.md 全量术语一致性（基表 25 条 + terms.txt 追加 13 条）==`
     → `扫描文件 10 个`，`发行门：自测通过；术语失败 0（放行 0）；错误 0；警告 0`，**结论：可发行**；
   - 报告要素（两条判据标题、自测结论、全量扫描口径、失败/放行/错误/警告计数、发行结论）由
     `tests/test_role_packs_acceptance_t5.py::TestQualityGateReports` 钉住；
   - **fail-closed 反向验证**：向拷贝副本注入一处服务商术语的勿用译法后，发行门退出码 1、结论「未过不可发行」——门能拒绝（同文件钉住）。
3. **发行门覆盖范围披露（诚实口径）**：`quality-gate.py --root` 只收集 `surfaces/gui/src` 与 `docs/`，
   不覆盖 `role-packs/`；对 role-packs 的术语把关**唯一有效入口是发行门**（其自行 `rglob` 全量收集）。
   本次对全仓跑 `--root` 得 33 处术语失败，逐文件核对全部落在企业版文档、上游对照文档与 GUI 源码等
   **既有遗留**（main 上同样失败），无一处在 `role-packs/`、开箱指南或本验收记录——不属本 PRD 质量门范围，
   如实留档不掩盖。开箱指南原文推荐的 `--terms-file` 单参数命令实为空扫（不收集任何文件），已随本 PR 勘误（见下）。

## 无密钥（验收标准第三条）

- 扫描范围：`role-packs/**/*.md`（10 个）+ `role-packs/terms.txt` + 开箱指南 + 本验收记录，逐行扫描；
- 扫描口径：英文密钥/凭据字样（通用密钥词、私有密钥块标记、常见令牌前缀形态）、令牌赋值形态、
  IPv4 字面量、内网域名后缀形态、邮箱形态账号——
  **零命中**（`tests/test_role_packs_acceptance_t5.py` 的无密钥两例钉住，随 CI 常态把关）；
- 角色包内容纪律核对：三包 persona 正文与 6 个技能正文均含「占位符 / 不可信数据」红线段；
  示例客户、候选人、合同全虚构；`role-packs/README.md` 明文红线「文档与示例无真实主机名 / IP / 账号 / 密钥」在场。

## 勘误与收尾（走查发现 → 本 PR 修复）

1. **开箱指南步骤 2 缺技能安装动线**：原文写「本地目录安装入口指向 `role-packs/<pack>`……装完在技能列表
   确认出现包内技能」，但 `install_from_dir` 只装角色本体、不装包内技能——照做技能不会出现。
   已补上技能动线（整目录拷入全局技能目录 / 项目目录 / zip 上传三选一，与 `role-packs/README.md` 对齐）。
2. **开箱指南步骤 3 引用不存在的技能**：原文写「触发一次角色技能（如 hr 的入职清单）」，hr 包实际成员是
   《岗位说明（JD）》草稿与《面试题纲》。已改为 JD 草稿并附真实触发话术「帮我写个 JD」。
3. **开箱指南步骤 3 推荐的空扫命令**：原文推荐 `quality-gate.py --terms-file <术语表>` 自查，
   实测该命令不收集任何文件、恒过（`--root role-packs` 同样空扫，见上节披露）。已改为指向发行门
   `release-gate-role-packs.py`，并注明 `--root` 不覆盖 role-packs/ 的口径。

## 测试

- 自动化验收（本 PR 新增）：`.venv` 下 `pytest tests/test_role_packs_acceptance_t5.py -q` → **10 passed**
  （三包演示 4 例：安装/技能列表/启用后触发/迭代卸载；质量门 3 例：自测、发行门报告齐全、fail-closed 反向；
  无密钥 2 例；文档术语 1 例）。
- 既有回归：`tests/test_role_packs.py`（T2 门）、`tests/test_release_gate_role_packs.py`（T3 门）、
  `tests/test_role_packs_onboarding.py`（T4 门）、`tests/test_build_in_public_docs.py`、
  `tests/test_build_in_public_bilingual.py` → **53 passed**。
- 全量：`.venv` 下 `pytest tests -q` → **1539 passed, 4 skipped, 2 failed**；2 例失败
  （`test_cli_bridge.py::test_environment_is_not_inherited_wholesale`、
  `test_shell_i18n_hazards.py::test_no_bare_variable_immediately_before_a_wide_character[.github/workflows/upstream-weekly.yml]`）
  为 main 上预存的环境相关失败（PRD-155/T5 验收记录同口径在案），且后者属在途 PR #41（在途 workflow 改动）
  的修复域，本 PR 未触碰其文件。
- 本 PR 仅改文档与测试，不触碰生产代码（`coworker/`、`scripts/`、`surfaces/` 零改动）。

## 偏差披露

- 「触发」的验收口径：走 `load_skill` 真实工具路径 + 技能列表中文话术在场的确定性断言；
  未接真实大模型对话（提示词组装与模型选技能属上游引擎行为，不属三包交付物）。
  persona 侧以「启用后进入选择器 + 中文 system prompt 在场」为生效判据。
- 演示状态（安装/启用/卸载）全部落在系统临时目录的独立状态区，未写入真实用户状态目录；
  发行门与全仓扫描对本仓库真实文件运行。
