# 企业定制版 · 换肤与多平台打包指南

- 版本：v1.0 · 2026-08-04
- 适用：基于 `openworker-zh-localized` 的企业定制版（换品牌皮肤 + macOS Apple Silicon / Intel + Windows 打包分发）

---

## 1. 换皮肤：主题体系与改法

### 1.1 主题机制（现状）

前端颜色**单一事实源**在 `surfaces/gui/src/styles.css` 的 CSS 自定义属性：

- 亮色：`:root { --paper; --panel; --ink; --muted; --faint; --line; --accent; --accent-soft; --ok; --warn-*; --danger; --teal-*; --solid; --on-solid; … }`
- 暗色：`html[data-theme="dark"] { … }`（`data-theme` 由 `index.html` 内联脚本在首帧前设置，避免闪白；切换逻辑在 `src/theme.ts`）
- Tailwind（`surfaces/gui/tailwind.config.js`）不含任何硬编码色值，全部 token 映射到上述变量（经 `color-mix` 包装以支持 `/NN` 透明度工具类）

**结论：换主题色 = 只覆盖一个 CSS 变量块，不碰任何组件代码。**

### 1.2 企业皮肤包做法（推荐）

为把同步冲突面压到零，企业皮肤做成**独立覆盖文件**而非直接改 `styles.css`：

1. 新建 `enterprise/branding/theme.css`，只写变量覆盖：

```css
/* 企业主题 —— 只覆盖变量，两套（亮/暗）都要给 */
:root {
  --accent: #c8102e;            /* 企业主色（示例：企业红） */
  --accent-soft: #fdeaea;
  --solid: #c8102e;             /* 主按钮底色 */
  --on-solid: #ffffff;
}
html[data-theme="dark"] {
  --accent: #ff5a6e;
  --accent-soft: #3a1b20;
  --solid: #e2354d;
  --on-solid: #ffffff;
}
```

2. 挂载点：在 `surfaces/gui/src/main.tsx`（或 `index.html`）追加一行 import 该文件——后加载的覆盖先加载的，级联即生效。
3. 字体如需企业字库：在 `tailwind.config.js` 的 `fontFamily.sans` 首位插入企业字体名，字体文件放 `surfaces/gui/src/fonts/`（该目录已存在）。

改动量：新文件 1 个 + 挂载 1 行 + 可选字体 1 行。上游改版式/组件不影响皮肤；上游改默认配色也不覆盖企业色（企业覆盖层级更后）。

### 1.3 品牌名称与图标清单

| 品牌项 | 文件 | 说明 |
|--------|------|------|
| 应用名（窗口/安装包名） | `surfaces/gui/src-tauri/tauri.conf.json` → `productName`（现值 `OpenWorker 中文版`） | 改为如 `XX企业智能助手` |
| Bundle ID | 同文件 → `identifier`（现值 `com.openworker.desktop.zh`） | 改为 `com.<corp>.openworker`。⚠️ 改后 macOS 视为不同 App，状态目录与已装旧版不互通，须在首个企业版就定妥 |
| 发行方 | 同文件 → `bundle.publisher` | 企业名 |
| 应用图标 | `surfaces/gui/src-tauri/icons/`（icon.icns、icon.ico、icon.png、32/64/128 png、Square*Logo.png、StoreLogo.png、tray.png） | 用 `npx tauri icon <企业logo.png>`（输入 ≥1024×1024 透明底 PNG）一次性生成全套，源图存 `enterprise/branding/` |
| 托盘图标 | 同目录 `tray.png` / `tray.rgba` | macOS 建议模板图（单色）风格 |
| macOS 权限文案等 | `surfaces/gui/src-tauri/Info.plist` | 各 NSUsageDescription 已中文化，替换其中产品名 |
| 托盘菜单/更新提示文案 | `surfaces/gui/src-tauri/src/lib.rs` | 已中文化，替换其中「OpenWorker」字样 |
| DMG 背景图 | `packaging/dmg-background.png` / `@2x.png` / `.tiff` | 企业视觉版拖装背景 |
| 前端页面标题 | `surfaces/gui/index.html`（`<title>` 现仍为 `OpenWorker`，`lang="en"` 建议一并改 `zh-CN`） | 浏览器/窗口标题 |
| 前端词标与启动屏 | `surfaces/gui/src/components/Sidebar.tsx`（侧栏 `OpenWorker` + BETA 徽章）、`src/App.tsx` 启动屏词标、`Onboarding.tsx` 欢迎语 | 界面内品牌名 |
| 前端 Logo 图形 | `surfaces/gui/src/components/Icon.tsx` 中 `logo` 分支的 SVG path | 界面内 Logo |
| 网站品牌 | `website/`（企业站副本中替换，见 DEPLOYMENT） | 域名、名称、Logo、下载链接 |

> 已知汉化盲区：`surfaces/gui/src/humanize.ts`（工具步骤一行文案与审批标题）大部分仍是英文模板——企业验收会暴露中英混排，建议在品牌化的同一批改动中补译。

> 文案层面：界面中文文案是直接写在组件里的（无 i18n 资源层）。企业只需替换品牌词（全局搜「OpenWorker」），不建议大面积改功能文案——那会放大与汉化版的同步冲突。
>
> 另需产品决策一项：侧栏含「OpenWorker Cloud」登录入口（`Sidebar.tsx`，对应 `config.toml` 的 `cloud_*` 键）——企业版通常应隐藏该入口并置空 `cloud_relay_ws_url`，或替换为企业自建云中转。

---

## 2. 多平台打包

### 2.1 构建产物矩阵（现有流水线已支持）

`.github/workflows/release.yml` 用矩阵在三种 runner 上构建，产物命名稳定：

| 平台 | 目标 | 产物 | 构建脚本 |
|------|------|------|---------|
| macOS Apple Silicon | aarch64-apple-darwin | `OpenWorker-CN-macos-arm64.dmg` + `.app.tar.gz`(+`.sig`) | `packaging/build_dmg.sh`（macos-14/15 arm64 runner） |
| macOS Intel | x86_64-apple-darwin | `OpenWorker-CN-macos-x64.dmg` + `.app.tar.gz`(+`.sig`) | 同上（macos-13 x86_64 runner，Actions 提供至 2027-08） |
| Windows 10/11 x64 | x86_64-pc-windows-msvc | NSIS `…-setup.exe`（currentUser 装机）+ `.msi` | `packaging/build_windows.ps1` |

> 注意：仓库里 Windows 构建有**两条并存路径**——`release.yml` 矩阵中的 windows-latest 项（tag `v*` 触发，随 mac 一起出正式包）与独立的 `build-windows.yml`（手动/`win-*` tag 触发的轻量版，无签名）。企业流水线应以 `release.yml` 为准，`build-windows.yml` 仅留作调试（其头部注释还有旧仓库名残留，企业副本可清理）。

> 关于 macOS Universal（单包双芯片）：现方案为**双包分发**（网站按芯片给下载链接、更新清单按 target 分发），因为 PyInstaller 打包的 Python sidecar 难以做成 universal 二进制。维持双包是当前最稳做法。

### 2.2 打包链路（两平台同构）

```
Python 后端 (coworker)
   └─ PyInstaller (packaging/openworker-server.spec, 入口 packaging/server_entry.py)
        → onedir 独立运行目录 → staged 到 surfaces/gui/src-tauri/binaries/sidecar/
React 前端 (surfaces/gui) ─ vite build ─┐
Tauri 壳 (src-tauri, Rust) ────────────┴─ tauri build → .app/.dmg（mac）或 .msi/.exe（win）
                                             （sidecar 作为 resources 打入包内）
```

企业注意两点：

- **企业 Python 包进 sidecar**：若企业连接器/工具作为独立 Python 包实现，需在 `openworker-server.spec` 的 `collect_submodules` 列表追加包名（懒加载依赖仿 spec 中 websockets/pypdf 的 `collect_all` 写法显式收集，带数据文件的走 `datas`）。
- **外接后端调试**：桌面壳按 `COWORKER_SERVER_BIN` 环境变量 → 打包内 sidecar → 开发 `.venv` 的顺序解析后端，设该变量可让壳直接启动企业版服务器二进制，不必每次重打包。

本地构建命令：

```bash
# macOS（在对应芯片的 Mac 上执行，或 CI 矩阵完成）
python3 -m venv .venv && .venv/bin/pip install -e '.[bedrock]' pyinstaller tzdata typer
cd surfaces/gui && npm ci && cd ../..
bash packaging/build_dmg.sh          # 产出 .app + .dmg

# Windows（PowerShell）
powershell -ExecutionPolicy Bypass -File packaging/build_windows.ps1
```

### 2.3 签名与公证（企业必办清单）

| 平台 | 需要什么 | 注入方式 |
|------|---------|---------|
| macOS 签名 | Apple Developer Program（组织账号）→ Developer ID Application 证书 | Secrets：`APPLE_CERTIFICATE`、`APPLE_CERTIFICATE_PASSWORD`、`APPLE_SIGNING_IDENTITY` |
| macOS 公证 | App Store Connect API Key（Notary） | `APPLE_API_KEY`、`APPLE_API_KEY_CONTENT`、`APPLE_API_ISSUER` |
| 更新包签名 | Tauri updater minisign 密钥对（**企业自建，勿沿用汉化版公钥**：`npm run tauri signer generate`） | 私钥进 Secrets：`TAURI_SIGNING_PRIVATE_KEY`(+`_PASSWORD`)；公钥写入 `tauri.conf.json > plugins.updater.pubkey` |
| Windows 代码签名 | OV/EV 代码签名证书（CA 购买；EV 免 SmartScreen 冷启动信誉期） | 证书接入 `build_windows.ps1`/CI（signtool），可后补——未签名包配合企业域内白名单也可分发 |

流程细节（Keychain 导入、公证提交、`latest-zh.json` 生成与回写）已在 `docs/release-signed-updates.md` 完整文档化，release.yml 在 tag 发布时强制校验上述 Secrets 存在。企业版沿用该管线，仅替换 Secrets 与命名。

### 2.4 自动更新改企业源

现状机制：`tauri.conf.json > plugins.updater.endpoints` 指向本仓库 GitHub Release 的 `latest-zh.json`（由 `packaging/make_update_manifest.py` 生成，release.yml 回写 `releases/latest-zh.json` 兜底）。

企业版改造（配置级）：

0. **密钥切换断链提醒**：若企业版承接已安装的汉化版用户，更换 `pubkey` 后旧客户端无法验证新更新包——需要发布一个用户手动安装的"桥接版本"（详见 `docs/release-signed-updates.md`）。企业全新装机不受影响。
1. endpoints 改为企业可达地址，二选一：
   - 私有 GitHub Release 直链（客户端可匿名访问不了私有仓——需在企业站放反代或用内网静态服务器托管 `latest-corp.json` 与更新包）；
   - **推荐**：企业内网/企业站静态托管 `https://apps.<corp>.com/openworker/latest-corp.json` + 更新包文件
2. `make_update_manifest.py` 输出清单中的下载 URL 改为企业托管地址
3. pubkey 换企业密钥（见 2.3）；版本号采用 `0.x.y-corp.n`
4. 发布流水线（`release-corp.yml`，企业仓独立文件）在 tag 时构建 → 签名/公证 → 上传企业托管 → 刷新清单

验收：安装 `0.1.7-corp.1` → 发布 `0.1.7-corp.2` → 客户端收到更新提示并完成升级，签名校验通过。

---

## 3. 企业打包自查清单（发布前逐项过）

- [ ] `productName` / `identifier` / `publisher` / 图标全套 / 托盘图标 / DMG 背景已品牌化
- [ ] `theme.css` 亮/暗两套变量齐全，暗色模式下对比度可读
- [ ] updater endpoints + pubkey 为企业值（grep 确认无 `zhanglunet` / 汉化版公钥残留）
- [ ] 默认 `config.toml` 指向企业模型端点，无公网模型默认项
- [ ] 三平台产物均能安装、启动、完成一次对话与一次表格分析
- [ ] macOS 双芯片包分别在 arm64 与 Intel 真机（或 Rosetta 关闭的 VM）验证
- [ ] Windows 包在干净 Win10/Win11 上验证 WebView2 引导安装
- [ ] 自动更新全链路演练（旧版 → 新版）通过
- [ ] LICENSE/NOTICE 保留上游 MIT 声明
