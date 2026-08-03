# OpenWorker 中文站

OpenWorker 中文产品介绍与源码分析站点。网站内容基于公开代码和文档整理，并明确区分上游项目与中文本地化仓库：

- 上游项目源码：[andrewyng/openworker](https://github.com/andrewyng/openworker)
- 中文本地化与本站仓库：[zhanglunet/openworker-zh-localized](https://github.com/zhanglunet/openworker-zh-localized)
- 官方网站：[openworker.com](https://openworker.com)

## 本地运行

需要 Node.js `>=22.13.0`。

```bash
npm install
npm run dev
```

## 验证与构建

```bash
npm test
npm run build
```

站点基于 vinext 构建，可输出 Cloudflare Workers 兼容产物。

## 部署到 Cloudflare

```bash
npm run deploy:cloudflare
```

部署脚本会先重新构建站点，再通过 `wrangler.jsonc` 发布到当前 Wrangler 登录的 Cloudflare 账号。

## 内容范围

- OpenWorker 中文产品说明
- 模型、连接器与工作流程
- React/Tauri 桌面层与 Python Agent Server 架构
- TurnEngine、权限系统和数据边界分析
- 上游源码与中文本地化仓库入口

## 归属说明

OpenWorker 项目及其源代码由上游仓库 `andrewyng/openworker` 提供。本仓库负责中文本地化、中文介绍站和相关分析材料；本站不是 OpenWorker 官方网站。
