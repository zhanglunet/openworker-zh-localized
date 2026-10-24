# PRD-155/T1：中文面板信息架构与文案表

> trend issue #775。对应 PRD-155（中央仓库 zhanglunet/trend）。
> 状态：T1 设计稿——只定信息架构、中文文案表、演示数据契约与适配层边界，不写实现代码；T2/T3 按本稿落地。
> 借鉴：[bowenliang123/dsh-context](https://github.com/bowenliang123/dsh-context)（Apache-2.0）——复用「静态页拉起面板 + 组成/时间线分区」的形态与结构，表述自研；T2 落地时在面板页脚保留原项目版权声明引用。

## 1. 背景与现状落点

三条仓库现状（2026-10-23，main = d7c8bbc）决定本设计的形态：

| 现状 | 对本设计的影响 |
|---|---|
| `ui-mocks/` 已有 4 个零依赖静态 HTML 样机（`redesign.html` 等，Tailwind CDN + `data-theme` 明暗双主题，双击即开） | 面板演示形态落 `ui-mocks/dsh-context-panel.html`：纯静态页，无服务、无构建、不做 SaaS；T2 能力组成、T3 调用演进同页两区渐进交付 |
| `surfaces/gui/src/` 的中文是内嵌字符串，无 i18n key（PRD-067/T1 §1 盘点结论，方案 A「继续自维护」已拍板） | §3 文案表的「键名」是**文档键**（评审、中英对照、T4 文档引用用），落地时按仓库惯例内嵌，ui-mocks 阶段作页内 `LABELS` 常量；不是运行时查表 key |
| `scripts/quality-gate.py` 的 `TERMS` 已锁定 25 条术语（PRD-067/T1 §4，用户 2026-10-18 拍板），品牌词（GitHub、Slack 等）豁免 | §3 每条文案标注术语表来源；已拍板译法直接复用，面板新词单列「本稿新增（评审点）」——T1 验收标准即文案评审通过 |

**与借鉴对象的边界**：面板是 owzh 自有资产（自研静态页，后续可进 `surfaces/gui`），**不安装、不绑定** dsh-context 上游插件（英文-only、未本地化）——只借鉴面板形态与分区思路，规避 PRD 非目标「不依赖未本地化的上游英文-only 插件硬绑定」，也无许可证传递负担（引用声明即可）。

## 2. 面板信息架构（两区）

```
+----------------------------------------------------------------------------------+
| OpenWorker 上下文面板    角色「样例角色-运营助手」· 会话「整理本周趋势日报摘要」     |
|                                                            [演示数据] ← 常驻徽标  |
+----------------------------------------------------------------------------------+
|    [① 能力组成]   [② 调用演进]                  ← 顶部页签，默认落在①              |
+----------------------------------------------------------------------------------+
| ① 能力组成                                                                        |
|   装配清单                                                                        |
|   模型     <示例模型名>（服务商：<示例服务商>）                                    |
|   角色     样例角色-运营助手：负责日报整理与摘要                                   |
|   技能     2 项：日报摘要 · 周报归档                                              |
|   连接器   2 个：GitHub · Slack（账号均为占位符）                                  |
|   工具     2 个：web_search · file_read                                           |
|   审批     敏感操作需人工审批                                                     |
|   上下文构成（token 占比，合计 10,300）                                           |
|   系统提示     ██████████ 31%   3,200 tok                                       |
|   工具定义     █████████ 27%     2,800 tok                                        |
|   技能注入     ██████ 18%       1,900 tok                                        |
|   连接器说明   ████ 12%           1,200 tok                                       |
|   历史会话串   ████ 12%           1,200 tok                                       |
+----------------------------------------------------------------------------------+
| ② 调用演进（选中「②」页签时展示）                                                  |
|   09:00 ●用户消息──●工具调用──◆连接器调用──◆审批──●智能体回复 09:03                 |
|              帮我整理…  web_search   GitHub·读周报  写入前确认  已生成 5 条要点     |
|   点击任一节点 → 下方详情：该步状态（成功/失败/已重试）、输入/输出 token、耗时      |
+----------------------------------------------------------------------------------+
| 页脚：面板形态借鉴自 bowenliang123/dsh-context（Apache-2.0）· 当前为演示数据       |
+----------------------------------------------------------------------------------+
```

| 区 | 回答的问题 | 主数据（§4 契约） | 交互 |
|---|---|---|---|
| ① 能力组成 | 这个数字同事装了什么能力、上下文被什么占着 | `capabilities` + `context_composition` | 装配清单只读；占比条悬停看 token 数 |
| ② 调用演进 | 一次运行里调用怎么发生、哪步失败/重试、花了多少 token | `timeline[]` | 节点点击出该步详情；时间倒序不需要（按发生顺序） |

两区取舍说明：dsh-context 的「压缩记录」区不复刻——owzh 当前无上下文压缩动作可展示，不造假区；将来上游有对应能力再增第三区（信息架构留页签扩展位）。

## 3. 中文 UI 文案表

术语表来源列：**067 §4** = `scripts/quality-gate.py` `TERMS` 25 条拍板表；**067 §4 组合** = 拍板术语的组合词；**本稿新增** = 面板新词，即本次评审点。

### 3.1 面板框架

| 键名 | 中文文案 | 英文对照 | 术语表来源 |
|---|---|---|---|
| `panel.title` | 上下文面板 | Context panel | 本稿新增（评审点） |
| `panel.subtitle.role` | 角色 | Persona | 067 §4 |
| `panel.subtitle.session` | 会话 | Session | 067 §4 |
| `panel.badge.demo` | 演示数据 | Demo data | 本稿新增（评审点） |
| `panel.tab.composition` | 能力组成 | Capabilities | 本稿新增（评审点，PRD-155 任务名） |
| `panel.tab.timeline` | 调用演进 | Invocation timeline | 本稿新增（评审点，PRD-155 任务名） |
| `panel.footer.attribution` | 面板形态借鉴自 bowenliang123/dsh-context（Apache-2.0） | Panel form inspired by bowenliang123/dsh-context (Apache-2.0) | 本稿新增（许可证声明，T2 落地） |

### 3.2 能力组成区

| 键名 | 中文文案 | 英文对照 | 术语表来源 |
|---|---|---|---|
| `comp.group.model` | 模型 | Model | 067 §4 |
| `comp.group.provider` | 服务商 | Provider | 067 §4（已拍板，勿用「供应商」） |
| `comp.group.persona` | 角色 | Persona | 067 §4 |
| `comp.group.skills` | 技能 | Skills | 067 §4（勿残留英文 Skill） |
| `comp.group.connectors` | 连接器 | Connectors | 067 §4 |
| `comp.group.tools` | 工具 | Tools | 本稿新增（评审点；067 只拍板「工具调用」） |
| `comp.group.approvals` | 审批 | Approvals | 067 §4 |
| `comp.approval_policy` | 审批策略 | Approval policy | 067 §4 组合 |
| `comp.context.title` | 上下文构成 | Context composition | 本稿新增（评审点） |
| `comp.context.system` | 系统提示 | System prompt | 067 §4（prompt→提示词） |
| `comp.context.tools` | 工具定义 | Tool definitions | 本稿新增（评审点） |
| `comp.context.skills` | 技能注入 | Skill injections | 本稿新增（评审点） |
| `comp.context.connectors` | 连接器说明 | Connector descriptions | 067 §4 组合 |
| `comp.context.history` | 历史会话串 | Thread history | 067 §4（thread→会话串） |
| `comp.count` | 共 {count} 项 | {count} in total | 本稿新增 |
| `comp.empty` | 尚未装配任何能力 | No capabilities configured | 本稿新增 |

### 3.3 调用演进区

| 键名 | 中文文案 | 英文对照 | 术语表来源 |
|---|---|---|---|
| `tl.node.user` | 用户消息 | User message | 本稿新增 |
| `tl.node.assistant` | 智能体回复 | Agent reply | 067 §4（agent→智能体，勿用「代理」） |
| `tl.node.tool_call` | 工具调用 | Tool call | 067 §4 |
| `tl.node.connector_call` | 连接器调用 | Connector call | 067 §4 组合 |
| `tl.node.approval` | 审批 | Approval | 067 §4 |
| `tl.status.ok` | 成功 | Success | 本稿新增（评审点；067 只拍板「失败」反义词） |
| `tl.status.failed` | 失败 | Failed | 067 §4 |
| `tl.status.retried` | 已重试 | Retried | 067 §4（retry→重试） |
| `tl.tokens.in` | 输入 token | Input tokens | 本稿新增（评审点：「token」业界惯例不译） |
| `tl.tokens.out` | 输出 token | Output tokens | 本稿新增（评审点，同上） |
| `tl.detail.duration` | 耗时 | Duration | 本稿新增 |
| `tl.empty` | 该运行暂无调用记录 | No invocations in this run | 067 §4（run→运行）+ 本稿 |

### 3.4 警示与说明

| 键名 | 中文文案 | 英文对照 | 术语表来源 |
|---|---|---|---|
| `warn.demo_note` | 当前为演示数据，非真实运行 | Demo data, not a live session | 本稿新增 |
| `warn.provider_missing` | 未配置模型服务商 | No model provider configured | 067 §4 组合 |
| `warn.placeholder_note` | 敏感信息已用占位符代替 | Sensitive values replaced with placeholders | 本稿新增 |

评审口径建议：仅 §3 中标「本稿新增（评审点）」的 11 条需要拍板，其余为已拍板术语复用或中性描述词。

## 4. 本地/演示数据约定（虚构样例）

### 4.1 契约：`panel-data v1`（面板唯一数据格式）

字段表（`*` = 待 coworker 适配时核对上游口径的假设，见 §5）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `schema_version` | int | 恒 `1`；不等于 1 → 面板显示「数据源版本不支持」，不渲染 |
| `meta.generator` | enum | `demo` / `coworker`；`demo` 时强制显示演示徽标 |
| `session.role_name` | string | 角色名（虚构样例：`样例角色-运营助手`） |
| `session.session_title` | string | 会话标题（虚构样例：`整理本周趋势日报摘要`） |
| `session.model` / `session.provider` | string | 展示名，允许占位符形态（`<示例模型名>`） |
| `session.started_at` | string | ISO 8601，虚构固定值 |
| `capabilities.skills[]` | object[] | `{name, source}` |
| `capabilities.connectors[]` | object[] | `{kind, account}`；`account` 一律占位符 |
| `capabilities.tools[]` | object[] | `{name}` |
| `capabilities.approval_policy` | string | 中文短语，直接展示 |
| `context_composition.*` | object | 5 段：`system/tools/skills/connectors/history`，各含 `tokens`(int) 与 `share`(0–1，契约算好，面板不二次归一)* |
| `timeline[]` | object[] | `{at, kind: user/assistant/tool_call/connector_call/approval, label, status?: ok/failed/retried, tokens_in?, tokens_out?, duration_ms?, connector?}` |

### 4.2 落点与样例

T2 落 `ui-mocks/fixtures/panel-demo-data.json`，本稿定内容口径（节选，完整样例 T2 按此扩写）：

```json
{
  "schema_version": 1,
  "meta": { "generator": "demo" },
  "session": {
    "role_name": "样例角色-运营助手",
    "session_title": "整理本周趋势日报摘要",
    "model": "<示例模型名>",
    "provider": "<示例服务商>",
    "started_at": "2026-10-23T09:00:00+08:00"
  },
  "capabilities": {
    "skills": [{ "name": "日报摘要", "source": "内置样例" }],
    "connectors": [
      { "kind": "github", "account": "<占位符-账号>" },
      { "kind": "slack", "account": "<占位符-账号>" }
    ],
    "tools": [{ "name": "web_search" }, { "name": "file_read" }],
    "approval_policy": "敏感操作需人工审批"
  },
  "context_composition": {
    "system": { "tokens": 3200, "share": 0.31 },
    "tools": { "tokens": 2800, "share": 0.27 },
    "skills": { "tokens": 1900, "share": 0.18 },
    "connectors": { "tokens": 1200, "share": 0.12 },
    "history": { "tokens": 1200, "share": 0.12 }
  },
  "timeline": [
    { "at": "09:00", "kind": "user", "label": "帮我整理这周的日报要点" },
    { "at": "09:00", "kind": "tool_call", "label": "web_search", "status": "ok", "tokens_in": 640, "tokens_out": 210 },
    { "at": "09:01", "kind": "connector_call", "connector": "github", "label": "读取示例仓库周报", "status": "ok" },
    { "at": "09:02", "kind": "approval", "label": "写入共享文档前需确认", "status": "ok" },
    { "at": "09:03", "kind": "assistant", "label": "已生成 5 条要点摘要", "tokens_out": 880 }
  ]
}
```

### 4.3 红线（继承 PRD-155 风险条款）

1. 账号、密钥、内部主机名、IP 一律 `<占位符-…>` 形态；连接器品牌名（GitHub、Slack）可出现（`quality-gate.py` `BRAND_WORDS` 豁免），但令牌、仓库地址、用户名全占位。
2. 「演示数据」徽标常驻页头，`meta.generator=demo` 时由代码强制显示，数据文件关不掉。
3. T2 为 fixtures 增加一条自查断言：键名或字符串值命中 `/(secret|password|credential|api[-_]?key|bearer|private[-_]?key|\\d+\\.\\d+\\.\\d+\\.\\d+)/i` 即测试失败（沿用 quality-gate 的自查思路，轻量实现）。
4. 时间戳、token 数全虚构；占比五段之和恒为 1.00。

## 5. 上游 API 适配层隔离设计

**风险对标**：PRD-155 明示「上游 API 变更」为主要风险。隔离方式：面板渲染层只认 `panel-data v1`（§4），永远不直接消费 coworker 后端的原始接口。

```
[ coworker 后端原始 API ]  →  [ coworker 适配器 ]  →  panel-data v1  →  [ 渲染层（两区） ]
        （上游，会变）              （映射层，可重写）        （稳定契约）        （不感知上游）
[ ui-mocks/fixtures 样例 ] →  [ demo 适配器 ]      →  panel-data v1  →  [ 渲染层 ]
```

1. **统一入口**：渲染层唯一数据通道 `loadPanelData(): Promise<PanelData>`，按配置选适配器；默认 `demo`（零网络，`file://` 直接可开）。
2. **`coworker` 适配器本期只留桩**：端点形状本稿**不预设**（不猜 URL、不猜字段），等 T4 后对上游实测再定；对接时沿用既有本机凭据机制（后端 sidecar token，注入方式同 README §7.1 的 `VITE_COWORKER_API_TOKEN` 路径），**不新增凭据体系**；仅绑本机回环地址。
3. **对齐三规则**（沿用 trend 仓库 PRD-145/T1 已验证的做法）：上游字段同名同义 → 直连；改名 → 只在 `coworker` 适配器内做映射，面板与文案表不动；缺字段 → 对应区块显示「数据源未提供」，**不造假数**。
4. **收益**：上游 API 变更的影响面被压到单个适配器文件；T2/T3 用演示数据做的全部成果（布局、文案、交互）在真实对接时可整体复用，只换数据源。

## 6. 与 PRD-121/122 开箱文档的联动点（T4 预告）

现状：PR #38（PRD-121/T1 安装脚本，DRAFT）、PR #39（PRD-122/T1 英文版 README，OPEN）均在流程中。本面板作为「中文开箱即用差异点」的接入位置：

| 联动点 | 位置 | 内容（T4 交付） |
|---|---|---|
| 差异化卖点首露 | `README.md` 第 2 节「与原版的主要区别」表 | 新增一行：上下文可视化面板｜无｜无｜有（中文，演示数据可本地打开） |
| 开箱小节 | `README.md` 第 8 节「已汉化的内容」之后 | 新增「上下文面板（演示）」小节：两区截图 + 三步走（① 装好/克隆仓库；② 浏览器打开 `ui-mocks/dsh-context-panel.html`；③ 对照页签看懂能力组成与调用演进） |
| 截图占位 | `docs/assets/panel-demo-zh.png` | T4 用演示环境补真图（本 T1 先留文件名占位与构图说明：两区各一张，必须为演示数据画面）；禁止真实信息入图 |
| 英文同步 | `README.en.md` | 同结构新增英文小节，翻译底稿即 §3 文案表「英文对照」列；章节一致性由 PRD-122/T3 的 CI 章节比对把关，中英必须同加 |
| 开箱动线串联 | PRD-121 安装文档（PR #38） | 「装完先看什么」指向面板演示页，串成「装好 → 打开面板看懂数字同事的能力 → 跑第一个任务」的动线 |

## 7. 下一步

确认后进 T2（#776）：能力组成视图（演示数据）——按 §2① 布局 + §3 文案表（含评审拍板结果）+ §4 `panel-data v1` 契约，落地 `ui-mocks/dsh-context-panel.html` 能力组成区与 `ui-mocks/fixtures/panel-demo-data.json` 样例。验收口径：本地双击 HTML 即可见演示数据；面板文案与 §3 逐条一致；样例文件通过 §4.3 敏感信息自查断言；页脚含 dsh-context 版权声明引用。T3（#777）调用演进时间线在同一页面 §2② 区落位，可与 T2 并行。
