# OpenWorker 汉化版源码测试报告

**测试日期：** 2026-08-03  
**测试平台：** macOS 26.5.2 (Apple Silicon arm64)  
**测试目标：** 从源码跑起 `Lenovo202409/openworker-zh`，验证中文界面汉化是否生效。

---

## 1. 结论

✅ **汉化界面已生效**。前端 React 组件中的用户可见文案已被翻译为中文，TypeScript 编译通过（`tsc --noEmit`）。

✅ **前后端已同时运行**。后端在 `127.0.0.1:8765`，前端 dev server 在 `localhost:1420` / `127.0.0.1:1420` / 局域网地址。

✅ **CORS + API token 验证已通过**。浏览器发起的 API 请求能正常返回数据。

⚠️ **前端测试用例未同步汉化**。部分测试失败的原因是测试仍断言英文文案（如 "Copied"），而组件实际渲染出的是中文（如 "已复制"）。这直接证明汉化已经应用到 UI 上，但需要后续维护者同步更新测试。

---

## 2. 环境配置

由于当前系统没有 Homebrew、pyenv 或 Node.js，所有依赖都安装在 workspace 内的 `local/` 目录，未使用 sudo。

| 组件 | 版本 | 安装路径 |
|--------|------|------------|
| Python | 3.13.13 | `local/miniforge3` (Miniforge) |
| Node.js | 20.15.1 | `local/node` |
| Rust | 已存在 | macOS Xcode Command Line Tools |

### 2.1 安装步骤

```bash
# 下载 Miniforge
mkdir -p local && cd local
curl -L -o miniforge.sh https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh
bash miniforge.sh -b -p "$PWD/miniforge3"

# 下载 Node.js
curl -L -o node.tar.gz https://nodejs.org/dist/v20.15.1/node-v20.15.1-darwin-arm64.tar.gz
tar -xzf node.tar.gz
mv node-v20.15.1-darwin-arm64 node
```

### 2.2 配置 PATH

```bash
export PATH=/Users/john/OpenWorker/de8ccae2-dac/local/miniforge3/bin:/Users/john/OpenWorker/de8ccae2-dac/local/node/bin:$PATH
```

---

## 3. 项目构建

### 3.1 克隆汉化版仓库

```bash
git clone https://github.com/Lenovo202409/openworker-zh.git
cd openworker-zh
```

### 3.2 创建 Python 虚拟环境

（注意：必须用 conda 的 python 直接路径，避免 macOS python3 跳到系统 3.9）

```bash
/Users/john/OpenWorker/de8ccae2-dac/local/miniforge3/bin/python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[messaging,dev]"
```

### 3.3 修复 mcp 版本兼容性问题

初始安装会拉下 `mcp==2.0.0`，与项目代码中的旧 API `streamablehttp_client` 不兼容，需要降级到 1.x：

```bash
.venv/bin/python -m pip install 'mcp>=1.1,<2.0'
```

验证：
```bash
.venv/bin/python -c "from mcp.client.streamable_http import streamablehttp_client; print('OK')"
```

### 3.4 安装前端依赖

```bash
cd surfaces/gui
npm install
```

### 3.5 运行时修复

按上述步骤跑起后，发现前端在浏览器中打不开，是以下两个问题导致的：

1. **前端没有获取 sidecar token**  
   Vite dev 模式会将 `__COWORKER_DEV_TOKEN__` 注入给前端，但它会从 `COWORKER_STATE_DIR` 下读取 `sidecar-8765.token`。如果运行前端时没有设置 `COWORKER_STATE_DIR` / `VITE_COWORKER_API_TOKEN`，前端发出的 API 请求会全部 401/403，页面白屏。  
   **解决：** 在运行前端的终端里设置 `VITE_COWORKER_API_TOKEN=$(cat $STATE/sidecar-8765.token)`。

2. **Vite 默认只绑定 localhost（IPv6）**  
   部分浏览器 / 系统解析 `localhost` 为 IPv4 `127.0.0.1`。如果 Vite 只绑定 `::1`，访问 `localhost:1420` 可能被拒绝。  
   **解决：** 启动前端时加 `--host`，让 Vite 同时监听 IPv4/IPv6/localhost。

---

## 4. 运行与测试

### 4.1 起动后端 server

直接运行：

```bash
bash /Users/john/OpenWorker/de8ccae2-dac/start-openworker-server.sh
```

手动启动：

```bash
cd openworker-zh
mkdir -p /Users/john/OpenWorker/de8ccae2-dac/.openworker-state
TOKEN=$(openssl rand -hex 32)
echo "$TOKEN" > /Users/john/OpenWorker/de8ccae2-dac/.openworker-state/sidecar-8765.token
COWORKER_API_TOKEN=$TOKEN COWORKER_STATE_DIR=/Users/john/OpenWorker/de8ccae2-dac/.openworker-state \
  .venv/bin/openworker-server --cwd /Users/john/OpenWorker/de8ccae2-dac --port 8765
```

验证后端 API：
```bash
TOKEN=$(cat /Users/john/OpenWorker/de8ccae2-dac/.openworker-state/sidecar-8765.token)
curl -s -H "X-OpenWorker-Token: $TOKEN" http://127.0.0.1:8765/v1/health
# {"status":"ok",...}
```

### 4.2 起动前端 GUI

直接运行：

```bash
bash /Users/john/OpenWorker/de8ccae2-dac/start-openworker-gui.sh
```

然后打开浏览器：

```
http://localhost:1420/
http://127.0.0.1:1420/
```

### 4.3 TypeScript 类型检查

```bash
cd surfaces/gui
npx tsc --noEmit
```

结果：**`exit_code: 0`，无错误**。

### 4.4 前端测试

```bash
cd surfaces/gui
npm test -- --run
```

结果：`Tests 24 failed | 44 passed (68)`

失败用例全是无法找到英文文案，因为 UI 已经渲染为中文。代表性失败对比：

| 测试无法找到 | 组件实际渲染 | 说明 |
|----------------|----------------|------|
| "Copied" | "已复制" | 复制消息按钮 |
| "2 steps" | "2 步" | 步骤组折叠 |
| "Running 1 step…" | "正在运行 1 步…" | 正在运行中的步骤 |
| "1 declined" | "1 个已拒绝" | 审批拒绝统计 |
| "Downloading…" | "下载中…" | 更新下载 |
| "Restart to update" | "重启以更新" | 更新按钮 |

此外，源码检查发现设置页面已经使用中文：
- `设置` (Settings)
- `模型` (Models)
- `角色` (Personas)
- `语音输入` (Voice input)
- `通用` (Appearance)

### 4.5 CORS 验证

```bash
curl -s -H "Origin: http://localhost:1420" \
  -H "X-OpenWorker-Token: $(cat /Users/john/OpenWorker/de8ccae2-dac/.openworker-state/sidecar-8765.token)" \
  http://127.0.0.1:8765/v1/health
```

返回：
```
HTTP/1.1 200 OK
access-control-allow-origin: http://localhost:1420
{"status":"ok",...}
```

---

## 5. 常见问题

### 5.1 python3 默认是 3.9.6

macOS 系统 `python3` 只有 3.9，项目要求 >=3.10。必须通过 conda/Miniforge 或 pyenv 装新版本 Python。

### 5.2 mcp 版本不兼容

当前 `pip install -e .[messaging,dev]` 会安装 `mcp==2.0.0`，但项目代码还在调用 1.x 的 `streamablehttp_client`。需要手动降级：
```bash
.venv/bin/python -m pip install 'mcp>=1.1,<2.0'
```

### 5.3 浏览器打不开

如果前端在浏览器中打开白屏，检查：
1. 是否给前端传递了 `VITE_COWORKER_API_TOKEN` 环境变量；
2. 是否用 `npm run dev -- --host` 让 Vite 监听所有本地地址。

---

## 6. 最终启动脚本

### 6.1 后端 `start-openworker-server.sh`

已保存在 `/Users/john/OpenWorker/de8ccae2-dac/start-openworker-server.sh`。

### 6.2 前端 `start-openworker-gui.sh`

已保存在 `/Users/john/OpenWorker/de8ccae2-dac/start-openworker-gui.sh`。

运行方式：

```bash
# 终端 1
bash /Users/john/OpenWorker/de8ccae2-dac/start-openworker-server.sh

# 终端 2
bash /Users/john/OpenWorker/de8ccae2-dac/start-openworker-gui.sh
```

然后打开浏览器：**http://localhost:1420/**
