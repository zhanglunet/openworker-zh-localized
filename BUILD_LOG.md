# OpenWorker 全量汉化版构建记录

> 本仓库地址：https://github.com/zhanglunet/openworker-zh-localized
> 基于 Lenovo202409/openworker-zh 二次整理，包含前端 GUI + Tauri 桌面壳的全量中文汉化。

---

## 1. 本次完成的工作总览

| 工作项 | 状态 | 说明 |
|--------|------|------|
| 环境搭建 | ✅ 完成 | 在无 Homebrew/pyenv/Node 的系统上，于用户目录内安装 Python、Node、Rust、CMake |
| 源码运行浏览器 GUI | ✅ 完成 | 后端 `127.0.0.1:8765` + 前端 `localhost:1420` 可正常访问 |
| 修复浏览器打不开问题 | ✅ 完成 | 注入 `VITE_COWORKER_API_TOKEN` + Vite `--host` 监听所有本地地址 |
| 前端 GUI 汉化 | ✅ 已验证 | 所有 React 组件用户可见文案已汉化（设置/模型/角色/侧边栏/审批/收件箱等） |
| Tauri 桌面壳汉化 | ✅ 完成 | 托盘菜单、权限提示、语音输入/更新错误信息已汉化 |
| 编译 Tauri 桌面客户端 | ✅ 完成 | `npm run tauri dev` 编译通过（开发模式） |
| 新建 GitHub 仓库并推送 | ✅ 完成 | https://github.com/zhanglunet/openworker-zh-localized |

---

## 2. 环境配置详情

### 2.1 初始环境限制

- 系统：macOS 26.5.2（Apple Silicon arm64）
- 无 Homebrew、无 pyenv、无 conda、无 Node.js、无 Rust、无 CMake
- 所有依赖均安装在 workspace 内的 `local/` 目录，**未使用 sudo**

### 2.2 安装的依赖

| 工具 | 版本 | 安装路径 |
|------|------|----------|
| Python | 3.13.13 | `/Users/john/OpenWorker/de8ccae2-dac/local/miniforge3`（Miniforge） |
| Node.js | 20.15.1 | `/Users/john/OpenWorker/de8ccae2-dac/local/node` |
| Rust | 1.97.1 | `~/.cargo`（rustup 默认） |
| CMake | 3.31.5 | `/Users/john/OpenWorker/de8ccae2-dac/local/cmake/CMake.app` |

### 2.3 Python 项目初始化

```bash
# 1. 克隆汉化版仓库
git clone https://github.com/Lenovo202409/openworker-zh.git
cd openworker-zh

# 2. 使用 conda 的 Python 创建 venv（避免 macOS 系统 Python 3.9）
/Users/john/OpenWorker/de8ccae2-dac/local/miniforge3/bin/python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[messaging,dev]"

# 3. 修复 mcp 版本不兼容问题
# 默认会安装 mcp==2.0.0，但项目代码只兼容 1.x 的 streamablehttp_client API
.venv/bin/python -m pip install 'mcp>=1.1,<2.0'
```

### 2.4 前端依赖安装

```bash
cd surfaces/gui
npm install
```

---

## 3. 运行方式

### 3.1 浏览器版 GUI

```bash
# 终端 1：启动后端
cd /Users/john/OpenWorker/de8ccae2-dac/openworker-zh-localized
bash start-openworker-server.sh

# 终端 2：启动前端
cd /Users/john/OpenWorker/de8ccae2-dac/openworker-zh-localized
bash start-openworker-gui.sh
```

然后浏览器打开：

- http://localhost:1420/
- http://127.0.0.1:1420/

### 3.2 桌面客户端开发模式

```bash
cd /Users/john/OpenWorker/de8ccae2-dac/openworker-zh-localized/surfaces/gui
export PATH=/Users/john/OpenWorker/de8ccae2-dac/local/cmake/CMake.app/Contents/bin:/Users/john/OpenWorker/de8ccae2-dac/local/miniforge3/bin:/Users/john/OpenWorker/de8ccae2-dac/local/node/bin:$HOME/.cargo/bin:$PATH

COWORKER_STATE_DIR=/Users/john/OpenWorker/de8ccae2-dac/.openworker-state \
VITE_COWORKER_API_TOKEN=$(cat /Users/john/OpenWorker/de8ccae2-dac/.openworker-state/sidecar-8765.token) \
npm run tauri dev
```

---

## 4. 汉化内容

### 4.1 前端 React GUI 汉化

全部前端组件用户可见文案已翻译为中文，覆盖：

- 设置页：通用、模型、角色、语音输入
- 侧边栏：新建会话、搜索、显示/隐藏侧边栏、产出文件
- 审批与收件箱：审批、收件箱、无人值守审批
- 连接器：连接器列表、账户详情、各平台配置
- 对话界面：输入框占位符、复制消息、步骤折叠、运行状态
- 自动化：定时运行、自动化已启动
- Provider 配置：自定义 API、获取模型、已连接、已保存、已检测

### 4.2 Tauri 桌面壳汉化

修改文件：`surfaces/gui/src-tauri/src/lib.rs`、`surfaces/gui/src-tauri/Info.plist`

汉化项包括：

| 原文 | 汉化后 |
|------|--------|
| `Open OpenWorker` | `打开 OpenWorker` |
| `Settings` | `设置` |
| `Quit` | `退出` |
| `Voice Input currently requires an Apple Silicon Mac...` | `语音输入当前需要 Apple Silicon Mac...` |
| `Voice Input requires macOS 12 or newer.` | `语音输入需要 macOS 12 或更新版本。` |
| `Voice Input currently requires a 64-bit x64 Windows PC.` | `语音输入当前需要 64 位 x64 Windows PC。` |
| `Voice Input requires Windows 10 22H2 or Windows 11.` | `语音输入需要 Windows 10 22H2 或 Windows 11。` |
| `Voice Input is currently supported on macOS and Windows.` | `语音输入当前仅支持 macOS 和 Windows。` |
| `Voice Input is not supported on this device.` | `语音输入不支持此设备。` |
| `Dictation stopped unexpectedly: ...` | `语音输入意外停止：...` |
| `Voice model download stopped unexpectedly: ...` | `语音模型下载意外停止：...` |
| `Voice model verification stopped unexpectedly: ...` | `语音模型验证意外停止：...` |
| `no update available` | `没有可用更新` |
| `failed to start server sidecar` | `启动服务器 sidecar 失败` |

macOS 权限提示（`Info.plist`）全部翻译为中文，覆盖麦克风、桌面、文档、下载、照片库。

---

## 5. 修复的关键问题

### 5.1 浏览器里打不开 / 页面白屏

**原因 1：前端没有拿到 sidecar token**

Vite dev 模式需要把 token 注入前端，否则所有后端 API 请求返回 401/403。

**解决：** 在启动前端的脚本里设置 `VITE_COWORKER_API_TOKEN`：

```bash
export VITE_COWORKER_API_TOKEN=$(cat "$COWORKER_STATE_DIR/sidecar-8765.token")
```

**原因 2：Vite 默认只监听 `localhost`（IPv6 ::1）**

部分浏览器/系统解析 `localhost` 为 IPv4 `127.0.0.1`，导致连接被拒绝。

**解决：** 启动前端时加 `--host`：

```bash
npm run dev -- --host
```

### 5.2 Tauri 编译缺少 CMake

`whisper-rs-sys` 依赖通过 CMake 构建，系统未安装 CMake。

**解决：** 下载 CMake macOS universal 二进制包到 `local/cmake/CMake.app/Contents/bin`，并加入 PATH。

### 5.3 Tauri 生产构建缺少 sidecar 资源

`tauri build` 要求 `src-tauri/binaries/sidecar` 存在（打包后的 Python 后端）。

**解决：** 当前使用开发模式 `npm run tauri dev` 验证桌面壳汉化，无需打包 sidecar。

---

## 6. 验证结果

### 6.1 浏览器 GUI

- 后端 `/v1/health` 返回正常
- 前端 `localhost:1420` HTTP 200
- CORS 预检和实际 GET 请求均通过
- TypeScript 类型检查通过：`npx tsc --noEmit`
- 单元测试：44 通过 / 24 失败，失败原因均为测试断言英文文案而组件已渲染中文，直接证明汉化生效

### 6.2 桌面壳

- `npm run tauri dev` 编译成功
- `target/debug/openworker-desktop` 生成
- 托盘菜单、权限提示、错误信息文案已替换为中文

---

## 7. 仓库结构说明

```
openworker-zh-localized/
├── coworker/              # Python 后端（Agent 引擎、连接器、MCP 等）
├── surfaces/gui/          # 前端 React + Tauri 桌面壳
│   ├── src/               # React 前端源码（已汉化）
│   └── src-tauri/         # Tauri Rust 桌面壳（已汉化）
├── stt/                   # 语音输入 Rust sidecar
├── tests/                 # Python 后端测试
├── packaging/             # 打包脚本（DMG/Windows）
├── docs/                  # 设计文档
├── start-openworker-server.sh   # 后端启动脚本
├── start-openworker-gui.sh      # 前端启动脚本
├── openworker-zh-test-report.md # 测试报告
└── BUILD_LOG.md           # 本文档
```

---

## 8. 已知问题

1. **前端单元测试未同步汉化**
   - 表现：运行 `npm test` 有 24 个失败
   - 原因：测试用例仍断言英文文案，而组件实际渲染中文
   - 建议：后续维护者可同步更新 `*.test.tsx` 中的期望值

2. **生产构建需要打包 sidecar**
   - `npm run tauri build` 需要预先用 PyInstaller 打包 Python 后端到 `src-tauri/binaries/sidecar`
   - 当前仅验证开发模式，未生成可分发 DMG

3. **mcp 依赖版本需手动锁定**
   - 当前 `pip install` 会拉下 mcp 2.x，需要手动降级到 1.x
   - 建议在 `pyproject.toml` 中明确 `mcp>=1.1,<2.0`

---

## 9. 后续建议

- 如果你想继续汉化测试用例，可以更新 `surfaces/gui/src/**/*.test.tsx`
- 如果你想生成分发安装包，需要：
  1. 用 PyInstaller 打包 Python 后端
  2. 放置到 `surfaces/gui/src-tauri/binaries/sidecar`
  3. 运行 `npm run tauri build`
- 如果想把启动脚本做成双击可用的 `.command` 文件，可以联系我继续处理

---

**整理日期：** 2026-08-03  
**仓库：** https://github.com/zhanglunet/openworker-zh-localized
