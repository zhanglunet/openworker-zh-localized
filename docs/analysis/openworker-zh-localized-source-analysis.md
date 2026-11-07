# OpenWorker 中文本地化仓库源码分析

更新时间：2026-11-07T20:21:23+09:00

仓库：zhanglunet/openworker-zh-localized

当前分支：main

当前提交：b64c3b618e5762581508035056694cf341032708

## 1. 总体判断

本仓库是在 OpenWorker 原始项目基础上的中文本地化与中文站扩展版本。它不是单纯的静态翻译包，而是包含桌面 App、Python 本地 Agent 服务、React 工作台、连接器/MCP、打包脚本、中文网站、下载产物和持续文档化页面的一体化仓库。

## 2. 代码规模快照

- 跟踪文件总数：733
- 当前提交：b64c3b6
- 主要文件类型：
  - py: 322
  - ts: 105
  - md: 88
  - tsx: 79
  - png: 25
  - svg: 23
  - json: 20
  - yml: 15
  - html: 8
  - [none]: 7
  - sh: 6
  - css: 4
  - mjs: 4
  - rs: 4
  - toml: 4
  - dmg: 2

## 3. 目录结构

- surfaces: 229 个文件
- tests: 146 个文件
- coworker: 134 个文件
- docs: 112 个文件
- website: 36 个文件
- scripts: 22 个文件
- .github: 11 个文件
- role-packs: 11 个文件
- packaging: 10 个文件
- ui-mocks: 6 个文件
- stt: 4 个文件
- releases: 3 个文件
- .gitignore: 1 个文件
- BUILD_LOG.md: 1 个文件
- LICENSE: 1 个文件
- openworker-zh-test-report.md: 1 个文件
- pyproject.toml: 1 个文件
- README.en.md: 1 个文件
- README.md: 1 个文件
- start-openworker-gui.sh: 1 个文件
- start-openworker-server.sh: 1 个文件

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
