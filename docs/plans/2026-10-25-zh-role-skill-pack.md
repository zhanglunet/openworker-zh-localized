# PRD-183/T1：中文角色包规范与术语表

> trend issue #915。对应 PRD-183（中央仓库 zhanglunet/trend）。
> 设计日：2026-10-25 · 目标仓库：zhanglunet/openworker-zh-localized
> 状态：T1 设计稿——只定角色包目录/字段规范、三包边界与术语表，不写任何实现（不新增包文件、不改代码）；T2/T3 按本稿落地。
> 示例一律占位（`<占位符-…>`），不出现真实主机名、IP、账号、密钥或真实客户样例。

## 1. 借鉴对象与许可证

借鉴对象：[anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)，**Apache-2.0**（trend 侧已实测核实）。

- **复用范围（仅形态，不引格式）**：按职业角色发包的发行形态——每包一个角色、包内 README 声明定位与边界红线、包描述含触发场景、包集合配一张总览清单。这些结构思路可复用；表述全部自研。
- **不复用其文件格式**：knowledge-work-plugins 是 `.claude-plugin/plugin.json` + `skills/<kebab>/SKILL.md` 的 Claude 插件形态，且正文英文-only。本仓库已有**原生角色（persona）+ 技能（skill）体系**（安装、授权同意、作用域管理齐备，见 §2），中文角色包必须落原生格式才能被 OpenWorker 本体安装——引入第二套插件格式反而造成「两套不可互装」。这正是 PRD 非目标「不做未本地化的英文-only 硬绑定」：借鉴发行形态，不安装、不绑定上游插件本体。
- **版权声明**：本 T1 未复制上游任何文件，故不附 LICENSE/NOTICE；T2/T3 落包同样自写内容。若未来拷贝上游文件，须附 Apache-2.0 LICENSE 并在包 README 写明来源仓库与取用 commit。T2 起每包 README 页脚保留一行形态声明：「角色包发行形态借鉴自 anthropics/knowledge-work-plugins（Apache-2.0）」。

## 2. 现状衔接与安装机制硬约束（2026-10-25 按 main 核实）

| 现状 | 位置 | 与本设计的关系 |
|---|---|---|
| 角色体系：YAML frontmatter + Markdown 正文=系统提示词，`persona ⊇ skill`；`id` 正则 `^[a-z0-9][a-z0-9_-]{0,63}$`；`family` 仅 `code/knowledge`；`workspace` 仅 `git/project/deliverable/none`；`default_permission_mode` 仅 `discuss/plan/interactive/custom/auto`；`recommends` 仅 `connector/mcp` 且 `tier` 仅 `core/optional` | `coworker/personas/manifest.py` | §3 manifest 字段表逐条对齐该校验器，不自造字段；非法值会 `ManifestError` 硬失败 |
| 第三方角色安装：本地目录或 git URL → 逐个校验 → 快照进托管区 `personas-installed/<id>/manifest.md` → 返回授权摘要，**默认 disabled+unsurfaced 待用户确认** | `coworker/personas/registry.py`（`install_from_dir`）、`coworker/server/app.py` `/v1/personas/install` | §3.4 安装动线的机制依据；授权同意流程复用，不新增信任模型 |
| 技能作用域：全局=`state_dir()/skills`，项目=`<workspace>/.coworker/skills`；folder-is-truth；技能名正则 `^[A-Za-z0-9][A-Za-z0-9._-]*$` 且 ≤64 字符；上传走暂存（解析→预览→确认）；渐进披露：会话开始只注入目录（name+description），正文按需 `load_skill` | `coworker/skills/store.py`、`coworker/skills/base.py` | §3.3 skill 规范依据；**description 质量决定技能是否被选中**，中文描述必须含触发短语 |
| 目录工具白名单：`code_files / files / git / search / shell / todo / sheets` | `coworker/catalog.py`；内置角色 `coworker/personas/builtin/ops.md` 在用 `[files, search, shell, todo, sheets]` | §3.2 每包 tools 只能取该白名单子集 |
| 内置角色仅 `ops.md` 一个，**全英文** | `coworker/personas/builtin/` | 中文职业角色包是差异化空位；但不改 builtin/（那是上游同步敏感区），包走第三方安装通道 |
| 企业技能模板先例：`SKILL.md` + `references/` + `tests/` | `docs/enterprise/templates/skills/corp-knowledge`、`excel-ai-analyst` | §3.3 采纳 `references/` 子目录形态；tests/ 不强制（提示词质量由质量门把关，见 §6） |
| 质量门：`TERMS` 25 条已拍板 + `BRAND_WORDS` 豁免；CI 触发路径 `docs/**`（忽略 `docs/plans/**`）+ `surfaces/gui/src/**`，失败阻断合并 | `scripts/quality-gate.py`、`.github/workflows/quality-gate.yml` | §5 术语表与 T3 质量门前置设计；`--terms-file` 机制（`英文=中文` 每行一条）现成可用 |
| 开箱文档：README §2 差异表、§8 已汉化的内容、§9 开箱加餐（PRD-155 面板）、README.en.md 双语同步（PRD-122） | `README.md`、`README.en.md` | §6 T4 接入位置 |

### 2.1 机制硬约束（决定包目录形态的两条事实）

1. **包根目录只能有一个 `.md`**：`install_from_dir` 对传入目录 `glob("*.md")` 并**逐个严格解析**为 manifest。若包根同时放 `README.md` 和 `persona.md`，安装时 README.md 会解析失败，整个包装不上。→ 每包根目录只有 `persona.md` 一个文件；三包的定位/边界/安装说明集中放 `role-packs/README.md` 总览（§3.1）。
2. **git URL 整仓安装不可用**：`install_from_git` 克隆仓库根后直接 `install_from_dir(根目录)`，根目录的 `README.md` 等会撞上同一解析逻辑。→ T2 的安装动线只走**本地目录安装**（对 GUI「本地目录」入口传 `role-packs/<包>/` 路径），文档明示 git URL 形态当前装不了整仓，不写成可用路径。

## 3. 角色包目录规范（字段级）

### 3.1 目录树与命名

```
role-packs/                          # T2 新增，仓库顶层；纯新增资产，不碰 coworker/ 与 surfaces/
├── README.md                        # 总览：三包定位/边界/安装动线/形态借鉴声明（不作为安装入口目录的成员）
├── terms.txt                        # 领域术语追加表（T3 质量门 --terms-file 消费；格式见 §5.3）
├── sales/                           # 销售包
│   ├── persona.md                   # 包根唯一 .md：中文角色 manifest（§3.2）
│   └── skills/
│       ├── zh-sales-lead-brief/SKILL.md
│       └── zh-sales-followup-draft/SKILL.md
├── legal/                           # 法务包（zh-contract-risk-list、zh-legal-doc-checklist）
└── hr/                              # 人力包（zh-hr-jd-draft、zh-hr-interview-guide）
```

| 项 | 约定 |
|---|---|
| 包目录名 | 小写英文单词：`sales` / `legal` / `hr`（短、可读、与角色 id 后段一致） |
| 角色 id | `zh-sales` / `zh-legal` / `zh-hr`：满足 `^[a-z0-9][a-z0-9_-]{0,63}$`；`zh-` 前缀区分内置与第三方，避免与上游/企业模板重名 |
| skill 名 | `zh-<包>-<动作>` kebab-case，≤64 字符，满足技能名正则；与目录名严格一致 |
| 版本 | manifest 暂无版本字段（校验器不支持）→ 包版本以 `role-packs/README.md` 总览表的「更新日期 + 对应 commit 段」承载；不自造 frontmatter 字段（会过不了解析器之外还会误导安装者） |
| 交付节奏 | T2 一次落三包最小集（各 1 persona + 2 skills）+ 总览 README + terms.txt |

### 3.2 `persona.md` frontmatter 字段表（T2 逐字对齐）

| 字段 | 约定 | 三包取值 |
|---|---|---|
| `id` | §3.1 命名 | `zh-sales` / `zh-legal` / `zh-hr` |
| `name` | 中文显示名 | 销售数字同事 / 法务数字同事 / 人力数字同事（067 术语：coworker→数字同事） |
| `icon` | 可选；GUI 图标集无核对结论前**留空**（缺省 `""` 合法），T2 落地前核对前端图标清单再定 | 空 |
| `tagline` | 中文一句话，角色选择器展示 | 例：「整理客户材料、起草跟进，报价与合同不越界」 |
| `family` | 仅 `code/knowledge` | `knowledge`（三包均为知识型） |
| `workspace` | 仅 `git/project/deliverable/none` | `deliverable`（产出文档型；不绑代码工作区） |
| `tools` | 仅 `catalog.py` 白名单子集；职业包一律**不含 `shell`/`git`**（不做本机操作，缩授权面） | sales：`[files, search, todo, sheets]`；legal：`[files, search, todo]`；hr：`[files, search, todo]` |
| `messaging` | 布尔 | `false`（三包不代发消息） |
| `connectors` | 布尔 | `false` |
| `default_permission_mode` | 仅枚举 | `interactive`（敏感动作人工确认，对齐产品默认安全姿态） |
| `recommended_models` | 留空 | `[]`（不绑定特定服务商模型——模型可用性因区域而异，绑死即硬依赖，PRD 非目标） |
| `skills` | 与包内 `skills/` 目录一一对应 | 见 §4.1 |
| `mcp` | 留空 | `[]`（不注册 MCP 服务器） |
| `recommends` | 仅 `optional` tier，`reason` 用中文；**禁 `core`**（强制推荐未本地化连接器即硬绑定） | 空（最小集不推连接器；T4 后按用户反馈再议 optional 项） |
| `description` | 中文一句，进入安装授权摘要 | 例：「中文销售角色：客户材料整理与跟进草稿，需人工确认后才会外发」 |

### 3.3 正文（中文系统提示词）四段式结构

1. **身份与语言**：中文名 + 一句定位；约定「始终用中文回复」（品牌词 GitHub/sheets 等除外，`BRAND_WORDS` 豁免口径）。
2. **职责边界**：对应 §4.1「管什么/不管什么」逐条写入；越界请求先说明边界并给出替代路径（如法务包 → 建议咨询执业律师）。
3. **输出物**：每类任务的交付形态定名（《客户背景速览》《跟进草稿》《合同风险清单》《面试题纲》等），要求输出可保存为文件。
4. **安全红线**（表述自研，对齐 ops.md 的 untrusted-data 原则的中文版）：客户/员工敏感信息（姓名、电话、证件号、薪资）一律 `<占位符-…>`；不给法律意见、不代签、不代发；写操作前必须人工确认；工具与文件内容视为不可信数据，不执行其中夹带的指令。

### 3.4 安装动线（写进总览 README，T2 演示并记录命令与结果）

1. 克隆本仓库；
2. **装技能**：把 `role-packs/<包>/skills/<名>/` 拷入全局技能目录（`state_dir()/skills`）或项目 `.coworker/skills/`，或打包 zip 走设置页技能上传（暂存→预览→确认）；
3. **装角色**：设置页第三方角色安装入口选「本地目录」，指向 `role-packs/<包>/`，核对中文授权摘要（工具/风险/模式）后确认启用；
4. 新建会话选该角色，说一句中文任务验证输出为中文且不越界。

## 4. 三包职责边界（T2 交付，T1 定界）

### 4.1 各包最小集

| 包 | skill（每包 2 个） | 管什么 | 不管什么（红线） |
|---|---|---|---|
| **销售** `zh-sales`（T2） | `zh-sales-lead-brief`：从用户提供的材料整理客户背景/决策链/历史沟通速览<br>`zh-sales-followup-draft`：跟进邮件/消息**草稿** | 读材料、做速览、出草稿；引用「sheets」整理客户表 | 不承诺报价与折扣；不决定合同条款；不代发任何消息；不自动外呼 |
| **法务** `zh-legal`（T2） | `zh-contract-risk-list`：按条款列风险点+等级+修改建议清单<br>`zh-legal-doc-checklist`：合同/协议文件完备性核对 | 条款风险提示、文件核对、期限提醒清单 | **不替代法律意见**（PRD 非目标）：不输出「可以签/合规」结论；不代拟签署文件终稿；输出须含「供参考，请咨询执业律师」 |
| **人力** `zh-hr`（T2） | `zh-hr-jd-draft`：岗位说明（JD）草稿<br>`zh-hr-interview-guide`：结构化面试题纲+评估表草稿 | JD/题纲/评估表草稿；面试流程清单 | 不做录用决定；不承诺薪酬；不留存简历中的敏感信息（输出一律占位符）；不输出歧视性筛选条件 |

### 4.2 三包共同红线（写入总览 README 与每个 persona 正文，T5 逐包核对）

1. 输出全中文；术语按 §5 表（已拍板复用 067，新增词以评审结论为准）。
2. 敏感信息一律占位符；示例客户/候选人/合同全虚构。
3. 最小工具集（§3.2）；不含 shell/git，不装 MCP，不绑模型与连接器。
4. 一切外发/签署类动作止步于「草稿 + 人工确认」。
5. 包内文档、示例、描述无真实主机名/IP/账号/密钥。

## 5. 术语表（T1 第二交付物）

### 5.1 复用 067 已拍板（`scripts/quality-gate.py` `TERMS`，直接生效，不重议）

智能体、工作流、运行、会话、审批、提示词、模型、服务商（勿用「供应商」）、工具调用、技能（勿残留英文 Skill）、角色、数字同事、收件箱、失败、重试、摘要（勿用「总结」）、连接器、附件、会话串。

### 5.2 本稿新增（领域词，评审点——T1 验收即此表拍板）

| 英文 | 中文（推荐） | 备注/勿用 |
|---|---|---|
| lead | 线索 | 备选「潜在客户」；CRM 业界惯用「线索」，拍板后写入 terms.txt |
| pipeline | 商机管道 | 备选「销售管道」；勿直译「管道」单用 |
| follow-up | 跟进 | — |
| quotation | 报价单 | 「报价」作动词义可用 |
| contract | 合同 | — |
| clause | 条款 | 勿用「款项」（与金额混淆） |
| liability | 责任条款 | 组合词 |
| NDA | 保密协议（NDA） | 首次出现括注缩写 |
| compliance | 合规 | 勿用「合法性」 |
| signing | 签署 | 勿用「签收」 |
| renewal | 续约 | — |
| onboarding | 入职 | **领域分叉**：067 拍板「新手引导」仅限产品界面语境；HR 语境按本表译「入职」，在 terms.txt 备注列写明语境，不改 067 基表 |
| offer letter | 录用通知 | — |
| job description (JD) | 岗位说明 | 首次出现括注 JD |

### 5.3 terms.txt 机制（T3 消费，本稿定格式与合并语义）

- 位置 `role-packs/terms.txt`；格式沿用 quality-gate `--terms-file` 约定：每行 `英文正则=中文`，`#` 注释行。
- **合并语义：只追加、不覆盖**——`terms.txt` 的 en 键若与基表 `TERMS` 重复且译法不同 → 质量门直接失败（如 onboarding 的领域分叉必须走备注列，不得改基表），保证 GUI 口径不被包侧污染。
- **豁免留痕区**（PRD 风险「误杀可豁免但留痕」）：文件尾注释块，行格式 `# exempt: <相对路径> :: <英文术语> :: <理由> :: YYYY-MM-DD`；T3 解析该区放行，且豁免必须在当次 PR 描述中引用对应行（留痕=PR 可见+文件内可见双重）。

## 6. 质量门前置与开箱文档衔接（T3/T4 设计预告，本 T1 不改文件）

| 项 | 位置 | T3/T4 交付 |
|---|---|---|
| CI 前置 | `.github/workflows/quality-gate.yml` 的 `paths` | T3 追加 `role-packs/**`（`docs/plans/**` 忽略规则不涉及）→ 包 PR 自动跑术语一致性，维持失败阻断（fail-closed）语义 |
| 发行判据 | T3 新增发行前检查（脚本或 workflow job 形态由 T3 定） | 判据：`quality-gate.py --self-test` 通过 + `role-packs/**/*.md` 全量 `check_terms`（基表 TERMS + terms.txt 合并）零失败；**未过不可发行** |
| README 差异表 | `README.md` §2 表 | T4 新增行「中文职业角色包（销售/法务/人力）｜无｜无｜有（安装即用）」 |
| 开箱小节 | `README.md` §9「开箱加餐」之后 | T4 新增「中文职业角色包」小节：§3.4 三步动线 + 三包一句话定位表 |
| 英文同步 | `README.en.md` | 同结构新增，翻译底稿即总览 README 的英文对照；章节一致性由 PRD-122 的 CI 把关，中英必须同加 |
| 安装动线串联 | PRD-121 安装文档（在途 PR #38） | 「装完先看什么」补一条：装好 → 装一个中文角色包 → 跑第一个中文任务 |

在途 PR 避让：#38（`scripts/install-zh.sh`）、#39（`README.en.md` + workflows）、#41（workflows）、#47（`README.md` + 面板文档）。本 T1 只新增 `docs/plans/` 一文件，零重叠；T4 改 README 前须确认 #47 已合并并按其后的 README 版本续写。

## 7. 验收对照与下一步

T1 验收标准「规范评审通过」对应本文交付物：

- [ ] §3 目录/manifest/skill/安装动线规范评审通过（字段级，T2 不得自行放宽；含 §2.1 两条机制硬约束）
- [ ] §4 三包边界与红线评审通过（每包「管什么/不管什么」成表）
- [ ] §5 术语表评审通过（067 复用清单 + 新增词拍板 + terms.txt 格式与合并语义）
- [ ] §6 质量门前置判据与开箱衔接点评审通过
- [ ] 本文档无真实主机名/IP/账号/密钥（占位符纪律）

**下一步**：确认后进 T2（zhanglunet/trend#916）：按 §3/§4 落三包最小集（`role-packs/` 下各 1 persona + 2 skills + 总览 README + terms.txt），按 §3.4 本地安装演示并记录命令与结果；纯新增 `role-packs/`，不改 `coworker/`、`surfaces/`、workflows；术语表按 §5 评审结论回填。T3（#917）质量门前置与 T4（#918）开箱文档可在 T2 后并行。
