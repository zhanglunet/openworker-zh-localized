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

### 形态 A：公网企业站（`enterprise/site` + Cloudflare Workers）✅**已交付**

init 脚本已经把站点装好了：`enterprise/site/`（下载页 + 企业介绍，纯静态 assets-only
Worker，不引入 Next.js 构建）+ `.github/workflows/deploy-corp-site.yml`。

**三步有先后依赖，顺序错了会卡住**：Worker 必须先存在才能绑域名；安装包超过 Worker
的单文件上限，所以要单独建对象存储。

#### A1. Cloudflare API Token → GitHub Secret

1. Cloudflare → 右上角头像 → **My Profile** → **API Tokens** → **Create Token**
2. 用模板 **「Edit Cloudflare Workers」** → **Use template**
3. 只改两处：**Account Resources** 选目标账号；**Zone Resources** 选企业域名
   （域名还没进 Cloudflare 就先选 All zones，A2 做完再回来收紧）
4. **Continue to summary** → **Create Token** → **立刻复制**（页面关掉就再也看不到）
5. 企业仓 Settings → Secrets and variables → Actions → **New repository secret**：
   - `CLOUDFLARE_API_TOKEN` = 刚才那串
   - `CLOUDFLARE_ACCOUNT_ID` = Workers & Pages 页面右栏的 Account ID
     —— **仅当 token 能访问多个账号时才需要**

> ⚠️ Secret 名字必须逐字一致、区分大小写。写错不会报错：工作流只打一条
> 「未配置，跳过部署」的 notice 然后**绿灯通过** —— 看起来一切正常，实际什么都没发。
> 这是有意设计（没配凭据不该让流水线常红），代价就是拼错会静默。

配好后手动跑一次 `Deploy 企业站`，Worker `openworker-<corp-id>-site` 才真正存在。

#### A2. 绑定企业域名

**前置**：域名得先是这个 Cloudflare 账号下的站点（首页站点列表里状态 **Active**）。
还没有的话：Add a site → 输入域名 → 选套餐 → 拿到两个 Cloudflare 名称服务器 →
去注册商后台把域名 NS 改成它们 → 等状态变 Active。

然后：Workers & Pages → 点 `openworker-<corp-id>-site` → **Settings** →
**Domains & Routes** → **Add** → **Custom Domain** → 填域名 → Add domain。

Cloudflare 自动建 DNS 记录并签发证书，一两分钟后即可访问。

> 域名绑定**不在代码里**，只存在于 Cloudflare 控制台 —— `deploy 成功 ≠ 域名可访问`。

#### A3. 安装包托管（R2）

安装包**不能**放进 `enterprise/site/public/`：Cloudflare Workers 静态资源
**单文件上限 25 MiB**，而桌面端 DMG 通常 60–80 MB，会直接部署失败。
私有仓的 GitHub Release 直链也不行 —— 员工匿名访问是 404。

用 R2（同账号，免出网流量费）：

1. Cloudflare 左侧 → **R2 Object Storage** → 首次使用需激活
2. **Create bucket** → 如 `<corp>-openworker-releases`
3. 进桶 → **Settings** → **Custom Domains** → **Connect Domain** → 如 `dl.<企业域名>`
   （**别用自带的 `*.r2.dev`** —— 有速率限制，只适合调试）
4. **Upload** 三个安装包（macOS arm64 `.dmg`、macOS x64 `.dmg`、Windows `.msi`）
5. 填 `enterprise/site/public/downloads.json`：

```json
{
  "version": "0.1.0",
  "released": "2026-08-06",
  "files": {
    "mac-arm64":   { "url": "https://dl.example.com/App-0.1.0-aarch64.dmg", "size": "72 MB" },
    "mac-x64":     { "url": "https://dl.example.com/App-0.1.0-x64.dmg",     "size": "78 MB" },
    "windows-x64": { "url": "https://dl.example.com/App-0.1.0-x64.msi",     "size": "65 MB" }
  }
}
```

三个 key 是固定的（与页面里的 `PLATFORMS` 一一对应，`tests/test_corp_site.py` 钉着）。
`url` 留空页面显示「即将开放」，不是坏链接。改完推送即自动重新部署。

> **R2 顺带解开 1.7 和 D1 的一半**：把 `tauri.conf.json` 的
> `plugins.updater.endpoints` 指向同一个桶的 `latest-<corp-id>.json`，
> 冒烟测试 `test_updater_endpoints_point_at_enterprise_host` 就能变绿 ——
> 它把 `zhanglunet` / `andrewyng` / `github.com` / `githubusercontent.com` /
> `openworker.com` 一律判为「非企业域」，企业自有域名不在黑名单里。

#### A4. 两条不能破的红线（`deploy-corp-site.yml` 里各有守卫）

1. **不能覆盖汉化站。** 汉化站 oaosf.cn 的 Worker 叫 `openworker-cn-site`，而企业仓是
   从汉化仓镜像来的，`website/wrangler.jsonc` 里那个名字一直在树里 —— 同账号下同名
   部署会直接把线上站顶掉，wrangler 不会问你一句。部署前查两处：解析出的 Worker 名、
   以及 `enterprise/site/wrangler.jsonc` 的 `name` 字段。
2. **不能把内部信息发到公网。** 部署前扫 `public/`，内网域名、私网 IP、疑似凭据一律
   拒绝部署 —— 发出去就已经被抓取了，撤回也晚了。

#### A5.（可选）沿用汉化站那套 Next.js 站

想要源码分析等完整页面时才走这条。三个已知缺口：

- **会公开仓库提交记录**：`scripts/generate-site-reports.mjs` 把最近提交发布到页面上。
  在企业仓里那等于公开企业开发动态 —— 这正是 `enterprise/site/` 不继承它的原因。
- **IMAGES 绑定缺失**：`worker/index.ts` 的 `/_vinext/image` 端点调用 `env.IMAGES`，
  但 `wrangler.jsonc` 未声明 images 绑定 —— 照抄配置部署后该端点会运行时报错。
- **站点测试断言要同步改**：`tests/rendered-html.test.mjs` 硬编码了「OpenWorker 中文站」、
  DMG 文件名、SHA-256、Bundle ID 与双仓库链接。

走这条务必先把 `wrangler.jsonc` 的 `name` 改掉，否则就是 A4 第 1 条那个后果。

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

**① 常驻挂载（已交付，推荐）** —— 全局配置里声明，每个会话自动只读挂载，员工不必手工添加：

```toml
# <state-dir>/config.toml
knowledge_roots = ["~/CorpKB", "/Volumes/Shared/制度"]
```

三条性质：**永远只读**（常驻共享目录的写权限不该由一行配置发出去）、**工作区配置不能声明**（否则一个克隆下来的仓库写上 `knowledge_roots = ["~/.ssh"]` 就等于自己给自己发钥匙，与 `allowed_commands` 同级别管控）、**不持久化进会话**（管理员从配置里移除，访问权限就真的没了，不会在旧会话里阴魂不散）。路径不存在时静默跳过——同步盘还没下完不该让人开不了会话。

**② 临时挂载**：员工把目录添加为工作区文件根；IT 脚本也可对运行中会话直接挂：`POST /v1/sessions/{id}/roots`，body `{"path": "...", "writable": false}`。

**③ 检索技能**：预置 [templates/skills/corp-knowledge/](templates/skills/corp-knowledge/)，教模型「先 grep 定位、再精读片段」，并强制**每个结论给出处**——企业知识库里答错的代价不是回答质量差，是有人照着做了。

**④ 敏感子库**用目录权限控制（agent 以当前用户身份访问，读不到的就是读不到）。

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
├── cli-bridge/        # ✅ 已交付：通用 CLI → MCP 桥（配置驱动，不必每个 CLI 手写一个 server）
├── kb-server/         # ✅ 已交付：知识库检索 MCP server（知识库 v2）
└── corp-api/          # ✅ 已交付：内部系统 HTTP API → MCP 桥（ERP/工单/HR/审批流）
enterprise/connectors/
└── corp/              # ✅ 已交付：原生连接器描述符模板（要 GUI 卡片 + 逐工具审批时用）
```

> 内部系统（ERP/工单/HR）怎么接、两条路线怎么选、写操作怎么保证每次都弹框，
> 见 **[CONNECTOR_GUIDE.md](CONNECTOR_GUIDE.md)**。一句话版：默认走 `corp-api` 声明式桥
> （零上游改动），**读写必须拆成两个 MCP server 条目**——`requires_approval` 是 server 级的，
> 混在一起要么查订单也弹框、要么关单也不弹。

### 知识库 v2：什么时候需要它

v1（`knowledge_roots` 目录挂载）零成本、够用，但有三件事做不到，任一成立就该上 v2：

| v1 做不到 | 为什么 |
|-----------|--------|
| 知识库不是文件系统 | Confluence、语雀、自建 RAG 只有 HTTP 接口，挂不了盘 |
| 权限要按人校验 | 挂载是「这台机器上这个用户能读的目录」，合规要的是「这个人在知识库里有权看的内容」——只有知识库自己能回答 |
| 检索质量 | grep 在几万篇文档上又慢又只会字面匹配 |

v2 把知识库放在 MCP 后面：Agent 只能调 `kb_search` / `kb_get`，**拿不到文件系统访问权**，每次调用带调用方凭据打到知识库，能看什么由知识库说了算。知识内容不进仓库、不进安装包。

两种后端一份配置切换：`http`（对接已有检索服务，响应字段声明式映射，不必为每家写代码）、`folder`（对文档目录做本地排序检索，给还没有检索服务的团队先用起来——注意它与 v1 的区别仍是**不把目录挂给 Agent**）。

```bash
python3 server.py --config kb.json --check --query 报销   # 不启动服务，先试搜一次
```

**CLI 桥怎么用**（[templates/mcp/cli-bridge/](templates/mcp/cli-bridge/)）：用一份 `tools.json` 声明「哪些子命令、各自什么参数」，桥自己生成 MCP 工具定义。

```bash
python3 server.py --spec tools.json --check   # 先校验并列出工具，不启动服务
```

**为什么不直接把 `corp-cli` 加进 `allowed_commands`**：那等于把整个 CLI 的全部子命令、全部参数都交出去，包括 `delete`、`--force`、以及你没想到的那些。桥反过来做——只有白名单里显式声明的子命令能被调用，参数名/类型/枚举逐个校验，未声明的参数是**拒绝**而不是忽略（静默忽略会让调用方以为 `--force` 生效了）。

其余边界：argv 直传不经 shell（`;` `|` `$()` 只会是普通字符串实参）、每次调用有超时、输出超长截断、按正则脱敏后才回给模型、环境变量按白名单传递而非整个继承。

知识库权限在 MCP 服务端按调用者校验，知识内容不进安装包。也可通过 `POST /v1/mcp` 由脚本写入配置。

## 5.4 目录白名单：只留企业批准的入口

```toml
# <state-dir>/config.toml（全局专属）
allowed_connectors = ["github", "jira"]      # 留空 = 不限制
denied_connectors  = ["gmail", "slack"]      # 与 allowlist 冲突时，拒绝优先
allowed_providers  = ["custom", "ollama"]
denied_providers   = ["openai", "anthropic"]
```

**隐藏不等于禁止**，所以四处都拦：

| 执行点 | 拦什么 |
|--------|--------|
| `connector_list()` | UI 列表 —— 同时也是 agent 工具装配的数据源，所以被拒的连接器**工具根本不会被装进去** |
| `connect_connector()` | 手写 API 请求也连不上 |
| `provider_descriptors()` | 设置页里不出现被拒的模型厂商 |
| `build_provider_client()` | 每次模型调用的唯一漏斗 —— 旧的存储档案、会话里手打的模型 id、指向已禁厂商的配置，全都在这里被拒 |

## 5.5 审计外发到企业 SIEM

```toml
audit_forward_url     = "https://siem.corp.internal/ingest"
audit_forward_token   = "${CORP_SIEM_TOKEN}"   # Bearer；${VAR} 从环境读，不必写进配置
audit_forward_batch   = 50
audit_forward_timeout = 5
```

按优先级排的三条承诺，各有测试钉着：

1. **一轮对话绝不等 SIEM** —— 后台线程发送，`send()` 只入队。收集器要 30 秒才回，用户零感知。
2. **SIEM 挂了绝不影响 Agent** —— 所有失败路径吞掉并降频记日志。不存在「日志收集器不可达」导致人干不了活的配置。
3. **本地日志始终是事实来源** —— 先落 SQLite 再外发。外发丢了是 SIEM 的缺口，永远不是审计链的缺口。

队列有界，满了**丢旧留新**并计数：无界队列是拿看得见的缺口换看不见的内存增长，而队列满本身就说明收集器已经落后了，新事件才是排查要看的。脱敏复用本地那一套规则——磁盘上被打码的，线上也一定被打码，不是另写一套会漂移的规则。

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
