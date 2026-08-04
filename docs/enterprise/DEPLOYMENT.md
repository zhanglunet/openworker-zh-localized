# 企业定制版 · 部署步骤

- 版本：v1.0 · 2026-08-04
- 覆盖：私有仓建立 → 同步流水线 → 企业站 → 私有模型接入 → 技能/知识库/MCP 部署 → 桌面端分发与更新
- 前置阅读：[UPSTREAM_SYNC.md](UPSTREAM_SYNC.md)（同步原理）、[BRANDING_PACKAGING.md](BRANDING_PACKAGING.md)（打包细节）

---

## 0. 前置准备清单（开工前办齐）

| 项 | 说明 | 责任方 |
|----|------|--------|
| GitHub 组织 + 私有仓权限 | `<corp>/openworker-enterprise`（私有）；若代码不允许出内网，用企业 GitLab/Gitea 同理 | IT |
| Apple Developer Program（组织账号） | Developer ID 证书 + Notary API Key（macOS 签名公证；办理周期 1-2 周，尽早启动） | IT/法务 |
| Windows 代码签名证书 | OV 起步，EV 更佳（可后补） | IT |
| Tauri updater 企业密钥对 | `npm run tauri signer generate` 生成，私钥入 Secrets | 定制团队 |
| 企业模型端点 | OpenAI 兼容 API（vLLM/网关）内网地址 + API Key + 模型名清单 | AI 平台组 |
| 企业域名 | 企业站（如 `ai.<corp>.com`）+ 更新托管（如 `apps.<corp>.com`），内网或公网按合规定 | IT |
| 大表哥资产 | excel-ai-analyst 技能包（SKILL.md + excel_ai.py）；如需内嵌 Step 0 页面，取得 anp.asia 页面部署授权/文件 | 定制团队 |
| 内网构建镜像 | `pyproject.toml` 中 aisuite 依赖钉在 git commit（`git+https://github.com/andrewyng/aisuite.git@…`）——内网 CI 构建需镜像该仓库（或私有 PyPI 缓存）；npm/crates 同理准备企业镜像源 | IT/定制团队 |

---

## 1. 建立私有仓（保留完整历史，一次做对）

```bash
# 1) 镜像克隆汉化版（完整历史，同步的共同祖先就在这里）
git clone --bare https://github.com/zhanglunet/openworker-zh-localized.git
cd openworker-zh-localized.git

# 2) 在 GitHub 建空私有仓 <corp>/openworker-enterprise（不要初始化 README）

# 3) 全量镜像推送
git push --mirror git@github.com:<corp>/openworker-enterprise.git

# 4) 正常克隆私有仓开始工作
cd .. && git clone git@github.com:<corp>/openworker-enterprise.git
```

> ⚠️ 不要用 GitHub 网页 Import（历史可能被改写）、更不要下载 zip 重新 `git init`——共同祖先一丢，以后每次同步都是全文件冲突。

初始化企业结构（首个提交）：

```bash
cd openworker-enterprise
mkdir -p enterprise/{skills,branding,config,mcp,connectors,tools,tests,site}
# 放入 .github/workflows/sync-localized.yml（见 UPSTREAM_SYNC.md 3.2）
# 放入 .github/workflows/release-corp.yml（复制 release.yml 改名字/密钥/托管地址）
git checkout -b corp/init && git add -A && git commit -m "corp: 初始化企业定制层目录与同步流水线"
```

分支模型：`main`（企业稳定线）← feature 分支（定制开发）；`sync/localized-main`（同步专用，流水线自动管理）。

## 2. 同步流水线部署

1. 把 `sync-localized.yml` 放入私有仓 `.github/workflows/`（内容见 [UPSTREAM_SYNC.md](UPSTREAM_SYNC.md) 3.2）
2. 仓库 Settings → Actions → 允许 GitHub Actions 创建 PR（"Allow GitHub Actions to create and approve pull requests"）
3. 手动触发一次 `workflow_dispatch` 验证：应显示 already-synced（刚镜像完）
4. 在 `enterprise/tests/` 加入定制冒烟测试并挂到 CI（防覆盖闸门，见 UPSTREAM_SYNC.md 3.4）

## 3. 企业站部署（两种形态选一）

现状参考：oaosf.cn 站点源码在 `website/`（Next.js 16 由 vinext 适配 Cloudflare Workers，wrangler 部署，`scripts/generate-site-reports.mjs` 从仓库 git 数据与 `docs/` 生成分析/更新页内容）。

### 形态 A：公网企业站（沿用 Cloudflare，最省事）

```bash
cd website
npm ci
npm run dev                 # 本地预览 http://localhost:3000
npm test                    # 构建 + 渲染 HTML 测试
npx wrangler login          # 企业 Cloudflare 账号
npm run deploy:cloudflare   # 构建并部署 Worker
# Cloudflare 控制台：Workers 自定义域绑定企业域名（DNS 托管到 Cloudflare 或 CNAME 接入）
```

品牌化改动：站名/文案/Logo（`website/app/` 各页面）、下载链接指向企业托管产物、删除或替换 oaosf.cn 专属内容。企业站定制项集中记录在 `enterprise/site/`，正式文件按挂载点规则小改 `website/`。

### 形态 B：内网静态/Node 部署（数据合规要求高时）

`website/` 本质是 Next 应用：`npm run build` 后用内网 Node 服务托管；或将下载页做成纯静态页放内网 Nginx。更新托管（`latest-corp.json` + 安装包）用同一台内网静态服务器即可：

```
/var/www/openworker/
├── latest-corp.json
├── OpenWorker-<corp>-macos-arm64.dmg / .app.tar.gz / .sig
├── OpenWorker-<corp>-macos-x64.dmg  / .app.tar.gz / .sig
└── OpenWorker-<corp>-windows-setup.exe / .msi
```

## 4. 私有模型接入（先跑通，再预置）

### 4.1 手工验证（任一员工机器）

GUI 设置 → 模型 → 添加 Provider：

- **Custom（OpenAI 兼容）**：Base URL `http://llm.<corp>.internal:8000/v1`（vLLM/网关地址，端口按实际）、API Key、模型名（如 `qwen3-72b-corp`）
- 或 **Ollama**：地址 `http://127.0.0.1:11434`（本机）/内网 Ollama 服务地址

界面提供「获取模型列表」「测试连接」（汉化版已有），通过即可对话验证。

### 4.2 预置为默认（企业构建）

`enterprise/config/config.default.toml`（基于 `docs/config.example.toml` 裁剪；配置分层为 内置默认 < `<state-dir>/config.toml` 全局 < `<workspace>/.coworker/config.toml` 工作区，其中 `allowed_commands`/`auto_allow` 出于安全仅全局生效；state 目录 = `$COWORKER_STATE_DIR` > Windows `%APPDATA%\coworker` > `~/.config/coworker`）：

```toml
model = "custom:qwen3-72b-corp"  # 企业默认模型。⚠️ 必须带 provider 前缀（custom:/ollama:）——
                                 # 裸模型名会被路由到默认 openai provider，静默走错端点
mode = "interactive"             # 审批策略：交互式（每步工具调用可控）
max_iterations = 12

allowed_commands = [
  "ls", "cat", "pwd", "grep", "find",
  "git status", "git diff", "git log",
  "python3",
]

host = "127.0.0.1"
port = 8765
```

配套两件事：

- **能力矩阵登记**：`coworker/providers/matrix.py` 的 `MATRIX` 是精选模型表（键为完整路由 id，如 `custom:qwen3-72b-corp`），未登记的模型会落入 `capabilities.py` 的保守启发式（并行工具调用/视觉默认关、无上下文水位条），Agent 效果被动降级——企业模型条目是**必改项**（挂载点小改）。
- **凭据预置**：Provider 密钥存 `<state-dir>/secrets.json`（0600 权限），值支持 `${ENV_VAR}` 引用（配合 `<state-dir>/.env`），适合 IT 下发时不落明文。
- **企业规范注入**：把企业写作规范、术语表、合规要求写入 `<state-dir>/AGENTS.md`——每个会话的 system prompt 自动注入该文件（零代码），项目根的 `AGENTS.md` 再按项目叠加。

预置落地方式（按序生效）：

1. 安装包首启引导：桌面壳检测 `~/.config/coworker/config.toml` 不存在时，从打包资源复制默认配置（代码级小改，放挂载点）
2. 或 IT 批量下发：MDM/域策略把 `config.toml` 与 Provider profile 写到用户目录
3. Provider 端点/密钥属敏感信息：默认配置只带端点不带 Key，Key 由员工首登时输入（存本机 secrets），或对接企业统一鉴权网关按人发 Key

验收：断公网环境（仅内网）新装机器完成一次对话 + 一次文件工具调用。

## 5. 企业技能包与知识库部署

### 5.1 技能包

技能目录（SKILL.md 规范，Anthropic 格式）：

- 全局：应用状态目录 `state_dir()/skills`（每个技能一个文件夹，内含 `SKILL.md` + 资源）
- 工作区：`<workspace>/.coworker/skills`

部署方式：

```
enterprise/skills/                 # 企业技能包源（随仓库版本管理）
├── excel-ai-analyst/              # 大表哥（SKILL.md + excel_ai.py + 参考文档）
├── baoxiao-shenhe/                # 报销审核 SOP
├── zhoubao-huizong/               # 周报汇总
└── …
```

首启（或每次启动）时由桌面壳/后端把 `enterprise/skills/` 打包资源同步到 `state_dir()/skills`（同名跳过或按版本覆盖，员工自建技能不受影响）。IT 也可用脚本推送到员工机器。GUI 设置中可对单个技能启停（`skills-settings.json`）。

### 5.2 知识库 v1（文件根挂载）

1. 企业知识库目录通过同步盘/网盘挂载到员工机器（如 `~/CorpKB/`）
2. 员工把该目录添加为工作区/文件根，agent 即可读取检索
3. 敏感子库用目录权限控制（agent 以当前用户权限访问）

### 5.3 企业 CLI / 知识库 MCP（v2）

MCP 配置文件是标准 `mcpServers` 格式（与 Claude Desktop/Cursor 粘贴兼容）：全局 `<state-dir>/mcp.json`，工作区级 `<workspace>/.coworker/mcp.json`（仅受信任工作区加载，全局同名优先）。企业 CLI 零代码接入示例：

```json
{
  "mcpServers": {
    "corp-cli": {
      "command": "/opt/corp/bin/mytool-mcp",
      "args": ["--serve"],
      "env": {"CORP_TOKEN": "${CORP_TOKEN}"},
      "enabled": true,
      "include_tools": ["search", "create_ticket"],
      "requires_approval": true
    },
    "corp-kb": {
      "url": "https://kb.corp.internal/mcp",
      "headers": {"Authorization": "Bearer ${CORP_KB_TOKEN}"}
    }
  }
}
```

`${VAR}` 在加载时由 SecretStore 从进程环境和 `<state-dir>/.env` 解析；`include_tools`/`exclude_tools` 控制工具白黑名单，`requires_approval` 强制审批。HTTP/SSE 端点支持 OAuth 2.1 + PKCE 浏览器登录（token 存 `mcp-oauth:<server>` profile）。仓库内封装脚本放：

```
enterprise/mcp/
├── corp-cli/          # 企业 CLI 封装成 stdio MCP server（薄封装脚本）
└── corp-kb/           # 知识库检索 MCP server（对接 Confluence/语雀/自建 RAG）
```

知识库权限在 MCP 服务端按调用者校验，知识内容不进安装包。也可通过 `POST /v1/mcp` 由脚本写入配置。

## 6. 桌面端构建、签名与分发

按 [BRANDING_PACKAGING.md](BRANDING_PACKAGING.md) 完成品牌化后：

1. 配置企业仓 Secrets：`APPLE_CERTIFICATE(_PASSWORD)`、`APPLE_SIGNING_IDENTITY`、`APPLE_API_KEY(_CONTENT)`、`APPLE_API_ISSUER`、`TAURI_SIGNING_PRIVATE_KEY(_PASSWORD)`（详细流程照 `docs/release-signed-updates.md`）
2. 打 tag `v0.1.7-corp.1` → `release-corp.yml` 矩阵构建 macOS arm64 / macOS x64 / Windows 三产物并签名公证
3. 产物 + `latest-corp.json` 发布到企业托管（形态 A：企业站/Release 反代；形态 B：内网静态服务器）
4. 企业站下载页更新三平台链接与 SHA-256
5. 分发：企业站自助下载 + IT MDM 批量安装（macOS PKG 可由 DMG 内 .app 二次封装，Windows 用 MSI 静默参数）

## 7. 上线验收清单

- [ ] 同步演练：汉化仓出新提交 → 企业仓次日收到同步 PR → CI 冒烟绿 → 合并后企业定制全部存活
- [ ] 断公网验收：仅内网环境完成对话、技能调用、表格分析、知识库检索
- [ ] 三平台安装 + 自动更新演练通过（arm64 Mac / Intel Mac / Windows）
- [ ] 审计：一次完整任务的工具调用在审计日志可查
- [ ] 回滚预案：企业托管保留上一版产物与清单，`latest-corp.json` 回指旧版即完成回滚
