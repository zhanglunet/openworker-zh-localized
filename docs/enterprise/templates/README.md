# OpenWorker 企业定制版 · 私有仓开箱模板

这一包文件用来把 **OpenWorker 汉化版**变成一个**可持续同步、可独立发版**的企业私有仓。
四个文件覆盖四件事：把仓建起来（init）、让上游改动持续流进来（sync）、别把定制改丢了（tests）、
出企业品牌的安装包（release）。

## 三仓链路

```
andrewyng/openworker（上游，公开）
        │  sync-upstream.yml            ← 汉化仓里已有，不用管
        ▼
zhanglunet/openworker-zh-localized（汉化版，公开）
        │  sync-localized.yml           ← 本模板包提供
        ▼
<corp>/openworker-enterprise（企业私有仓）
        │  release-corp.yml             ← 本模板包提供，产出企业品牌安装包
        ▼
   企业内部装机 / 内网更新服务器
```

严格单向、逐级同步：企业仓的改动**永远不回流**到汉化仓和上游。

---

## 一、文件清单

| 模板文件 | 是什么 | 落到企业仓的路径 | 谁来安装 |
|---|---|---|---|
| `init-enterprise-repo.sh` | 一键初始化脚本：镜像汉化仓（保留完整历史）→ 建 `enterprise/` 骨架 → 生成 config/branding/mcp 模板 → 装下面三个模板文件 → 停用继承来的工作流（见下）→ 打印 A~G 人工待办清单 | 本身不进仓，在本地跑；产物落在企业仓各处（可留一份到 `enterprise/tools/`） | 人工执行 |
| `sync-localized.yml` | 汉化版 → 企业版每日同步流水线：有新提交就在 `sync/localized-main` 分支上 merge，成功开 PR、冲突开 Issue，并在 PR 上跑定制存活冒烟测试 | `.github/workflows/sync-localized.yml` | **init 脚本自动装** |
| `test_enterprise_customization.py` | 定制"存活"冒烟测试：把每一处挂载点（品牌五键、provider 注册、能力矩阵、主题 import、技能名规则）变成 pytest 断言，同步覆盖了就红 | `enterprise/tests/test_enterprise_customization.py` | **init 脚本自动装** |
| `release-corp.yml` | 企业品牌发布流水线：macOS arm64/x64 + Windows；`corp-v*` tag 触发；产物用企业前缀；生成 `latest-<corp>.json` 更新清单；**没配签名 Secrets 时自动降级为未签名内测包** | `.github/workflows/release-corp.yml` | **init 脚本自动装** |
| `skills/excel-ai-analyst/` | 大表哥表格助手技能包：SKILL.md + 配套 `excel_ai.py`（四子命令）+ references + 测试与对抗套件 | `enterprise/skills/excel-ai-analyst/` | **init 脚本自动装** |
| `skills/corp-knowledge/` | 企业知识库检索技能：先 grep 定位再精读片段，**每个结论必须给出处**（答错的代价是有人照着做了） | `enterprise/skills/corp-knowledge/` | 人工拷贝 |
| `mcp/cli-bridge/` | 企业 CLI → MCP 桥：一份 `tools.json` 声明子命令与参数，桥生成 MCP 工具定义；只放行白名单子命令、argv 直传不经 shell、超时/截断/脱敏 | `enterprise/mcp/cli-bridge/` | **init 脚本自动装** |
| `mcp/kb-server/` | 企业知识库检索 MCP server（知识库 v2）：`http` 后端对接 Confluence/语雀/自建 RAG（字段声明式映射），`folder` 后端做本地排序检索；**Agent 只拿检索结果、没有文件系统访问权** | `enterprise/mcp/kb-server/` | **init 脚本自动装** |
| `mcp/corp-api/` | 内部系统 HTTP API → MCP 桥（ERP/工单/HR/审批流）：一份 `api.json` 声明接口、参数与**响应字段白名单**，桥生成 MCP 工具；路径参数逐段转义 + URL 归一化后必须仍在 `base_url` 之下、不跟随重定向、非 GET 必须显式 `write: true`。随包两份示例**有意拆成读/写两份**（`requires_approval` 是 server 级的） | `enterprise/mcp/corp-api/` | **init 脚本自动装** |
| `connectors/corp/` | 原生连接器描述符模板：要 GUI 卡片 + **逐工具审批**时才用。需要内网有 OAuth 2.1 + DCR 的 HTTP MCP 端点，外加 5 行挂载点 | `enterprise/connectors/corp/` → 人工放到 `coworker/connectors/corp/` | init 脚本装到 `enterprise/`，**挂载点由人工加** |
| `verify-private-model.py` | 私有模型接入验证：对企业自建的 OpenAI 兼容端点实测能力矩阵（含并行工具调用、工具结果回传），产出结论与可直接用的 `models.json` | 不进仓，拿到端点时跑一次 | 人工执行 |

> init 脚本默认从**自己所在目录**找模板（`-t/--templates` 可改），三个模板文件（两个 `.yml`
> 加一个 `.py`）它都会装；缺哪个就 warn 并跳过哪个。所以请**整包一起下载/拷贝**，
> 在包目录里执行脚本。

### init 还会做一件容易被忽略的事：停用继承来的工作流

镜像汉化仓会把汉化版的全部工作流一起带进企业仓。init 把其中会"抢 main"或"发错品牌包"的
几个改名成 `*.yml.disabled`（GitHub 只识别 `.github/workflows` 下的 `.yml` / `.yaml`）：

| 被停用 | 原因 |
|---|---|
| `sync-upstream.yml.disabled` | 每天直接从 `andrewyng/openworker` 同步，绕过汉化层，且与 `sync-localized.yml` 抢同一个 `main` |
| `release.yml.disabled` / `prerelease.yml.disabled` / `build-windows.yml.disabled` | 用汉化版品牌和 `latest-zh.json` 发包；企业发布走 `release-corp.yml`（`corp-v*` tag） |
| `update-site-reports.yml.disabled` | 定时以 `contents: write` 直接 push 回 `main` |
| `deploy-site.yml.disabled` | 把内容部署到汉化版公开站点 |

**不要把它们改回来。** 保留 `.disabled` 文件而不是删除，是为了让后续同步时 git 的改名检测
还能把上游对这些文件的修改跟上，不至于每轮都冲突。

推 `v*` / `app-v*` tag 在企业仓里不会有任何反应，就是因为 `release.yml` 已被停用 —— 企业发布
只认 `corp-v*`。

---

## 二、使用顺序

### 第 0 步 · 准备

- 在企业 GitHub（或 GitHub Enterprise）里建一个**空的**私有仓，例如 `acme/openworker-enterprise`
  （不要勾 README/.gitignore，必须是空仓）。
- 本地准备好 `git ≥ 2.23`、`bash 4+`、`python3`。
- 想好两个标识（后面到处都要用，**定了就别改**）：
  - `CORP_ID`：小写 ASCII 短名，如 `acme`。会成为技能名前缀、模型路由 id 前缀、
    更新清单文件名 `latest-acme.json` 的一部分。
  - 企业中文名，如 `艾克米科技`，用于品牌文案。

### 第 1 步 · 跑 init 脚本

```bash
cd <模板包目录>
chmod +x init-enterprise-repo.sh

# 先空跑，看清楚它要做什么（不写文件、不联网）
./init-enterprise-repo.sh -c acme -N 艾克米科技 \
    -r git@github.com:acme/openworker-enterprise.git --dry-run

# 确认无误后真跑
./init-enterprise-repo.sh -c acme -N 艾克米科技 \
    -r git@github.com:acme/openworker-enterprise.git
```

常用开关：`--skip-mirror`（私有仓已有内容）、`--no-push`（只在本地提交）、
`--force`（覆盖已存在的模板文件）、`-y/--yes`（跳过交互确认，CI 用）、`-h` 看完整帮助。

脚本跑完会打印一份 **A~G 人工待办清单**，第 2~5 步就是在做那份清单。

### 第 2 步 · 把冒烟测试接进 CI

三个模板文件（`sync-localized.yml`、`release-corp.yml`、`test_enterprise_customization.py`）
init 都已经装好了，不需要再手工复制。这一步只剩一处上游文件要改（init 清单的 **F1**）——
`.github/workflows/ci.yml`：

```diff
-        run: pytest tests -q
+        run: pytest tests enterprise/tests -q
```

> ⚠️ **改完 CI 一定是红的，这是设计如此**（init 清单 F3 也这么写）。冒烟测试里那些
> "不许等于汉化版旧值"的**负向**断言不依赖任何配置、永远执行，而此刻 `tauri.conf.json`
> 还是汉化版的品牌值。所以合理的顺序是：**先做完第 3~4 步的品牌改造，再合这个 diff**；
> 或者先合、并接受 `main` 红到品牌改完为止。别把红灯当成模板坏了。

### 第 3 步 · 平台设置与 Secrets

**（a）合并策略 —— 全清单里最要命的一条**

Settings → General → Pull Requests：**只保留 "Allow merge commits"**，关掉 squash 与 rebase。

> 同步 PR 必须用 **merge commit** 落地。squash 会把汉化版的一串提交压成一个全新提交，
> 企业仓 `main` 就不再是 `localized/main` 的后代，祖先链断掉；下一次同步时
> `git merge-base --is-ancestor` 恒为假，**汉化版全部历史会被重放一遍**，
> 已经解决过的冲突全部复发，而且每同步一次多累积一轮。rebase 同理（改写 SHA）。

**（b）Actions 权限**

Settings → Actions → General → Workflow permissions：勾 "Read and write permissions"，
并勾 "Allow GitHub Actions to create and approve pull requests"（不勾第二项，
`sync-localized.yml` 里的 `peter-evans/create-pull-request` 会直接报错）。

**（c）Secrets / Variables**（详表见下方第四节）

只想先出内测包的话，这一步**什么都不用配** —— 直接跳到第 5 步的"发布链路"打 `corp-v*` tag。

### 第 4 步 · 跑冒烟测试，拿它当改造清单

```bash
python -m pip install -e ".[messaging,dev,bedrock]"
pytest enterprise/tests -q
```

**刚初始化完、品牌还没改时它是红的，不是 skip。** 实测（企业目录已由 init 生成、品牌未动）：

```
9 failed, 5 passed, 3 skipped
```

skip 只发生在**汉化仓/上游仓**里（没有 `enterprise/` 目录，`@requires_enterprise` 整体跳过）；
企业仓里 `enterprise/` 存在，那些"不许等于汉化版旧值"的负向断言就一定会跑、一定会红。

正确用法是**把这 9 条红当待办清单**，每改完一处就少一条：

| 红的用例 | 对应待办 |
|---|---|
| `test_brand_fields_are_enterprise_values` | D1：改 `productName` / `identifier` / `bundle.publisher` |
| `test_updater_endpoints_point_at_enterprise_host` | D1：改 `plugins.updater.endpoints`（见第六节，**必须走方式 B 才能变绿**） |
| `test_updater_pubkey_is_not_the_localized_key` | D1：换成企业自己的 minisign 公钥 |
| `test_enterprise_theme_css_is_mounted` / `..._covers_light_and_dark` | D2：改 `main.tsx` 的 import + 填 `theme.css` |
| `test_enterprise_skills_present` | 往 `enterprise/skills/` 放至少一个技能 |
| `test_enterprise_models_registered_in_matrix` | E1：`MATRIX` 里加企业模型 |
| `test_enterprise_config_default_is_valid_and_prefixed` / `test_enterprise_mcp_templates_are_valid` | 填 `config.default.toml` / `mcp.example.json` 里的占位值 |

### 第 5 步 · 验证两条链路

**同步链路**：Actions → "同步汉化版到企业版" → Run workflow，确认能拉到汉化仓并开出 PR。
合并时选 **"Create a merge commit"**。合并后在本地验证祖先链：

```bash
git remote add localized https://github.com/zhanglunet/openworker-zh-localized.git  # 只需一次
git fetch localized
git merge-base --is-ancestor localized/main HEAD && echo "祖先链通" || echo "断链了"
```

> ⚠️ **不要用 `git merge-base HEAD localized/main` 判断**。即使上一轮被 squash 掉、祖先链已经
> 断了，它照样会输出一个 SHA（squash 之前那个真正的共同祖先还在）——实测确认过，这个判据
> 恒为"有输出"，等于没判。只有 `--is-ancestor` 才是 `sync-localized.yml` 里真正用的那条判据。

**发布链路**：`surfaces/gui/src-tauri/tauri.conf.json` 当前 `version` 是 `0.1.7`，所以

```bash
git tag corp-v0.1.7 && git push origin corp-v0.1.7   # tag 里的版本号必须等于 conf 里的 version
```

要发新版就先把 conf 里的 `version` 改成 `0.1.8`，再打 `corp-v0.1.8`。
流水线会先做预检（tag 格式、版本号一致性、企业短名合法性、品牌五键、更新端点），再跑三平台构建。

---

## 三、最小可用路径（只想先跑起来的 5 步）

不办证书、不搞内网托管、不换图标，先让企业仓转起来并拿到能装的包：

1. **建空私有仓 → 跑 init 脚本**
   ```bash
   ./init-enterprise-repo.sh -c acme -N 艾克米科技 -r git@github.com:acme/openworker-enterprise.git
   ```
2. **改仓库设置**：只允许 merge commits；Actions 开 "Read and write" + "允许创建 PR"。
3. **先别改 ci.yml**（第 2 步那个 diff）——品牌没改完之前接上门禁只会让 `main` 一直红。
4. **出内测包**：一个签名 Secret 都不配，直接
   `git tag corp-v0.1.7 && git push origin corp-v0.1.7`（版本号取自 `tauri.conf.json`）。
   流水线检测到没有签名 Secrets，自动走**未签名分支**：发成 GitHub **prerelease**，
   剥掉全部更新物料，附中文安装说明和 SHA256 校验和。三平台安装包当天就能发给测试同事。
   这条路**不要求**品牌改完 —— 未签名模式下品牌预检只告警不拦截。
5. **手动跑一次同步工作流**，确认 PR 能开出来；合并时用 merge commit。

到这一步企业仓已经"活"了：能同步、能发包。之后再按需推进：
换品牌五键 → 换图标与主题 → 冒烟测试转绿 → 接上 ci.yml 门禁 →
办 Apple/Windows 证书 → 配内网更新托管 → 加企业技能与模型。

> ⚠️ 未签名包只适合内网测试：macOS 首次打开要 `sudo xattr -rd com.apple.quarantine "/Applications/<App>.app"`，
> Windows 会弹 SmartScreen。它**不接入自动更新**，既不会推给已安装的正式版用户，自身也不会自动升级。

---

## 四、Secrets / Variables 速查

在 Settings → Secrets and variables → Actions 配置。**Variables 是明文，Secrets 才是机密。**

### Variables（`release-corp.yml` 用）

| 名称 | 必填 | 说明 |
|---|---|---|
| `CORP_NAME` | 建议 | 产物名前缀，ASCII，如 `AcmeWorker` → `AcmeWorker-macos-arm64.dmg`。默认 `AcmeWorker` |
| `CORP_ID` | 建议 | 更新清单短名，如 `acme` → `latest-acme.json`。**必须与 `tauri.conf.json` 的 `plugins.updater.endpoints` 里的文件名一致**。默认 `acme` |
| `CORP_UPDATE_BASE_URL` | 否 | 内网更新分发根 URL；留空则更新清单指向私有仓 Release |
| `CORP_UPDATE_UPLOAD_URL` | 否 | 更新包上传接口根 URL（HTTP PUT）；配了才会执行上传步骤 |
| `CORP_WRITE_SITE_FALLBACK` | 否 | 设为 `true` 时把清单回写到 `enterprise/site/` |

> `CORP_NAME` / `CORP_ID` 都必须匹配 `^[A-Za-z0-9][A-Za-z0-9._-]*$` —— 和技能名用的是同一套规则，
> 流水线预检会卡住中文和空格。企业中文名放 `enterprise/config/branding.json` 的 `productName`。

### Secrets

| 名称 | 用途 | 不配的后果 |
|---|---|---|
| `APPLE_CERTIFICATE` / `APPLE_CERTIFICATE_PASSWORD` / `APPLE_SIGNING_IDENTITY` | macOS 签名（base64 `.p12` + 密码 + `Developer ID Application: … (TEAMID)`） | 走未签名内测分支 |
| `APPLE_API_KEY_CONTENT` / `APPLE_API_KEY` / `APPLE_API_ISSUER` | macOS 公证（base64 的 App Store Connect `.p8` + Key ID + Issuer ID） | 同上 |
| `TAURI_SIGNING_PRIVATE_KEY` / `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | 自动更新包签名（minisign，与 Apple 签名无关）。公钥填进 `tauri.conf.json` 的 `plugins.updater.pubkey`，生成：`npx @tauri-apps/cli signer generate -w ~/.tauri/<corp>.key` | 同上；且没有更新清单 |
| `WINDOWS_CERTIFICATE` / `WINDOWS_CERTIFICATE_PASSWORD` | Windows Authenticode（base64 `.pfx` + 密码），**可选** | Windows 包不签名，用户看到 SmartScreen 警告；其余照常 |
| `CORP_UPDATE_UPLOAD_TOKEN` | 内网上传凭据（Bearer） | 仅在配了 `CORP_UPDATE_UPLOAD_URL` 时需要 |
| `LOCALIZED_REPO_TOKEN` | `sync-localized.yml` 拉汉化仓用。汉化仓是公开仓时**不需要** | 私有化汉化层时同步会 403 |

> ⚠️ **名字以 `sync-localized.yml` 为准：`LOCALIZED_REPO_TOKEN`。** init 脚本打印的待办清单
> C1 项里把它写成了 `LOCALIZED_SYNC_TOKEN`，那是笔误；工作流里 `secrets.` 读的是
> `LOCALIZED_REPO_TOKEN`，配错名字等于没配（而且因为它本来就可选，会静默退回匿名拉取，
> 私有汉化仓下表现为 403）。

> 公证方式说明：`packaging/build_dmg.sh` 走的是 **App Store Connect API Key**
> （`notarytool --key/--key-id/--issuer`），不支持 `APPLE_ID` + 应用专用密码那一套。
> Secrets 名称一律以 `release-corp.yml` 文件头部的清单为准。
>
> 这组名称与汉化仓 `.github/workflows/release.yml` **保持一致**，已有的证书托管流程和运维文档可以直接复用。

---

## 五、定制放哪里（改上游文件 = 会冲突，属于预期）

**独立目录**（同步时几乎不冲突，放心堆）：

```
enterprise/
├── skills/      企业技能包（技能名只允许 ASCII：^[A-Za-z0-9][A-Za-z0-9._-]*$）
├── branding/    theme.css（init 生成）、图标源文件；
│                可选放一个 apply_branding.sh —— 存在时发布流水线会自动执行它，
│                用来把图标覆盖到 surfaces/gui/src-tauri/icons/
├── config/      config.default.toml + branding.json（都由 init 生成，里面是**占位值**）；
│                branding.json 是冒烟测试读期望品牌值的地方 —— 改 tauri.conf.json 时
│                必须同步改它，否则测试会报"品牌被同步覆盖"
├── mcp/         mcp.example.json（init 生成）
├── connectors/  企业连接器
├── tools/       运维脚本（可以把 init-enterprise-repo.sh 留一份在这）
├── tests/       test_enterprise_customization.py
└── site/        内网站点 / 更新清单兜底
```

**挂载点**（少量落在上游文件里，每次同步都要盯）：

| 文件 | 改什么 |
|---|---|
| `surfaces/gui/src-tauri/tauri.conf.json` | `productName` / `identifier` / `bundle.publisher` / `plugins.updater.endpoints` / `plugins.updater.pubkey` |
| `surfaces/gui/src/main.tsx` | 在 `import "./styles.css";` **之后**追加 `import "../../../enterprise/branding/theme.css";`（顺序反了覆盖不掉 `:root` 变量） |
| `surfaces/gui/src-tauri/icons/` | 至少换 `32x32.png` / `128x128.png` / `128x128@2x.png` / `icon.icns`（macOS）/ `icon.ico`（Windows）；别漏了 `icon.png`（源图）和 `tray.png` / `tray.rgba`（托盘图标，用户天天看见）。Windows Store 那组 `Square*Logo.png` / `StoreLogo.png` 不打包分发的话可以先不动 |
| `coworker/providers/registry.py` | `DESCRIPTORS` 里增/改条目；OpenAI 兼容自定义端点用 `name="custom"`，字段 `base_url` / `api_key` / `model` |
| `coworker/providers/matrix.py` | `MATRIX` 新增企业模型，**键是完整路由 id**，如 `"custom:acme-chat"` |
| `.github/workflows/ci.yml` | `pytest tests -q` → `pytest tests enterprise/tests -q` |

`test_enterprise_customization.py` 逐条盯着上面这张表 —— 同步把哪条冲掉了，CI 立刻标红。

**技能放置位置**：全局 `<state-dir>/skills/<name>/SKILL.md`，项目级 `<workspace>/.coworker/skills`。
`state_dir` 解析顺序：`$COWORKER_STATE_DIR` > `%APPDATA%\coworker`（Windows）> `~/.config/coworker`。
`base_url` / `api_key` 走 GUI 的 provider 配置界面（进 SecretStore），**不要写进 `config.toml`**。

---

## 六、更新包托管：两种选法

`release-corp.yml` 两种都支持，靠 Variables 切换：

| | 方式 A · 私有仓 Release（默认） | 方式 B · 内网静态服务器 / 对象存储（推荐） |
|---|---|---|
| 怎么开 | `CORP_UPDATE_BASE_URL` 留空 | 设 `CORP_UPDATE_BASE_URL`（+ `CORP_UPDATE_UPLOAD_URL` 才会自动上传） |
| 清单 URL | `https://github.com/<owner>/<repo>/releases/download/<tag>/<资产>` | `<CORP_UPDATE_BASE_URL>/<tag>/<资产>` |
| 坑 | **私有仓的 Release 资产必须带凭据才能下载**，Tauri updater 默认不带；要用得在 `plugins.updater` 里加 `headers` 把只读 token 发到客户端 —— 只适合仓库设为 internal、装机范围可控的场景 | GitHub 托管 runner **访问不到企业内网**，要么把 publish job 换成 self-hosted runner，要么给上传接口做带鉴权的公网入口 |
| 冒烟测试 | ❌ **必红** | ✅ 可全绿 |

> ⚠️ **方式 A 与本模板包自带的冒烟测试互斥。**
> `test_enterprise_customization.py` 的 `FORBIDDEN_UPDATER_MARKERS` 把 `github.com` /
> `githubusercontent.com` / `openworker.com` 一律判为"非企业域"，只要 `endpoints` 里出现
> 就直接 fail。而方式 A 的清单 URL 天生就是 `https://github.com/...`。
> 所以：**方式 A 只适合还没接自动更新的内测阶段**（内测包本来就不产出更新清单，
> `endpoints` 可以先保持不动）；一旦要让 `enterprise/tests` 全绿并接进 CI 门禁，
> 就必须换成方式 B —— `vars.CORP_UPDATE_BASE_URL` 指向企业自己的域名（内网站点、
> 对象存储自定义域，或企业站对 Release 做反代），并把 `enterprise/config/branding.json`
> 的 `updaterHost` 填成同一个域名。
> `release-corp.yml` 的预检发现 `endpoints` 里有公共域时会发一条 `::warning::` 提醒这件事，
> 但**不拦截**（否则内测阶段没法出包）。

清单一定要以 `no-cache` 发布（CDN 缓存会让客户端看不到新版本），流水线注释里给了 rsync / S3 两种替换写法。

> 只设了 `CORP_UPDATE_BASE_URL`、没设 `CORP_UPDATE_UPLOAD_URL` 时，清单会指向一个流水线
> 从没往里传过文件的地址（客户端拿 404 后静默停在旧版）。这种组合流水线会发 `::warning::`，
> 除非你另有分发流程负责把 `dist/` 放上去。

---

## 七、排错

| 现象 | 原因 / 处理 |
|---|---|
| 同步 PR 每次都是几百个冲突 | 上一轮用 squash 合并了，祖先链断了。确诊：`git merge-base --is-ancestor localized/main HEAD`（退出码非 0 = 断链）。**别用 `git merge-base HEAD localized/main`，它照样输出 SHA，判不出来。** 补救：手工做一次 `git merge localized/main` 把祖先链接回来，然后**立刻关掉 squash** |
| `GitHub Actions is not permitted to create or approve pull requests` | Actions 权限没勾 "Allow GitHub Actions to create and approve pull requests" |
| 发布流水线预检报 `tag ... 与 tauri.conf.json version ... 不一致` | 先改 `tauri.conf.json` 的 `version` 再打 tag。允许 `corp-v0.1.8` 和 `corp-v0.1.8-acme.1` 两种写法 |
| 预检报 `productName 仍是上游/汉化版默认值` | 品牌五键没改完。**正式签名版会直接 fail，未签名内测版只告警**，所以内测阶段能照常出包 |
| 预检报 `endpoints 里没有一条指向 latest-<corp>.json` | `vars.CORP_ID` 和 `tauri.conf.json` 的 endpoints 对不上，改到一致 |
| 装上去的包还会去公开仓拉更新 | `plugins.updater.endpoints` 还指着 `zhanglunet/openworker-zh-localized`，预检会拦，别绕过 |
| 企业模型在 GUI 里选不到 | `MATRIX` 的键不是完整路由 id（要 `custom:xxx`，不是 `xxx`） |
| 刚初始化完冒烟测试就是红的（9 failed） | **这是预期**，不是模板坏了。见第 4 步那张对照表，逐条改完就绿。红的原因是负向断言（"不许等于汉化版旧值"）不依赖任何配置、永远执行 |
| 冒烟测试全 skip | 说明 `enterprise/` 目录没被找到 —— 你多半是在**汉化仓/上游仓**里跑，或者 `OPENWORKER_ENTERPRISE_DIR` 指错了地方。在企业仓里全 skip 属异常，等于门禁没生效 |
| 品牌类断言"跳过"而不是比对 | 负向断言（不许等于旧值）永远跑；**正向**比对需要期望值。init 生成的 `branding.json` 只写了 `productName` / `identifier` / `publisher` / `updaterHost`，**有意不写** `providers` / `models` —— 这两项回落到 `enterprise/config/config.default.toml` 的 `model` 前缀与 `model` 本身，少一处要手工同步的重复配置。也可用 `OPENWORKER_ENTERPRISE_*` 环境变量覆盖 |
| 推了 `v0.1.7` tag 却没有任何构建 | 企业发布只认 `corp-v*`；`release.yml` 已被 init 改名成 `.disabled`。预检也会直接报 `tag "v0.1.7" 不合法` |
| Windows 更新装不上、提示签名不匹配 | Authenticode 签名后必须**重算** `.sig`（`.sig` 签的是内容）。流水线已处理并做了失败断言，别把那步删了 |

---

## skills/excel-ai-analyst —— 大表哥表格助手技能包

企业员工最高频的表格场景：一张跑了多年的业务 Excel，没人说得清里面的公式怎么串的。
本技能把它当作**没有文档的遗留代码**做逆向工程（PRD F4 的 L1 层）。

```
skills/excel-ai-analyst/
├── SKILL.md              # 技能本体：五步法 + OpenWorker 适配（审批白名单、resources_path 等）
├── scripts/excel_ai.py   # 配套脚本，四个子命令：tomd / verify / output / analyze
├── references/           # spec-schema.md（spec.json 全字段）/ pitfalls.md（踩坑）/ walkthrough.md（完整演练）
└── tests/                # 68 项基础用例 + 三套对抗套件（详见 tests/README.md）
```

**为什么值得随技能分发脚本**：原方法论只写"找不到 `excel_ai.py` 就现写一份"——
每个员工每次得到的实现质量都不一样。企业版把它实现好、测透，一次到位。

**装到哪**：`init-enterprise-repo.sh` 自动装到 `enterprise/skills/excel-ai-analyst`。
要让它对员工生效，还需同步到运行时技能目录（初始化清单 E 步）：

```bash
cp -r enterprise/skills/excel-ai-analyst "${COWORKER_STATE_DIR:-$HOME/.config/coworker}/skills/"
```

**员工要做的一件事**：把 `python3` 加进 `~/.config/coworker/config.toml` 的
`allowed_commands`，否则每一步脚本调用都会弹审批（SKILL.md 里有更保守的按脚本路径放行写法）。

**企业采纳的关键点**：脚本纯本地、零网络调用，表格数据不出内网。
