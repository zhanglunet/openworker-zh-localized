# Playbook 第 3 章：部署（正文）

> PRD-030/T4（trend #184）。依据 `docs/enterprise/DEPLOYMENT.md`（v1.0，2026-08-04）
> 及 `docs/enterprise/templates/` 下 `release-corp.yml`、`deploy-corp-site.yml`、
> `init-enterprise-repo.sh` 萃取。与 T1 大纲
> （`docs/plans/2026-10-17-enterprise-playbook-outline.md`）第 3 章对应。

## 0. 本章定位

| | 内容 |
|---|---|
| 输入 | 第 1 章产出的企业版安装包（macOS DMG / Windows 安装器）+ 第 2 章产出的三仓版本对应表 |
| 输出 | 下载站可下载 + 版本留档 + 发布日志已更新 |
| 读者 | 执行本次企业版发布的负责人（按顺序走，检查清单全勾才算完） |

本章只讲"发布出去"：构建签名 → 分发托管 → 下载站 → 留档 → 回滚。
私有仓建立与同步流水线是第 2 章的事，本章只保留"一次做对"的最小前置（§2.2）。

## 1. 前置准备清单（开工前办齐）

来源：DEPLOYMENT.md §0。凡是"办理周期以周计"的，现在就启动，别等到发布当天。

| 项 | 说明 | 责任方 | 备注 |
|---|---|---|---|
| GitHub 组织 + 私有仓权限 | `<corp>/openworker-enterprise`（私有） | IT | 代码不许出内网就用企业 GitLab/Gitea 同理 |
| Apple Developer Program（组织账号） | Developer ID 证书 + Notary API Key | IT/法务 | 办理周期 1–2 周，尽早启动；macOS 签名公证必需 |
| Windows 代码签名证书 | OV 起步，EV 更佳（可后补） | IT | 不配则 Windows 包未签名，会弹 SmartScreen |
| Tauri updater 企业密钥对 | `npm run tauri signer generate` 生成，私钥入 Secrets | 定制团队 | 自动更新验签用，与 Apple 签名无关 |
| 企业域名 | 企业站（如 `ai.<corp>.com`）+ 更新托管（如 `apps.<corp>.com`） | IT | 内网或公网按合规要求定 |
| 内网构建镜像 | aisuite 等依赖钉 commit；内网 CI 需镜像仓库或私有 PyPI 缓存 | IT/定制团队 | 内网构建才需要，公网 CI 可跳过 |

## 2. 部署步骤（按顺序执行）

### 2.1 私有仓与同步流水线（一次做对）

来源：DEPLOYMENT.md §1、§2。详见 playbook 第 2 章，这里只记"发布前必须已就位"的结论。

一键版（推荐）：

```bash
bash docs/enterprise/templates/init-enterprise-repo.sh \
  --corp acme --name "艾克米科技" \
  --repo https://github.com/acme/openworker-enterprise.git \
  --dry-run          # 先看一遍要做什么，确认后去掉 --dry-run
```

手工版四步：镜像克隆汉化版（`git clone --bare`，保留完整历史）→
在 GitHub 建空私有仓（不要初始化 README）→ `git push --mirror` →
正常克隆私有仓开始工作。

⚠️ 两条铁律：不要用 GitHub 网页 Import（历史可能被改写），更不要下载 zip
重新 `git init`——共同祖先一丢，以后每次同步都是全文件冲突。
分支模型：`main`（企业稳定线）← feature 分支；`sync/localized-main` 同步专用，
流水线自动管理。

同步流水线部署：`sync-localized.yml` 放入私有仓 `.github/workflows/` →
仓库 Settings 允许 Actions 创建 PR → 手动触发一次 `workflow_dispatch` 验证
（刚镜像完应显示 already-synced）。

### 2.2 构建、签名与发布流水线

来源：DEPLOYMENT.md §6；`templates/release-corp.yml`（1035 行，注释即文档）。

**第 1 步：配 Secrets / Variables**（企业仓 Settings → Secrets and variables → Actions）

- Variables：`CORP_NAME`（产物名前缀，如 AcmeWorker）、`CORP_ID`（小写短名，
  如 acme；决定清单文件名 `latest-acme.json`，必须与 `tauri.conf.json` 的
  `plugins.updater.endpoints` 一致）、`CORP_UPDATE_BASE_URL`（可选，见第 3 步）。
- Secrets（macOS 签名公证）：`APPLE_CERTIFICATE(_PASSWORD)`、
  `APPLE_SIGNING_IDENTITY`、`APPLE_API_KEY(_CONTENT)`、`APPLE_API_ISSUER`；
  自动更新签名：`TAURI_SIGNING_PRIVATE_KEY(_PASSWORD)`；
  Windows（可选）：`WINDOWS_CERTIFICATE(_PASSWORD)`。
- 签名 Secrets 一个都不配也能跑：流水线自动走"未签名测试包"分支发 prerelease，
  方便先内测、后办证。

**第 2 步：打 tag 发布**

```bash
# 先确认 tauri.conf.json 的 version（如 0.1.7），再打同号 tag，两者必须一致
git tag corp-v0.1.7 && git push origin corp-v0.1.7
```

注意 tag 前缀是 `corp-v*`（不是 `v*`）：企业仓从汉化仓同步时会带进上游的
`v*` tag，独立前缀才不会误触发企业发布。`release-corp.yml` 矩阵构建
macOS arm64 / macOS x64 / Windows 三产物并签名公证。

**第 3 步：选更新包托管方式（二选一）**

- 方式 A · 私有 Release（默认，`CORP_UPDATE_BASE_URL` 留空）：
  产物挂到私有仓 Release，`latest-<corp>.json` 指向 Release 直链。
  ⚠️ 私有仓 Release 资产要带凭据才能下载，得在 `tauri.conf.json` 的 updater 里
  加 Authorization header——等于把只读 token 发到客户端，仅适合"企业仓设为
  internal、装机范围可控"的场景。
- 方式 B · 内网静态服务器 / 对象存储（推荐）：
  设 `vars.CORP_UPDATE_BASE_URL`（如 `https://dl.corp.example.com/openworker`），
  产物走 `CORP_UPDATE_UPLOAD_URL`（HTTP PUT）或 R2 桶上传。
  好处：不依赖 GitHub 可达性，也不用把 token 发到客户端。

**第 4 步：更新企业站下载页**
下载页的三平台链接与 SHA-256 换成新版（见 §2.3 的 `downloads.json`）。

**第 5 步：分发**
企业站自助下载 + IT 用 MDM 批量安装（macOS 可由 DMG 内 .app 二次封装成 PKG，
Windows 用 MSI 静默参数）。

### 2.3 企业下载站搭建与发布（aiworker.download 流程展开）

来源：DEPLOYMENT.md §3。T1 大纲里"参考现有 aiworker.download 流程"指的就是
下面这套——企业下载站（如 aiworker.download）是按"形态 A"搭起来的：
Cloudflare Workers 静态站 + R2 对象存储托管安装包 + `downloads.json` 清单。
下面是具体步骤，不再是"参考"二字。

**形态 A：公网企业站（`enterprise/site` + Cloudflare Workers）——已交付**

`init-enterprise-repo.sh` 已装好：`enterprise/site/`（下载页 + 企业介绍，
纯静态 assets-only Worker）+ `.github/workflows/deploy-corp-site.yml`
（push main 自动部署）。

**A1. Cloudflare API Token → GitHub Secret**（顺序不能错）

1. Cloudflare → 头像 → My Profile → API Tokens → Create Token，用模板
   「Edit Cloudflare Workers」。
2. 只改两处：Account Resources 选目标账号；Zone Resources 选企业域名
   （域名还没进 Cloudflare 就先选 All zones，做完 A2 再回来收紧）。
3. Create Token 后立刻复制（页面关掉就再也看不到）。
4. 企业仓 Settings → Secrets → Actions，新建：
   `CLOUDFLARE_API_TOKEN`（刚才那串）、`CLOUDFLARE_ACCOUNT_ID`
   （Workers & Pages 页面右栏，仅 token 能访问多个账号时需要）。

⚠️ Secret 名字必须逐字一致、区分大小写。写错不会报错：工作流只打一条
"未配置，跳过部署"的 notice 然后绿灯通过——看起来一切正常，实际什么都没发。
配好后手动跑一次 `Deploy 企业站`，Worker `openworker-<corp-id>-site` 才真正存在。

**A2. 绑定企业域名**（控制台手工操作，不在代码里）

前置：域名已是该 Cloudflare 账号下状态 Active 的站点（没有就 Add a site，
改 NS，等 Active）。然后 Workers & Pages → 点开
`openworker-<corp-id>-site` → Settings → Domains & Routes → Add Custom Domain。
Cloudflare 自动建 DNS 记录并签发证书，一两分钟后可访问。
记住：`deploy 成功 ≠ 域名可访问`。

**A3. 安装包托管（R2）**

安装包不能放进 `enterprise/site/public/`：Workers 静态资源单文件上限 25 MiB，
而 DMG 通常 60–80 MB，会直接部署失败；私有仓 Release 直链也不行（匿名访问 404）。

1. Cloudflare → R2 Object Storage → Create bucket（如 `<corp>-openworker-releases`）。
2. 进桶 → Settings → Custom Domains → Connect Domain（如 `dl.<企业域名>`）。
   别用自带的 `*.r2.dev`——有速率限制，只适合调试。
3. Upload 三个安装包（macOS arm64 `.dmg`、macOS x64 `.dmg`、Windows `.msi`）。
4. 填 `enterprise/site/public/downloads.json`：

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

三个 key 是固定的（与页面 `PLATFORMS` 一一对应，`tests/test_corp_site.py`
钉着）；`url` 留空页面显示"即将开放"，不是坏链接。改完推送即自动重新部署。
顺带：把 `tauri.conf.json` 的 `plugins.updater.endpoints` 指向同桶的
`latest-<corp-id>.json`，自动更新就通了。

**A4. 两条不能破的红线**（`deploy-corp-site.yml` 里各有守卫）

1. 不能覆盖汉化站。汉化站 oaosf.cn 的 Worker 叫 `openworker-cn-site`，
   企业仓是从汉化仓镜像来的，`website/wrangler.jsonc` 里那个名字一直在树里——
   同账号下同名部署会直接把线上站顶掉，wrangler 不会问你一句。
   部署前查两处：解析出的 Worker 名、`enterprise/site/wrangler.jsonc` 的 name 字段。
2. 不能把内部信息发到公网。部署前扫 `public/`，内网域名、私网 IP、疑似凭据
   一律拒绝部署——发出去就已经被抓取了，撤回也晚了。

**A5.（可选）沿用汉化站那套 Next.js 站**
想要源码分析等完整页面时才走。三个已知缺口：会公开仓库提交记录；
`env.IMAGES` 绑定缺失导致 `/_vinext/image` 运行时报错；
`tests/rendered-html.test.mjs` 的硬编码断言要同步改。
走这条务必先把 `wrangler.jsonc` 的 `name` 改掉，否则就是 A4 第 1 条的后果。

**形态 B：内网静态 / Node 部署**（数据合规要求高时）

`website/` 本质是 Next 应用：`npm run build` 后用内网 Node 托管；
或下载页做成纯静态页放内网 Nginx。更新托管（`latest-corp.json` + 安装包）
用同一台内网静态服务器：

```
/var/www/openworker/
├── latest-corp.json
├── OpenWorker-<corp>-macos-arm64.dmg / .app.tar.gz / .sig
├── OpenWorker-<corp>-macos-x64.dmg  / .app.tar.gz / .sig
└── OpenWorker-<corp>-windows-setup.exe / .msi
```

### 2.4 分发与留档

1. **分发渠道**：企业站下载页自助下载（§2.3）+ IT 用 MDM 批量安装。
   两条渠道覆盖"员工自己装"和"IT 统一下发"。
2. **下载站版本页校验**：页面可访问、三平台链接有效、版本号与本次 tag 一致、
   SHA-256 与构建产物一致。
3. **历史版本留档**：R2 桶（形态 A）或内网静态服务器（形态 B）保留历史版本
   产物，不要删旧文件——回滚时要用的（见 §2.5）。`latest-<corp>.json`
   永远指向当前版本，历史版本页可查。
4. **发布日志更新**：`docs/updates/CHANGELOG.md` + `docs/updates/WEEKLY.md`
   按现有习惯追加本次版本记录。

### 2.5 回滚方案

来源：DEPLOYMENT.md §7。回滚不重新构建——"企业托管保留上一版产物与清单，
`latest-<corp>.json` 回指旧版即完成回滚"。

1. 确认上一稳定版的产物还在托管上（R2 桶 / 内网服务器 / 私有 Release），
   记下它的 tag（如 `corp-v0.1.6`）。
2. 把 `latest-<corp>.json` 的各平台 `url` 改回指上一版产物 URL。
3. 把 `downloads.json` 的 `version` 改回上一版号并推送（下载页自动重新部署）。
4. 验证：下载页链接可下、客户端自动更新不再提示新版（或正确提示回退版）。
5. 在 `docs/updates/CHANGELOG.md` 记一笔回滚原因与时间，通知 IT / 受影响员工。

⚠️ 回滚的前提是"上一版产物还在"——所以 §2.4 第 3 条"不要删旧文件"是硬要求。

## 3. 检查清单（本章完成标准）

沿用 T1 大纲第 3 章的 5 项，补充 2 项（§2.2–§2.3 落下来的）：

- [ ] 安装包已上传分发渠道（R2 桶 / 内网静态服务器 / 私有 Release，三选一就位）
- [ ] 下载站版本页可访问、链接有效、版本号与 tag 一致、SHA-256 与产物一致
- [ ] 版本留档完成（历史版本产物保留，历史版本页可查）
- [ ] 发布日志已更新（`docs/updates/CHANGELOG.md`、`WEEKLY.md`）
- [ ] 回滚方案就绪（上一版产物在托管上，`latest-<corp>.json` 可回指）
- [ ] （新增）企业站两条红线已过：Worker 名不是 `openworker-cn-site`，
      `public/` 无内部信息残留
- [ ] （新增）`corp-v*` tag 与 `tauri.conf.json` version 一致

## 4. 来源与回指

本章内容来源（`docs/enterprise/`，括号内为原文节号）：

| 本章小节 | 原文 |
|---|---|
| §1 前置准备清单 | `DEPLOYMENT.md` §0（全表照录，与发布相关的项未删减） |
| §2.1 私有仓与同步流水线 | `DEPLOYMENT.md` §1、§2；`templates/init-enterprise-repo.sh`；详见 playbook 第 2 章 |
| §2.2 构建、签名与发布 | `DEPLOYMENT.md` §6；`templates/release-corp.yml`（Secrets/Variables 清单、tag 规范、方式 A/B） |
| §2.3 企业下载站 | `DEPLOYMENT.md` §3（A1–A5 全节，含两条红线）；`templates/deploy-corp-site.yml`（守卫逻辑）；`templates/site/`（`wrangler.jsonc`、`public/downloads.json` 格式） |
| §2.4 分发与留档 | `DEPLOYMENT.md` §6（分发段）、§3 A3（R2 留档）；`docs/updates/` 现有习惯 |
| §2.5 回滚方案 | `DEPLOYMENT.md` §7 |

建议的回指文案（只给文案，不改原文；T2–T4 正文定稿时由维护者在原文对应节顶部加入）：

- `DEPLOYMENT.md` §3 顶部：`> 本节已被 playbook 第 3 章（部署）引用为"企业下载站搭建与发布"的执行步骤，playbook 版见 docs/plans/2026-10-17-playbook-ch3-deploy.md §2.3。`
- `DEPLOYMENT.md` §6 顶部：`> 本节已被 playbook 第 3 章引用为"构建、签名与发布"的执行步骤，playbook 版见 docs/plans/2026-10-17-playbook-ch3-deploy.md §2.2。`
- `DEPLOYMENT.md` §7 顶部：`> 本节已被 playbook 第 3 章引用为"回滚方案"，playbook 版见 docs/plans/2026-10-17-playbook-ch3-deploy.md §2.5。`
- `templates/release-corp.yml` 头部注释追加：`# playbook 第 3 章 §2.2 引用本文件为发布流水线规范。`

未覆盖的原文节（超出 T1 划定的第 3 章范围，此处声明不遗漏）：

- `DEPLOYMENT.md` §4 私有模型接入、§5 企业技能包与知识库部署——属"企业配置下发"
  范畴，playbook 三章未单列。T5 走查时确认：如需覆盖，建议在第 1 章"定制范围"
  小节引用，不在本章展开。

## 5. T5 走查才验证的事项（本稿不承诺）

1. 按 §2.2–§2.3 真实跑一次发布：Secrets 是否齐、tag 触发是否正常、
   R2/内网托管是否可达——任何一步卡住都记入走查报告的卡点清单。
2. 两条红线守卫是否真拦得住：可演练一次"误配 `openworker-cn-site`"看流水线
   是否拒绝（在测试仓演练，别拿生产仓试）。
3. `downloads.json` 三个 key 与页面 `PLATFORMS` 的对应关系跑一遍
   `tests/test_corp_site.py` 验证。
4. 回滚演练：按 §2.5 走一遍回指，确认客户端行为符合预期。
