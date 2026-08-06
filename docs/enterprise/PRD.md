# OpenWorker 企业定制版 · 产品需求文档（PRD）

- 版本：v1.0（开发前准备版）
- 日期：2026-08-04
- 基线仓库：[zhanglunet/openworker-zh-localized](https://github.com/zhanglunet/openworker-zh-localized)（汉化版）
- 上游仓库：[andrewyng/openworker](https://github.com/andrewyng/openworker)
- 配套文档：[开发计划](DEV_PLAN.md) · [三仓同步方案](UPSTREAM_SYNC.md) · [部署步骤](DEPLOYMENT.md) · [换肤与打包](BRANDING_PACKAGING.md)

---

## 1. 背景与目标

### 1.1 背景

OpenWorker 是本地优先（local-first）的开源 AI Agent 桌面应用：Python 后端（`coworker/`）驱动 model-tool 循环，React + Tauri 前端（`surfaces/gui/`）提供桌面工作台，敏感数据全部留在本机。汉化版已完成界面中文化、macOS DMG 分发、中文站 oaosf.cn 与上游每日自动同步。

企业在此基础上需要一个**企业定制版**：植入企业技能与知识库、接入企业内部系统与 CLI、使用企业私有部署的大模型、内置专属办公工具（如「大表哥」表格助手）、换企业品牌皮肤、面向 macOS（Apple Silicon / Intel）与 Windows 打包分发，并且**持续跟进上游更新而不丢失定制**。

### 1.2 目标

| # | 目标 | 衡量标准 |
|---|------|---------|
| G1 | 企业员工开箱即用：安装包内置企业模型、技能、知识库配置 | 新员工 10 分钟内完成安装并跑通首个任务 |
| G2 | 数据不出内网：模型调用、知识库、审计日志全部走企业内网 | 网络抓包无海外/公网模型流量 |
| G3 | 专属功能落地：「大表哥」表格助手可在桌面端直接使用 | 上传表格 → 结构分析报告全流程可用 |
| G4 | 可持续演进：上游/汉化版更新能在 1 周内合入企业版 | 每次同步的人工冲突处理 ≤ 2 小时 |
| G5 | 多平台覆盖：macOS（arm64/x86_64）+ Windows 安装包与自动更新 | 三平台安装包均可自动更新到企业更新源 |

### 1.3 非目标（本期不做）

- 不做多租户 SaaS 化改造（保持 local-first 架构）
- 不做移动端
- 不重写上游核心引擎（TurnEngine、Provider 路由等只做配置层与插件层定制，不动核心逻辑，以降低同步冲突面）
- 不做 Linux 桌面包（后端天然支持，桌面包待需求明确后追加）

---

## 2. 用户与场景

| 角色 | 场景 |
|------|------|
| 普通员工 | 用中文界面完成日常任务：写文档、处理表格（大表哥）、查企业知识库、发起内部系统操作 |
| 业务骨干 | 用企业技能包沉淀的 SOP（如报销审核、周报汇总）批量处理工作 |
| IT 管理员 | 统一配置模型端点、连接器白名单、技能包版本；查看审计日志 |
| 安全合规 | 审计工具调用记录，确认数据不出内网，管控高危操作审批 |
| 定制开发团队 | 维护企业版仓库，跟进上游同步，开发企业连接器/技能/皮肤 |

---

## 3. 定制能力全景

下表是企业可定制面的完整清单，均基于对现有源码的扩展点分析（详见 [oaosf.cn/source-analysis](https://oaosf.cn/source-analysis) 与 `docs/analysis/`）。定制分三档：**配置级**（改配置即可）、**资产级**（放置文件/资源即可）、**代码级**（需要开发）。

### 3.1 模型层：私有模型 / 端口 / 版本（配置级为主）

现状：`coworker/providers/registry.py` 以「描述符注册表 + 前缀路由」支持 19 个 Provider——OpenAI、Anthropic、Gemini、Bedrock、Vertex、**Ollama**（`_build_ollama`，免 Key，内网地址端口可配）、**Custom（OpenAI 兼容自定义端点）**（`_build_custom`：`base_url` + `api_key` + 模型名，GUI 有「获取模型」「测试连接」），以及 12 个经 `_compat()` 工厂声明的 OpenAI 兼容厂商（DeepSeek、Kimi、Qwen、阶跃星辰 StepFun 等）。模型按 `provider:model` 前缀路由（如 `custom:qwen3-72b`），凭据存 `<state-dir>/secrets.json`（0600，支持 `${ENV_VAR}` 引用）。

> ⚠️ 两个必须写进企业规范的事实：① 模型 id **必须带前缀**（`custom:`/`ollama:`），裸名会静默路由到默认 openai provider；② 能力矩阵 `matrix.py` 未登记的模型会被 `capabilities.py` 保守启发式降级（并行工具调用/视觉默认关），企业模型入矩阵是必改项。

企业定制需求：

| 需求 | 实现路径 | 档位 |
|------|---------|------|
| 接入企业私有模型（vLLM / Ollama / 企业网关，自定义 host:port） | Custom Provider 配 `base_url`（如 `http://llm.corp.example:8000/v1`）；或 Ollama Provider 配本地/内网地址 | 配置级 |
| 指定模型版本与默认模型 | `config.toml` 的 `model` 键 + Provider profile 中的模型名 | 配置级 |
| 预置企业 Provider（员工不需手工填端点） | 安装包内预置 `~/.config/coworker/config.toml` 模板或首启引导写入；或在 registry 中新增企业 Provider 描述符（名称、图标、默认端点） | 资产级/代码级 |
| 模型能力声明（上下文窗口、工具调用、多模态） | ✅ **已交付**：`<state-dir>/models.json` 本地声明覆盖层，不必改代码；能力用 [templates/verify-private-model.py](templates/verify-private-model.py) 对真实端点实测得出 | 配置级 |
| 禁用海外模型入口 | 定制 Provider 目录：企业构建里只暴露白名单 Provider | 代码级（小） |

### 3.2 技能层：企业技能包（资产级）

现状：`coworker/skills/` 实现了 Anthropic SKILL.md 规范（YAML frontmatter：`name`、`description`、`allowed-tools` + 指令正文 + 资源目录），渐进式加载（会话中只注入目录，按需 `load_skill`）。技能目录两级：

- 全局技能：`state_dir()/skills`（用户态，随应用状态目录）
- 工作区技能：`<workspace>/.coworker/skills`（项目级，优先随项目走）

企业定制需求：

| 需求 | 实现路径 | 档位 |
|------|---------|------|
| 预置企业技能包（如报销 SOP、周报模板、公文写作、**excel-ai-analyst 大表哥**） | ✅**已交付**：`provisioning.py` 首启把 `defaults/skills/<name>/` 逐个种进 `state_dir()/skills`——技能终于有了随安装包下发的正规通道；也可 IT 下发或走 REST 批量导入 | 资产级 |
| 技能包版本管理与更新 | 企业技能包独立 git 仓库 + 定时同步（可用 automation 定时任务或 IT 分发）；业务仓库级技能放 `<workspace>/.coworker/skills` 随 git 分发 | 资产级 |
| 技能白名单管控 | `skills-settings.json`（`state_dir()` 下）+ SkillLoader 的 allowed 回调已支持启停 | 配置级 |

注意三条约束（来自 `coworker/skills/store.py` 实测）：① 技能文件夹名仅限 ASCII（`^[A-Za-z0-9][A-Za-z0-9._-]*$`），中文放 description；② 项目级技能会**同名遮蔽**全局技能——企业预置技能存在被工作区仓库"技能投毒"替换的面，需要在冒烟测试或第三只读 scope（代码级小改）中防护；③ 禁用是个人状态（any-off-wins），当前无"强制启用企业技能"机制，如需管控属代码级小改。

### 3.3 知识层：企业知识库（资产级 + 代码级可选）

现状：无内置向量 RAG（全仓无 embedding/向量库代码）。知识接入的现实路径按成本从低到高：

1. **企业规范注入（零代码）**：`<state-dir>/AGENTS.md`（全局）+ 项目根 `AGENTS.md`——`coworker/project.py` 自动把它们注入每个会话的 system prompt，适合放企业写作规范、术语表、合规红线；
2. **文件根挂载**：`coworker/roots.py` 的 RootDir 机制 + `SessionManager.add_root()`（可运行中追加、可只读、持久化到会话）——把企业知识库目录（同步盘）挂给 agent 直接读；
3. **技能内置知识**：把结构化知识（制度、FAQ、模板）做成技能资源目录，`load_skill` 按需取用；
4. **记忆系统**：`coworker/memory/`（SQLite `<data-dir>/coworker.db`，global/workspace 两级作用域**全量注入** system prompt）——可预置少量"企业事实"，条数需克制；后端是 MemoryStore 抽象，可换企业集中存储（替换点仅 2 处）；
5. **预置企业角色**：`coworker/personas/builtin/` 加企业 persona（frontmatter + system prompt 的 .md），并设为默认角色；
6. **MCP 知识服务**（推荐中期方案）：企业已有知识库系统（Confluence/语雀/自建 RAG）封装成 MCP server，通过 `<state-dir>/mcp.json` 注册，agent 以工具调用检索——**知识库不进仓库、不进安装包，权限留在知识库侧**。

> 大知识库不要塞记忆表（全量注入会线性吃掉上下文并提前触发压缩）——用目录挂载或检索型 MCP。

### 3.4 工具与连接器层：企业系统 / CLI / MCP（代码级 + 配置级）

现状：`coworker/connectors/` 内置 25+ 连接器（声明式 descriptor + 工具定义），`coworker/mcp/` 支持注册外部 MCP server，`coworker/cli.py` 提供命令行入口，凭据由 `coworker/secrets.py` 管理。

| 需求 | 实现路径 | 档位 |
|------|---------|------|
| 企业内部系统连接器（OA/ERP/工单/HR） | 参照 `connectors/descriptors.py` 的 ConnectorDescriptor 纯数据声明 + `tool_defs.py` 工具目录（read 类工具免审批、write 类默认审批）；企业连接器仿 `connectors/experimental/` 子包模式独立分包，经 `register_descriptor` 注册，把同步冲突面压到最小 | 代码级 |
| 企业 CLI 工具接入 | 首选 MCP：把企业 CLI 封装成 stdio MCP server，写入 `<state-dir>/mcp.json`（标准 mcpServers 格式，支持 `${VAR}` 引用、`include_tools` 白名单、`requires_approval`）——零代码；次选 `allowed_commands` 白名单直接放行 CLI 命令 | 配置级/资产级 |
| 连接器目录定制（隐藏海外 SaaS，只留企业白名单） | DESCRIPTORS 为 Python 硬编码、无外置配置——直接删条目会与上游持续冲突，应加**过滤层**（在 `connector_list()` 出口按企业白名单过滤，或构建期开关），属挂载点小改 | 代码级（小） |
| 命令审批策略 | `config.toml`：`allowed_commands`、`auto_allow`、`mode`（plan/interactive/auto/custom）；受信任工作区（`workspace_trust.json`）才加载仓库级配置 | 配置级 |
| 企业 IM 双向接入（钉钉/飞书类） | 实现 `connectors/base.py` 的 BasePlatformAdapter 子类 + `adapters.py`/`config.py` 挂载（现有入站平台为 telegram/slack/github 硬编码元组） | 代码级（高，P3 备选） |

### 3.5 专属功能：「大表哥」表格助手（资产级 + 代码级）

「大表哥（excel-ai-analyst）」（[anp.asia](https://anp.asia)）把含公式的业务 Excel 当作无文档的遗留代码做逆向工程：六步法 = ①探测表型/表头/输入输出列/真实公式（浏览器本地、零上传）→ ②结构化转 MD → ③字段本体 → ④公式链与数据血缘 → ⑤全量真实数据逐行回算验证 → ⑥交付看板与 What-If。Step 0 免 AI 纯本地，后续步骤需要 AI 参与。

企业版集成分三层，逐层加深：

底座事实（决定集成设计）：后端 `coworker/tools/` 目前**没有任何表格处理工具**（能力目录仅 code_files/files/git/search/shell/todo 六项）；**聊天附件管线只接受 image/pdf/text（`coworker/attachments.py`），拖拽上传 xlsx 无法进入模型上下文**；GUI 仅把 .xlsx 产物归类为 sheet 做预览。因此大表哥的表格必须以**工作区文件**形态交给 agent（文件根/会话草稿目录），由技能指挥 shell/python 调 `excel_ai.py` 处理——这恰好也是数据不出本机的路径。

| 层 | 内容 | 档位 |
|----|------|------|
| L1 技能层 ✅**已交付** | 预置 `excel-ai-analyst` 技能（SKILL.md + `excel_ai.py` 脚本资源），员工对话里说"分析这个表"即触发五步法；表格文件放工作区或由技能引导指定路径。见 [templates/skills/excel-ai-analyst/](templates/skills/excel-ai-analyst/) | 资产级 |
| L2 入口层 ✅**已交付** | 会话空状态新增「读懂一张业务表格」任务卡（`surfaces/gui/src/components/SessionIntro.tsx`），点击预填五步法提示词。**仅当 `excel-ai-analyst` 技能对本会话可用时才渲染**——没装技能的用户界面完全不变，不会出现点了没反应的死入口；缺共享目录时降级为引导选择文件夹。如需"拖拽上传即分析"，须同步扩展 `attachments.py` 接受表格类型（挂载点小改） | 代码级（中） |
| L3 工具层 ✅**已交付** | 引擎 vendored 到 `coworker/sheets/`，`coworker/tools/sheets.py` 提供四个工具（`sheet_to_markdown` / `sheet_verify` / `sheet_result_xlsx` / `sheet_analyze`），在 `catalog.py` 登记为 `sheets` capability。相比技能走 shell 的路子多三点：**不必每步弹审批**（WRITE_LOCAL 而非 EXEC）、**冻结的 sidecar 里也能跑**（桌面版没有 python3 可 shell 出去）、**读路径按会话根目录校验**（含 spec.json 里点名的 workbook）。pandas/openpyxl 是可选 extra，未安装时能力整个跳过，默认安装零成本 | 代码级（中） |

验收：员工把一个 20MB 内多 Sheet 的 xlsx 拖入桌面端，得到结构探测 + 公式链 + 全量验证报告（MD/网页），全程数据不出本机/内网。

### 3.6 品牌层：皮肤 / 名称 / 图标（资产级）

现状：前端 Tailwind（`surfaces/gui/tailwind.config.js` + 全局 CSS）、桌面壳品牌集中在 `surfaces/gui/src-tauri/tauri.conf.json`（`productName`、`identifier`、`bundle.icon`、`publisher`）与 `Info.plist`。中文文案为源码内直接中文化（无 i18n 资源层），改文案 = 改组件文案。

详细方案见 [BRANDING_PACKAGING.md](BRANDING_PACKAGING.md)。要点：主题色/暗色模式集中到 CSS 变量层做"企业主题包"；应用名、Bundle ID（如 `com.<corp>.openworker`）、图标、DMG 背景、更新源全部品牌化；品牌资产集中放置以隔离同步冲突。

### 3.7 安全与合规（配置级 + 代码级小改）

- 权限与审批：`coworker/permissions.py` + `risk.py` 已有分级审批（工具按 read/write_local/exec/external 四类风险；discuss/plan/interactive/auto/custom 五种模式；命令前缀白名单且含 shell 元字符一律强制审批）；企业策略通过 `config.toml`（`mode`、`allowed_commands`、`auto_allow`）统一下发
- 审计：每个工具调用的 proposed→approval→finished 全阶段经 `audit_sink` 写入 `<state-dir>/coworker.db` 的 audit_events 表（`coworker/audit.py`）；**外发 SIEM 已交付**（`audit_forward_url` 等四个配置项）——后台线程、有界队列丢旧留新、失败开放，本地日志始终是事实来源
- 凭据：`coworker/secrets.py` 本机存储；企业密钥不进仓库、不进安装包
- 网络边界：企业构建默认只配置内网模型端点；云中转（`cloud_base_url`，默认 `https://api.openworker.com`，仅 OAuth 中转）在企业版中禁用或替换为企业网关
- 更新安全：Tauri updater 签名公钥替换为企业自持密钥，更新源指向企业内网/私有 GitHub

### 3.8 发布层：私有仓 / 企业站 / 安装包 / 自动更新

- 私有仓：`<corp>/openworker-enterprise`（私有），三仓同步策略见 [UPSTREAM_SYNC.md](UPSTREAM_SYNC.md)
- 企业站：复制 `website/`（vinext + Cloudflare Workers；内网可改静态托管/Node 部署）为企业介绍站 + 下载页 + 更新日志
- 安装包：macOS `.dmg`（aarch64 + x86_64，`packaging/build_dmg.sh` + `release.yml` 矩阵已支持双芯片）、Windows `.msi` + NSIS `.exe`（`packaging/build_windows.ps1` + `build-windows.yml`）
- 自动更新：`latest-zh.json` 清单机制改为企业更新源 `latest-<corp>.json`，由企业发布流水线生成

---

## 4. 功能需求清单（按优先级）

| ID | 需求 | 优先级 | 档位 | 验收标准 |
|----|------|--------|------|---------|
| F1 | 私有模型接入：Custom/Ollama Provider 预置企业端点、端口、模型版本 | P0 | 配置级 | 断网（仅内网）环境完成一次完整对话 + 工具调用 |
| F2 | 企业配置预置：安装包首启写入默认 `config.toml`（模型、审批策略、命令白名单） ✅**已交付** —— `coworker/provisioning.py` 首启种入 config.toml / models.json / mcp.json / AGENTS.md / skills，不覆盖、不复活、不致命 | P0 | 资产级 | 全新机器安装后零配置可用 |
| F3 | 企业技能包：≥5 个企业 SOP 技能 + excel-ai-analyst 预置到全局技能目录。注意：技能**没有包内分发通道**（PyInstaller 只打代码包，仅 personas/builtin 有 package-data），预置必须靠安装器/首启动拷贝逻辑（代码级小改）或 REST 导入脚本 | P0 | 资产级+小改 | 技能目录出现在会话 catalog，`load_skill` 可用 |
| F4 | 大表哥 L1+L2：技能 + 前端表格助手入口 | P0 | 代码级 | 3.5 节验收场景通过 |
| F5 | 品牌换肤：企业主题色/logo/应用名/图标/DMG 背景 | P0 | 资产级 | 三平台安装包全部呈现企业品牌 |
| F6 | 企业更新源：三平台自动更新指向企业发布清单，企业自持签名密钥 | P0 | 配置级 | 旧版安装包可自动升级到新版 |
| F7 | 知识库 v1：文件根挂载 + 技能内置知识 ✅**已交付** —— `knowledge_roots` 常驻只读挂载（全局配置专属）+ `corp-knowledge` 检索技能 | P1 | 配置级 | 员工可让 agent 检索企业制度文档并回答 |
| F8 | 企业 CLI 接入：≥1 个企业 CLI 以 MCP server 方式注册 ✅**已交付** —— 通用 CLI→MCP 桥（配置驱动，白名单子命令 + 参数校验 + 不经 shell） | P1 | 资产级 | 对话中可调用企业 CLI 完成真实操作 |
| F9 | 连接器/Provider 目录白名单：隐藏不合规入口 ✅**已交付** —— `allowed/denied_connectors|providers` 四个全局配置项，四处执行点（列表/工具装配/连接/client 构建），拒绝优先 | P1 | 配置级 | 企业构建 UI 中无海外 SaaS 连接器，且实际调用也被拒 |
| F10 | 审计外发：工具调用审计日志推送企业日志系统 ✅**已交付** —— 后台线程 + 有界队列 + 失败开放；本地先落库再外发，脱敏复用本地同一套规则 | P1 | 配置级 | SIEM 可查任意会话的工具调用记录 |
| F11 | 大表哥 L3：excel_ai 注册为内置工具 | P2 | 代码级 | agent 可编程调用并产出验证报告 |
| F12 | 知识库 v2：企业知识库 MCP 检索服务 ✅**已交付** —— http/folder 双后端，字段声明式映射；Agent 只拿检索结果、无文件系统访问权 | P2 | 资产级 | 知识检索走 MCP，权限在知识库侧校验 |
| F13 | 企业内部系统连接器（OA/工单等，首个） | P2 | 代码级 | 完成一个真实内部系统的读写操作 |
| F14 | 企业介绍站 + 下载页（企业域名） | P1 | 资产级 | 员工可从企业站下载对应平台安装包 |

---

## 5. 非功能需求

| 类别 | 要求 |
|------|------|
| 同步可持续性 | 企业定制代码与上游代码物理隔离（独立目录/文件优先，改动上游文件时最小 diff）；每次上游同步人工处理 ≤ 2h（G4） |
| 性能 | 桌面端冷启动 ≤ 5s（同汉化版基线）；大表哥 20MB 表格 Step 0 探测 ≤ 60s |
| 安全 | 全部模型/知识流量走内网；安装包签名（macOS 公证 + Windows 代码签名）；更新包企业密钥签名 |
| 兼容性 | macOS 12+（Apple Silicon / Intel）、Windows 10/11 x64；WebView2 自动引导安装 |
| 可运维性 | 版本号策略 `<上游版本>-<corp>.<n>`（如 `0.1.7-corp.1`）；每个发布带更新日志 |
| 许可合规 | 上游 MIT 许可证保留版权声明；企业闭源定制部分独立目录并在 NOTICE 中声明 |

---

## 6. 整体架构（定制层视角)

```
┌─────────────────────────────────────────────────────────┐
│  企业定制层（私有仓独有，物理隔离，同步零冲突）                  │
│  enterprise/skills/   企业技能包（含 excel-ai-analyst）      │
│  enterprise/branding/ 主题、图标、名称、DMG 背景               │
│  enterprise/config/   默认 config.toml、Provider 预置        │
│  enterprise/mcp/      企业 CLI / 知识库 MCP server 配置       │
│  enterprise/connectors/ 企业内部系统连接器                    │
│  企业站（website 复制品牌化）· 企业发布流水线（更新源/签名）        │
├─────────────────────────────────────────────────────────┤
│  汉化层（来自 zhanglunet/openworker-zh-localized）           │
│  前端/桌面壳中文文案 · 中文站基建 · 打包与同步流水线               │
├─────────────────────────────────────────────────────────┤
│  上游 OpenWorker（andrewyng/openworker）                    │
│  coworker 引擎 · Provider 体系 · 连接器 · GUI · Tauri 壳      │
└─────────────────────────────────────────────────────────┘
```

原则：**定制向上不向内**——能用配置和资产解决的不改代码；必须改代码的收敛到少量"挂载点"文件（Provider 目录、连接器 catalog、前端入口注册），把同步冲突面控制在个位数文件。

---

## 7. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 上游 Beta 期重构频繁，冲突面扩大 | 同步成本超预算 | 挂载点模式 + 每日小步同步（见 UPSTREAM_SYNC）；冲突自动开 Issue 提醒 |
| 无 i18n 资源层，上游文案改动即冲突 | 汉化层长期维护成本 | 汉化冲突由汉化仓先行消化，企业仓只消费汉化仓结果 |
| Apple 公证 / Windows 签名证书办理周期 | 分发受阻 | 提前启动证书申请（见 DEPLOYMENT 前置清单）；过渡期用企业 MDM 白名单分发未公证包 |
| 私有模型能力弱于公有模型 | 体验落差 | 能力矩阵按真实模型能力登记，必要时混合路由（敏感任务内网、通用任务可选） |
| 大表哥完整产线依赖 AI 且计算量大 | 大表体验差 | L1 用技能走既有模型；超大表引导用本地 `excel_ai.py` 全量跑批 |

---

## 8. 里程碑概览

详见 [DEV_PLAN.md](DEV_PLAN.md)。概要：

- **M0（第 1 周）**：私有仓建立 + 三仓同步打通 + 企业站雏形
- **M1（第 2-3 周）**：P0 全部落地（私有模型、配置预置、技能包、大表哥 L1/L2、换肤、企业更新源）→ 内测版 `0.x-corp.1`
- **M2（第 4-5 周）**：P1（知识库 v1、企业 CLI MCP、白名单、审计外发、企业站正式）→ 试点版
- **M3（第 6-8 周）**：P2（大表哥 L3、知识库 v2 MCP、首个内部系统连接器）→ 正式版
