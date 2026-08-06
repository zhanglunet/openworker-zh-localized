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
| 语音输入模型 | 桌面端语音输入（`stt/` whisper 引擎）默认从 huggingface.co 下载 **英文** base 模型（`stt/src/lib.rs` 的 `DEFAULT_MODEL_URL`），内网环境必须预置模型文件到 `<state-dir>/models/` 或改内网镜像；中文企业版应换中文/多语言 whisper 模型（挂载点小改） | 定制团队 |

---

## 1. 建立私有仓（保留完整历史，一次做对）

> **一键版**：本节全部步骤（含第 2 节的流水线安装）已封装成脚本，建议直接用：
>
> ```bash
> bash docs/enterprise/templates/init-enterprise-repo.sh \
>   --corp acme --name "艾克米科技" \
>   --repo https://github.com/acme/openworker-enterprise.git \
>   --dry-run          # 先看一遍要做什么，确认后去掉 --dry-run
> ```
>
> 下面是脚本背后的手工步骤，供理解与排障。

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

两个已知配置缺口（部署时必须处理）：

- **域名绑定不在代码里**：`wrangler.jsonc` 无 routes/custom_domain 配置，域名 → Worker 的映射只存在于 Cloudflare 控制台，必须手工绑定（deploy 成功 ≠ 域名可访问）。
- **IMAGES 绑定缺失**：`worker/index.ts` 的 `/_vinext/image` 端点调用 `env.IMAGES`，但 `wrangler.jsonc` 未声明 images 绑定——照抄配置部署后图片优化端点会运行时报错；企业站需在 `wrangler.jsonc` 补 `"images": { "binding": "IMAGES" }`，或确认站内不用该端点。
- 换品牌时**站点测试断言要同步改**：`tests/rendered-html.test.mjs` 硬编码了「OpenWorker 中文站」、DMG 文件名、SHA-256、Bundle ID 与双仓库链接。

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
max_iterations = 150             # 代码默认值即 150（docs/config.example.toml 中的 12 是过期值）

# 云端服务（企业内网版建议显式关闭/替换）：
# cloud_base_url = ""            # 默认 https://api.openworker.com，仅 OAuth 中转；企业可指向自建实例
# cloud_relay_ws_url = ""        # 置空即关闭云 relay 通道

allowed_commands = [
  "ls", "cat", "pwd", "grep", "find",
  "git status", "git diff", "git log",
  "python3",
]

host = "127.0.0.1"
port = 8765
```

配套两件事：

- **能力声明（不必改代码）**：未登记的模型会落入 `capabilities.py` 的保守启发式（并行工具调用/视觉默认关、无上下文水位条），Agent 被动降级。本仓库已加入**本地声明覆盖层**：在 `<state-dir>/models.json` 里声明即可，热重载、格式错只告警不影响启动。

  ```json
  {
    "models": {
      "custom:qwen3-72b-corp": {
        "label": "Qwen3 72B · 内网",
        "context_window": 131072,
        "tools": true, "streaming": true,
        "parallel_tool_calls": true, "vision": false, "pdf": false
      }
    }
  }
  ```

  声明优先于内置矩阵（网关可能用熟悉的模型名提供不同规格），并同时作用于能力探测、界面显示名、上下文水位条与模型建议列表。键必须是**完整路由 id**。

- **能力实测**：别靠猜。用 [templates/verify-private-model.py](templates/verify-private-model.py) 对着真实端点跑一遍：

  ```bash
  python3 docs/enterprise/templates/verify-private-model.py \
      --base-url https://llm.corp.example/v1 --model qwen3-72b-corp \
      --api-key "$CORP_LLM_KEY" --label "Qwen3 72B · 内网" \
      --context-window 131072 --emit
  ```

  它逐项实测 `/models`、基础对话、流式、工具调用、**并行工具调用**、**工具结果回传**、图片输入，给出「能不能作为企业默认模型」的结论，并直接生成上面那段 `models.json`（`--write` 可直接落盘）。「兼容 OpenAI 接口」在实践中是个光谱——收下 `tools` 却从不返回 `tool_calls`、能发起调用却不接受 `role=tool` 回执，这些都不报错，只会让 Agent 悄悄变笨，必须实测才知道。
- **凭据预置**：Provider 密钥存 `<state-dir>/secrets.json`（0600 权限），值支持 `${ENV_VAR}` 引用（配合 `<state-dir>/.env`），适合 IT 下发时不落明文。
- **企业规范注入**：把企业写作规范、术语表、合规要求写入 `<state-dir>/AGENTS.md`——每个会话的 system prompt 自动注入该文件（零代码），项目根的 `AGENTS.md` 再按项目叠加。

预置落地方式：

**① 首启自动预置（已交付，推荐）** —— `coworker/provisioning.py` 在服务启动时（`load_config()` 之前）把已发布的默认值种进空的 `<state-dir>`。企业构建把下面的目录打进安装包，设环境变量 `COWORKER_DEFAULTS_DIR` 指向它即可：

```
defaults/
  config.toml        → <state-dir>/config.toml
  models.json        → <state-dir>/models.json      # 私有模型能力声明
  mcp.json           → <state-dir>/mcp.json         # 企业 CLI / 知识库 MCP
  AGENTS.md          → <state-dir>/AGENTS.md        # 企业规范，自动进 system prompt
  skills/<name>/     → <state-dir>/skills/<name>/    # 逐个技能（含大表哥）
```

这条同时解决了此前记录的「**技能没有包内分发通道**」问题——技能终于有了随安装包下发的正规路径。

三条铁律（有测试钉住，含变异验证）：

- **不覆盖**已存在的文件——用户的就是用户的。想推「必须生效」的策略，这个机制不合适。
- **不复活**被删掉的技能——回执文件 `<state-dir>/.provisioned.json` 记着种过什么，员工删掉的东西不会在下次启动时自己回来。
- **不致命**——默认值有语法错只告警。没人应该因为一份配置里的笔误而打不开应用。

逐技能而非整目录的粒度，让后续版本能加新技能而不动员工已改过的那些。可用 `COWORKER_SKIP_PROVISIONING=1` 关闭。

**② IT 批量下发**（补充手段）：MDM/域策略直接把 `config.toml` 写到用户目录。

**③ 密钥不进默认值**：默认配置只带端点不带 Key。Key 由员工首登时输入（存本机 `secrets.json`），或对接企业统一鉴权网关按人发放。`config.toml` 与 `.env` 种下时会被设为 0600。

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
2. 员工把该目录添加为工作区/文件根，agent 即可读取检索；IT 脚本也可对运行中会话直接挂载：`POST /v1/sessions/{id}/roots`，body `{"path": "...", "writable": false}`（只读挂载）
3. 敏感子库用目录权限控制（agent 以当前用户权限访问）

> 相关目录速查：状态目录 `<state-dir>`（`$COWORKER_STATE_DIR` > `%APPDATA%\coworker` > `~/.config/coworker`）下有 `config.toml`、`secrets.json`、`mcp.json`、`skills/`、`AGENTS.md`、`models/`（whisper 语音模型）、`coworker.db`（记忆+审计）、`prefs.json` 等；会话草稿/产出默认落 `~/OpenWorker/<session_id>`（prefs 键 `scratch_base` 可改）——企业文件落盘规范应覆盖这两处。

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
