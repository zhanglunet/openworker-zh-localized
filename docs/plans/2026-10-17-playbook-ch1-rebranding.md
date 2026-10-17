# Playbook 第 1 章：换肤打包（T2 正文）

> PRD-030/T2（trend #182）。本章按 T1 大纲（`docs/plans/2026-10-17-enterprise-playbook-outline.md`，
> PR #6 已合并）第 1 章展开：把"换肤打包"写成按顺序可执行的步骤。
> 目标读者：第一次做企业换肤打包的执行人。本章的"检查清单"全勾才能进第 2 章。

## 0. 输入 / 输出

**输入**（开工前必须备齐）：

| # | 输入项 | 说明 |
|---|---|---|
| 1 | 汉化版基线版本 | `openworker-zh-localized` 的某个 **tag**（不是随手 commit）；版本号以 `surfaces/gui/src-tauri/tauri.conf.json` 的 `version` 为唯一真源 |
| 2 | 企业品牌素材包 | 应用名（中英文）、Logo 源图（≥1024×1024 透明底 PNG）、免责声明文案、下载站域名、企业主色（亮/暗两套色值）、可选企业字体 |

**输出**：

| # | 输出项 | 说明 |
|---|---|---|
| 1 | 企业版安装包 | macOS DMG（arm64 + Intel 双包）/ Windows 安装器（NSIS `.exe` + `.msi`） |
| 2 | 换肤记录单 | 见 §5 模板；随安装包一起归档，是第 2 章的输入 |

## 1. 开工前：两项产品决策 + 素材确认

这两项必须在动手前定，定晚了返工（依据 `BRANDING_PACKAGING.md` §1.3）：

1. **Bundle ID 定死**：`tauri.conf.json → identifier`（如 `com.<corp>.openworker`）。
   macOS 会把不同 Bundle ID 视为不同 App，状态目录与已装旧版不互通——**首个企业版就必须定妥**，之后再改等于让用户重装。
2. **侧栏「OpenWorker Cloud」登录入口去留**：企业版通常应隐藏该入口并置空 `cloud_relay_ws_url`
   （`Sidebar.tsx`，对应 `config.toml` 的 `cloud_*` 键），或替换为企业自建云中转。

素材确认：Logo 源图尺寸/透明底、免责声明文案终稿（见 §2.5）、企业色两套色值齐全。

## 2. 品牌替换五件套（按顺序做）

依据 `docs/enterprise/BRANDING_PACKAGING.md` §1.2–§1.3，以及
`zhanglunet/openworker-enterprise` README 的既有实践（T1 评审要求把引用展开，不再只写"参考"）。

### 2.1 主题皮肤：只覆盖变量，不碰组件

前端颜色的单一事实源是 `surfaces/gui/src/styles.css` 的 CSS 自定义属性
（亮色 `:root` / 暗色 `html[data-theme="dark"]`，Tailwind 不含硬编码色值）。
企业皮肤做成**独立覆盖文件**，把同步冲突面压到零：

1. 新建 `enterprise/branding/theme.css`，只写变量覆盖，亮/暗两套都要给：

```css
:root {
  --accent: #c8102e;            /* 企业主色（示例：企业红） */
  --accent-soft: #fdeaea;
  --solid: #c8102e;
  --on-solid: #ffffff;
}
html[data-theme="dark"] {
  --accent: #ff5a6e;
  --accent-soft: #3a1b20;
  --solid: #e2354d;
  --on-solid: #ffffff;
}
```

2. 在 `surfaces/gui/src/main.tsx`（或 `index.html`）追加一行 import 该文件——后加载的覆盖先加载的，级联即生效。
3. 企业字体：在 `tailwind.config.js` 的 `fontFamily.sans` 首位插入企业字体名，字体文件放
   `surfaces/gui/src/fonts/`（该目录已存在）。

改动量：1 个新文件 + 1 行挂载 + 可选 1 行字体。上游改版式/组件不影响皮肤。

### 2.2 应用名 / Bundle ID / 发行方

文件：`surfaces/gui/src-tauri/tauri.conf.json`。

| 字段 | 改法 | 说明 |
|---|---|---|
| `productName` | 如 `XX企业智能助手` | 窗口标题/安装包名（原值 `OpenWorker 中文版`）|
| `identifier` | `com.<corp>.openworker` | §1 已定，勿再改（原值 `com.openworker.desktop.zh`）|
| `bundle.publisher` | 企业名 | Windows 安装包的发布者显示名 |
| `bundle.windows.wix.language` | `["zh-CN"]` | 中文产品名必加：WiX 默认 en-US 代码页表达不了中文，`light.exe` 会失败导致整个 Windows 构建挂掉（本仓库已修复，企业版沿用即可）|

另有三个同文件的品牌挂载点，打包流水线会校验（见 §3.2）：
`plugins.updater.endpoints`（必须含 `latest-<corp_id>.json` 且不指向上游/汉化仓）、
`plugins.updater.pubkey`（企业自建密钥，见 §3.4）。

### 2.3 图标全套

1. 用 `npx tauri icon <企业logo.png>` 一次性生成 `surfaces/gui/src-tauri/icons/` 全套
   （`icon.icns`、`icon.ico`、`icon.png`、32/64/128 png、`Square*Logo.png`、`StoreLogo.png`、`tray.png`）；
   源图存 `enterprise/branding/` 备查。
2. 托盘图标：macOS 建议模板图（单色）风格。
3. 打包流水线约定：企业自己的图标覆盖脚本放 `enterprise/branding/apply_branding.sh`，
   构建时自动覆盖到 `surfaces/gui/src-tauri/icons/` 这个"挂载点"（脚本不存在则沿用仓库内图标）。

### 2.4 界面文案与品牌词

1. `Info.plist`：各 `NSUsageDescription` 替换产品名（已中文化，只换名）。
2. `surfaces/gui/src-tauri/src/lib.rs`：替换其中「OpenWorker」字样（托盘菜单/更新提示文案）。
3. `surfaces/gui/index.html`：`<title>`（现仍为 `OpenWorker`），`lang="en"` 一并改 `zh-CN`。
4. `Sidebar.tsx`（侧栏品牌名 + BETA 徽章）、`App.tsx` 启动屏词标、`Onboarding.tsx` 欢迎语。
5. `Icon.tsx` 中 `logo` 分支的 SVG path：换企业 Logo 图形。
6. DMG 背景图：`packaging/dmg-background.png`（`@2x.png` / `.tiff`）换企业视觉版。
7. 全局搜「OpenWorker」替换品牌词。**不建议大面积改功能文案**：界面中文是直接写在组件里的
   （无 i18n 资源层），改多了会放大与汉化版的同步冲突。
8. 已知汉化盲区（`BRANDING_PACKAGING.md` §1.3）：`surfaces/gui/src/humanize.ts`
   （工具步骤一行文案与审批标题）大部分仍是英文模板——在品牌化的同一批改动中补译，
   否则企业验收会暴露中英混排。

### 2.5 免责声明（openworker-enterprise 既有实践，原文照录）

openworker-enterprise README 顶部的标准文案，企业版直接沿用（换企业名）：

> 本项目为个人作品，**非官方发布**，与任何官方机构无隶属、代理或背书关系，
> 不代表其产品或立场。使用风险自负。商标与名称的权利归各自所有者。

应用内声明：`enterprise/config/branding.json` 写 `disclaimer` 字段，打包流水线
（`release-corp.yml`）构建时注入为 `VITE_CORP_DISCLAIMER` 环境变量；
缺失时构建只告警、应用内回落默认文案——所以文案要在开工前定稿，不要留到构建时。

网站品牌（`website/` 企业站副本的域名/名称/Logo/下载链接替换）归第 3 章部署，
本章只确认素材齐全。

## 3. 打包步骤（按顺序可执行）

依据 `BRANDING_PACKAGING.md` §2 + `docs/enterprise/templates/release-corp.yml`
（企业版流水线文件，企业仓独立持有，复制 `release.yml` 改名/密钥/托管地址而来）。

### 3.1 打 tag

- 格式：`corp-vX.Y.Z` 或 `corp-vX.Y.Z-<corp>.n`（流水线用白名单正则校验，`v0.1.7` 这种漏了
  `corp-` 前缀的会被拦下）。
- **tag 必须与 `tauri.conf.json` 的 `version` 一致**（去掉 `corp-v` 前缀、再去掉第一个 `-`
  之后的企业内部序号后比对），不一致构建直接失败——打 tag 前先改配置。
- 企业短名（`CORP_NAME`/`CORP_ID`）只允许 ASCII（`^[A-Za-z0-9][A-Za-z0-9._-]*$`），
  可直接用作 `enterprise/skills/<name>` 前缀。

> 口径说明：openworker-enterprise README 记载过 `0.2.3+1`（tag 目录写作 `0.2.3.1`）的写法，
> 那是早期实践；以 `release-corp.yml` 白名单（`corp-vX.Y.Z`）为准，流水线只认后者。

### 3.2 preflight 自动校验（流水线第一步，改漏了会在这里被拦）

1. 品牌五挂载点（`tauri.conf.json`）：`productName` / `identifier` / `bundle.publisher` /
   `plugins.updater.endpoints` / `plugins.updater.pubkey`——出现汉化版默认值
   （如 `OpenWorker 中文版`、`com.openworker.desktop.zh`）即视为品牌没换。
   **正式签名版改漏直接 fail**（发出去就是带着上游品牌的包，收不回来）；
   未签名测试版只告警，方便换肤没做完时先出内测包。
2. `updater.endpoints` 必须有一条指向 `latest-<corp_id>.json`；若还指着
   `zhanglunet` / `andrewyng` 的地址，说明企业包会去拉别人的更新，直接 fail。

### 3.3 构建矩阵（三平台一次出齐）

| 平台 | Runner | 产物 |
|---|---|---|
| macOS Apple Silicon | `macos-latest` | `.dmg` + `.app.tar.gz`（+`.sig`）|
| macOS Intel | `macos-15-intel`（以 GitHub 公告的可用性为准）| `.dmg` + `.app.tar.gz`（+`.sig`）|
| Windows 10/11 x64 | `windows-latest` | NSIS `…-setup.exe`（currentUser 装机）+ `.msi` |

> 双包分发说明：macOS 维持"双包"（arm64/x64 各一包，网站按芯片给下载链接），
> 因为 PyInstaller 打包的 Python sidecar 难以做成 universal 二进制——这是当前最稳做法，不要合包。

构建链路（两平台同构）：

```
Python 后端 → PyInstaller（packaging/openworker-server.spec，入口 packaging/server_entry.py）
    → onedir 独立运行目录 → staged 到 surfaces/gui/src-tauri/binaries/sidecar/
React 前端（vite build） + Tauri 壳（Rust） → tauri build → .app/.dmg 或 .msi/.exe
```

- 企业 Python 包进 sidecar：在 `openworker-server.spec` 的 `collect_submodules` 列表追加包名
  （带数据文件的走 `datas`，仿 spec 中 websockets/pypdf 的 `collect_all` 写法）。
- 调试免重打包：设 `COWORKER_SERVER_BIN` 环境变量，让桌面壳直接启动企业版服务器二进制
  （按"环境变量 → 打包内 sidecar → 开发 .venv"顺序解析）。

本地构建命令（CI 挂掉时的兜底）：

```bash
# macOS（在对应芯片的 Mac 上执行）
python3 -m venv .venv && .venv/bin/pip install -e '.[bedrock]' pyinstaller tzdata typer
cd surfaces/gui && npm ci && cd ../..
bash packaging/build_dmg.sh          # 产出 .app + .dmg

# Windows（PowerShell）
powershell -ExecutionPolicy Bypass -File packaging/build_windows.ps1
```

openworker-enterprise 既有实践：本机脚本 `CORP_NAME=AsiaInfoWorker bash packaging/local_prerelease_macos.sh`
（tag 按版本号自动生成，如 `corp-local-v0.2.3.1-macos-arm64`）；Windows 包走过 GitLab.com
Windows hosted runner（`.gitlab-ci.yml`，见 `docs/windows-gitlab-ci.md`）。

### 3.4 签名与公证（企业必办清单）

| 平台 | 需要什么 | 注入方式 |
|---|---|---|
| macOS 签名 | Apple Developer Program（组织账号）→ Developer ID Application 证书 | Secrets：`APPLE_CERTIFICATE`、`APPLE_CERTIFICATE_PASSWORD`、`APPLE_SIGNING_IDENTITY` |
| macOS 公证 | App Store Connect API Key（Notary） | `APPLE_API_KEY`、`APPLE_API_KEY_CONTENT`、`APPLE_API_ISSUER` |
| 更新包签名 | Tauri updater minisign 密钥对（**企业自建，勿沿用汉化版公钥**：`npm run tauri signer generate`） | 私钥进 Secrets（`TAURI_SIGNING_PRIVATE_KEY` + `_PASSWORD`）；公钥写入 `tauri.conf.json → plugins.updater.pubkey` |
| Windows 代码签名 | OV/EV 代码签名证书（CA 购买；EV 免 SmartScreen 冷启动信誉期） | 证书接入 `build_windows.ps1`/CI（signtool）；可后补——未签名包配合企业域内白名单也可分发 |

流程细节（Keychain 导入、公证提交、`latest-zh.json` 生成与回写）见
`docs/release-signed-updates.md`；`release.yml` 在 tag 发布时强制校验上述 Secrets 存在。
企业版沿用该管线，仅替换 Secrets 与命名。

### 3.5 自动更新改企业源

1. `tauri.conf.json → plugins.updater.endpoints` 改为企业可达地址，二选一：
   - 私有 GitHub Release 直链（客户端匿名访问不了私有仓——需在企业站放反代或内网静态服务器托管）；
   - **推荐**：企业内网/企业站静态托管 `https://apps.<corp>.com/openworker/latest-corp.json` + 更新包文件。
2. `packaging/make_update_manifest.py` 输出清单中的下载 URL 改为企业托管地址。
3. `pubkey` 换企业密钥（见 §3.4）；版本号采用 `0.x.y-corp.n`。
4. **断链提醒**：若企业版承接已安装的汉化版用户，更换 `pubkey` 后旧客户端无法验证新更新包——
   需要先发布一个用户手动安装的"桥接版本"（详见 `docs/release-signed-updates.md`）；企业全新装机不受影响。

验收标准：安装 `0.1.7-corp.1` → 发布 `0.1.7-corp.2` → 客户端收到更新提示并完成升级，签名校验通过。
（此项留到 T5 走查时真实演练。）

## 4. 验证清单（展开）

依据 `BRANDING_PACKAGING.md` §3 自查清单 + T1 大纲第 1 章检查清单展开。
"检查清单"全勾才能进第 2 章。

- [ ] **装得上**：三平台产物在干净机器上安装成功。macOS 双芯片包分别在 arm64 与 Intel
      真机（或关闭 Rosetta 的 VM）验证；Windows 包在干净 Win10/Win11 上验证 WebView2 引导安装。
- [ ] **打得开**：启动无报错，完成一次对话与一次表格分析。
- [ ] **品牌对**：`productName` / `identifier` / `publisher` / 图标全套 / 托盘图标 /
      DMG 背景已品牌化；`theme.css` 亮/暗两套变量齐全，暗色模式下对比度可读；
      全量 UI 走查一遍，无英文残留、无占位符（`humanize.ts` 补译已包含）。
- [ ] **更新源对**：grep 确认 updater `endpoints` + `pubkey` 为企业值，
      无 `zhanglunet` / 汉化版公钥残留；默认 `config.toml` 指向企业模型端点，无公网模型默认项。
- [ ] **功能一致**：与基线汉化版同版本功能一致（换肤只换品牌，不动功能）。
- [ ] **自动更新全链路演练通过**（旧版 → 新版，签名校验通过）——T5 走查时做。
- [ ] **LICENSE/NOTICE 保留上游 MIT 声明**。

openworker-enterprise 既有实践（本地验证命令备查）：

```bash
.venv/bin/python -m pytest enterprise/tests -q
git diff --check
```

## 5. 换肤记录单（模板）

第 1 章的输出物之一，第 2 章的输入。每次换肤打包填写一份，随安装包归档。

| 项 | 填写 |
|---|---|
| 汉化版基线 tag | （如 `v0.1.7`，必须是 tag，不能是随手 commit） |
| 企业名 / 应用名 | |
| Bundle ID | （首个企业版定妥后不再改） |
| 企业主色（亮/暗） | |
| 免责声明文案版本 | |
| 打包人 | |
| 打包日期 | |
| 产物清单 | macOS arm64 dmg / macOS Intel dmg / Windows exe+msi（勾选实际产出） |
| 已知事项 | （如 humanize.ts 补译范围、Cloud 入口处理方式） |

## 6. 来源与回指

**本章引用的原文节**（T1 大纲"对应关系"表的落点）：

- `docs/enterprise/BRANDING_PACKAGING.md`
  - §1.1 主题机制 → §2.1
  - §1.2 企业皮肤包做法 → §2.1
  - §1.3 品牌名称与图标清单 / 已知汉化盲区 / 文案层面 / 产品决策 → §1、§2.2–§2.4
  - §2.1 构建产物矩阵 / Windows MSI 陷阱 / 双包分发 → §3.3
  - §2.2 打包链路 / 企业 Python 包进 sidecar / COWORKER_SERVER_BIN / 本地构建命令 → §3.3
  - §2.3 签名与公证 → §3.4
  - §2.4 自动更新改企业源 / 桥接版本 → §3.5
  - §3 企业打包自查清单 → §4
- `docs/enterprise/templates/release-corp.yml`
  - tag 白名单 / CORP_NAME ASCII 规则 / 版本号唯一真源 → §3.1
  - preflight 品牌五挂载点校验 → §3.2
  - 构建矩阵 / 免责声明注入（`enterprise/config/branding.json` → `VITE_CORP_DISCLAIMER`）/
    `apply_branding.sh` 挂载点 → §2.3、§2.5、§3.3
- `zhanglunet/openworker-enterprise` README（T1 评审要求展开的"既有实践"）
  - 免责声明标准文案 → §2.5（原文照录）
  - 版本号规则（`0.2.3+1` 早期实践，口径以 §3.1 为准）→ §3.1 口径说明
  - 下载站实践（`aiworker.download`，旧域名 301 跳转）→ 第 3 章部署时引用
  - 本地验证命令（`pytest enterprise/tests`、`git diff --check`）→ §4

**建议的回指文案**（T5 时写回原文，本章只给文案，不改原文）：

- `BRANDING_PACKAGING.md` 顶部建议加：
  > 本节已被 playbook 第 1 章《换肤打包》（`docs/plans/2026-10-17-playbook-ch1-rebranding.md`）引用为执行步骤；改动本节前请先看 playbook 第 1 章 §6 的来源表。
- `templates/release-corp.yml` 头部注释建议加：
  > 企业打包流水线：执行步骤见 playbook 第 1 章 §3；品牌挂载点清单见 §2。

## 7. 留给 T5 走查验证的事项

- 自动更新全链路真实演练（§3.5 验收标准：`0.1.7-corp.1` → `0.1.7-corp.2`）。
- macOS 双芯片真机 / Windows 干净机实装验证。
- `humanize.ts` 补译抽查（中英混排是否清零）。
- 记录本次换肤各步骤实际耗时与卡点，输出"playbook 修订清单"（至少修订一处，
  否则视为走查不充分——T1 大纲附则要求）。
