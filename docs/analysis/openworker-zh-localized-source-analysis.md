# OpenWorker 中文本地化仓库源码分析

更新时间：2026-11-10T08:16:30+08:00

仓库：zhanglunet/openworker-zh-localized

当前分支：main

当前提交：00f9c5dc4a8cdd2adcb08c96c3f70f738cb63f8d

## 1. 总体判断

本仓库是在 OpenWorker 原始项目基础上的中文本地化与中文站扩展版本。它不是单纯的静态翻译包，而是包含桌面 App、Python 本地 Agent 服务、React 工作台、连接器/MCP、打包脚本、中文网站、下载产物和持续文档化页面的一体化仓库。

## 2. 代码规模快照

- 跟踪文件总数：760
- 当前提交：00f9c5d
- 主要文件类型：
  - py: 342
  - ts: 105
  - md: 93
  - tsx: 79
  - png: 25
  - svg: 23
  - json: 21
  - yml: 15
  - html: 8
  - [none]: 7
  - sh: 6
  - css: 4
  - mjs: 4
  - rs: 4
  - toml: 4
  - lock: 3

## 3. 目录结构

- surfaces: 229 个文件
- tests: 160 个文件
- coworker: 134 个文件
- docs: 116 个文件
- website: 36 个文件
- scripts: 28 个文件
- .github: 11 个文件
- role-packs: 11 个文件
- packaging: 10 个文件
- ui-mocks: 6 个文件
- stt: 4 个文件
- releases: 3 个文件
- skills: 2 个文件
- .gitignore: 1 个文件
- BUILD_LOG.md: 1 个文件
- LICENSE: 1 个文件
- openworker-zh-test-report.md: 1 个文件
- pyproject.toml: 1 个文件
- README.en.md: 1 个文件
- README.md: 1 个文件
- start-openworker-gui.sh: 1 个文件
- start-openworker-server.sh: 1 个文件
- uv.lock: 1 个文件

## 4. 核心模块

### 桌面壳

Tauri 负责启动窗口、托盘、原生权限、语音输入、更新检查和 Python sidecar 生命周期。

关键路径：
- `surfaces/gui/src-tauri/src/lib.rs`
- `surfaces/gui/src-tauri/tauri.conf.json`

### 前端工作台

React 工作台承载会话、审批、收件箱、连接器、模型配置、产物和实时事件流。

关键路径：
- `surfaces/gui/src/App.tsx`
- `surfaces/gui/src/api.ts`
- `surfaces/gui/src/components`

### 本地服务

FastAPI sidecar 暴露 REST 与 WebSocket，集中协调会话、任务、审计、自动化和持久化。

关键路径：
- `coworker/server/app.py`
- `coworker/server/manager.py`

### Agent 运行核心

TurnEngine、PermissionEngine、工具注册表和 ProviderRouter 组成 model-tool 循环。

关键路径：
- `coworker/engine.py`
- `coworker/permissions.py`
- `coworker/tools`
- `coworker/providers`

### 连接器与 MCP

内置连接器、MCP server 管理和 OAuth/账户视图把外部系统接入本地运行时。

关键路径：
- `coworker/connectors`
- `coworker/mcp`
- `surfaces/gui/src/connectors`

### 中文站与发布物

中文站、架构信息图、源码分析、日志周报和 macOS DMG 下载入口随仓库维护。

关键路径：
- `website`
- `docs`
- `releases`

## 5. 运行链路

1. 下载 DMG 或源码启动
2. Tauri/浏览器加载 GUI
3. sidecar 选择端口并生成 token
4. GUI 通过 REST/WebSocket 连接本地服务
5. 用户发起目标与上下文
6. 模型提出计划与工具调用
7. 权限系统判断风险与批准策略
8. 工具结果写入会话、审计、Inbox 或文件
9. 最终结果返回用户

## 6. 架构流程图

```mermaid
flowchart LR
  N0["用户目标"]
  N1["React/Tauri 工作台"]
  N2["FastAPI sidecar"]
  N3["SessionManager"]
  N4["TurnEngine"]
  N5["ProviderRouter"]
  N6["模型"]
  N7["工具/MCP/连接器"]
  N8["权限与审计"]
  N9["交付物"]
  N0 --> N1
  N1 --> N2
  N2 --> N3
  N3 --> N4
  N4 --> N5
  N5 --> N6
  N6 --> N7
  N7 --> N8
  N8 --> N9
```

## 7. API 与 MCP

- 健康与启动: /v1/health、WebSocket /ws/events
- 会话: /v1/sessions、/ws/session/{sessionId}
- 模型提供商: /v1/providers、/v1/providers/models
- 连接器: /v1/connectors/*、OAuth 状态轮询
- MCP: /v1/mcp/*、stdio / streamable-http server
- 自动化与 Inbox: /v1/automations/*、/v1/inbox/*
- 本地文件与产物: 文件工具、目录授权、产物预览

## 8. 企业定制扩展点

企业定制版（私有仓）可以在不重写核心的前提下，按下列层次定制。完整方案见 `docs/enterprise/`（PRD、开发计划、三仓同步、部署、换肤打包）。

### 模型层 · 私有模型（配置级）

Provider 注册表内置 Custom（OpenAI 兼容 base_url）与 Ollama 构建器，企业 vLLM/网关的端点、端口与模型版本直接配置接入；模型能力在能力矩阵登记。

关键路径：
- `coworker/providers/registry.py`
- `coworker/providers/matrix.py`
- `docs/config.example.toml`

### 技能层 · 企业技能包（资产级）

SKILL.md 规范（YAML frontmatter + 渐进式加载），全局 state_dir()/skills 与工作区 .coworker/skills 双目录；企业 SOP 技能与大表哥 excel-ai-analyst 预置即用。

关键路径：
- `coworker/skills/base.py`
- `coworker/skills/store.py`

### 知识层 · 企业知识库（资产级起步）

无内置向量 RAG；现实路径是文件根挂载 + 技能内置知识起步，中期把企业知识库封装成 MCP 检索服务，权限留在知识库侧。

关键路径：
- `coworker/roots.py`
- `coworker/project.py`
- `coworker/memory`

### 工具层 · 企业 CLI 与内部系统（配置级 + 代码级）

企业 CLI 首选封装为 MCP server 注册；内部系统按连接器 descriptor 模式扩展；allowed_commands 白名单与审批模式管控执行边界。

关键路径：
- `coworker/mcp`
- `coworker/connectors/descriptors.py`
- `coworker/cli.py`

### 专属功能 · 大表哥表格助手（三层渐进）

L1 预置 excel-ai-analyst 技能（表格当代码逆向：探测/公式链/全量验证）→ L2 前端表格助手入口 → L3 excel_ai 注册为内置工具。

关键路径：
- `coworker/tools`
- `surfaces/gui/src/App.tsx`

### 品牌层 · 换肤与命名（资产级）

颜色单一事实源是 styles.css 的 CSS 变量（Tailwind 仅映射 token），换肤=覆盖一个变量块；应用名/Bundle ID/图标/更新源集中在 tauri.conf.json。

关键路径：
- `surfaces/gui/src/styles.css`
- `surfaces/gui/tailwind.config.js`
- `surfaces/gui/src-tauri/tauri.conf.json`

### 同步层 · 三仓不覆盖同步（流水线）

上游→汉化版每日自动合并开 PR、冲突自动开 Issue；企业私有仓复制同款流水线单向对接汉化仓，配合 enterprise/ 目录隔离与挂载点纪律实现定制零覆盖。

关键路径：
- `.github/workflows/sync-upstream.yml`

### 发布层 · 多平台打包与更新（流水线）

发布矩阵覆盖 macOS Apple Silicon/Intel 双 DMG 与 Windows MSI/NSIS，latest-zh.json 驱动 Tauri 自动更新；企业版换名称、签名密钥与更新源即用。

关键路径：
- `.github/workflows/release.yml`
- `packaging/build_dmg.sh`
- `packaging/make_update_manifest.py`

## 9. 最近更新

- 2026-11-10 00f9c5d Merge pull request #115 from zhanglunet/trend/prd-341-t5-acceptance
- 2026-11-10 de236fe Merge pull request #114 from zhanglunet/trend/prd-341-t4-boundary
- 2026-11-10 4063e59 Merge pull request #113 from zhanglunet/trend/prd-341-t3-gate
- 2026-11-10 040aab4 Merge pull request #112 from zhanglunet/trend/prd-341-t2-checklist-impl
- 2026-11-10 dd8a640 Merge pull request #111 from zhanglunet/trend/prd-341-t1-12factors-design
- 2026-11-10 413e399 Merge pull request #109 from zhanglunet/trend/prd-341-t1-design
- 2026-11-09 9a05b1e test: PRD-341/T5 十二原则 checklist 验收试运行——test_prd341_t5_acceptance.py（7 例全绿，链上 T2–T4 33 例仍绿）①真实 skill 全量试运行（十二项全跑 机检 9 过+manual 3 附答留痕→READY_FOR_HUMAN 闸门零替人拍板+双 skill batch_gate 汇总逐 skill 裁决平列+回放逐字节可复现）②失败演练三路全显形（机检 fail→BLOCKED 未过项显形零视为通过/manual 未附答→PENDING_MANUAL 问题清单显形/manual 项被篡改为 pass→TAMPERED R4 复核拒绝）③文档无密钥（T1 设计文档经 git show origin/trend/prd-341-t1-12factors-design 扫描零密钥/零 IP/外链仅 github 与 example 域）（trend #1620 的 T5 环节）
- 2026-11-09 5c68185 test: PRD-341/T4 十二原则 checklist 划界断言——test_prd341_t4_boundary.py（7 例全绿）R3 数据驱动断言（run_checklist/checklist_gate 源码零原则 id 零机检器名复钉/gate 的 MANUAL_IDS is 数据模块同一 frozenset 单向引用/增补原则演练：运行时向 CHECKLIST 追加 P13 后 run_checklist 即覆盖新条目零改引擎代码 finally 还原零残留）+R2 零复用抽样断言（十二条 principle 全中文原创含 CJK 零英文 factor 术语/两模块 AST 零 humanlayer/12-factor/swe-agent 借鉴仓符号）+R1 复钉（check_ref 全部指向 scripts/ 既有模块）+与 199/227/303 划界（checklist_gate 单向只读消费零机检器模块导入）+与 PRD-303 重放包划界钉值（trend #1620 的 T4 环节）
- 2026-11-09 f9e7a1a feat: PRD-341/T3 十二原则 checklist 通过闸门——checklist_gate.py GATE_CODES 四码封闭（READY_FOR_HUMAN/PENDING_MANUAL/BLOCKED/TAMPERED）+checklist_gate 单 skill 通过闸门（机检 fail→BLOCKED failing 显形/机检全过 manual 未附答→PENDING_MANUAL 问题清单显形零视为通过 R4/全备→READY_FOR_HUMAN 荐人工拍板闸门零替人拍板/manual 项状态被篡改为 pass/fail→TAMPERED 显形拒绝 R4 复核 manual 只能是 manual）+batch_gate 全库汇总归重（消费 T2 summarize/任一非 READY 整库归重/逐 skill 裁决平列人工逐个拍板）+与 T2 串联三种真实产物逐一过闸+AST 只读消费零网络零机检器导入（10 例全绿，T2 16 例仍绿，trend #1620 的 T3 环节）
- 2026-11-09 9b2b02f feat: PRD-341/T2 十二原则 checklist 最小实现——CHECKLIST 声明式数据（check_ref 全部指向 scripts/ 既有模块 zh_trigger_registry/zh_sources/consistency_check/zh_skill_ref/skillpack_snapshot/cn_skill_sync_check/trigger_probe/zh_intake_gate 零新建判定逻辑 R1）+run_checklist 每 skill 一份（§6.1 裁决）+机检器反射注入适配器 honest 三态映射（None=clean/真值 pass/假值 fail 带 reason/异常 fail 显形/未注册 fail 显形——零视为通过 R4）+manual JSON 附答只留痕不改状态非法指向显形拒绝（§6.2 裁决）+summarize 全库汇总视图 failing 清单+引擎零硬编码 R3（数据与逻辑分离 T4 预埋）+模块 stdlib-only R2 零复用预埋（16 例 pytest 全绿）（trend #1620)
- 2026-11-09 af53436 docs: refresh generated site reports
- 2026-11-09 20fb91f chore: 更新上游哨兵水位（PRD-068）
