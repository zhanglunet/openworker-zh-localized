export const repoReport = {
  "generatedAt": "2026-08-04T00:31:16Z",
  "branch": "main",
  "head": "a107546f63d32b42a657d8551568b2298cd87011",
  "shortHead": "a107546",
  "totalFiles": 527,
  "byExt": [
    {
      "name": "py",
      "count": 221
    },
    {
      "name": "ts",
      "count": 105
    },
    {
      "name": "tsx",
      "count": 78
    },
    {
      "name": "svg",
      "count": 23
    },
    {
      "name": "png",
      "count": 22
    },
    {
      "name": "md",
      "count": 14
    },
    {
      "name": "json",
      "count": 12
    },
    {
      "name": "[none]",
      "count": 7
    },
    {
      "name": "html",
      "count": 5
    },
    {
      "name": "yml",
      "count": 5
    },
    {
      "name": "mjs",
      "count": 4
    },
    {
      "name": "rs",
      "count": 4
    },
    {
      "name": "sh",
      "count": 4
    },
    {
      "name": "toml",
      "count": 4
    },
    {
      "name": "css",
      "count": 3
    },
    {
      "name": "dmg",
      "count": 2
    },
    {
      "name": "js",
      "count": 2
    },
    {
      "name": "lock",
      "count": 2
    }
  ],
  "byTopDir": [
    {
      "name": "surfaces",
      "count": 228
    },
    {
      "name": "coworker",
      "count": 127
    },
    {
      "name": "tests",
      "count": 93
    },
    {
      "name": "website",
      "count": 36
    },
    {
      "name": "packaging",
      "count": 10
    },
    {
      "name": "docs",
      "count": 9
    },
    {
      "name": ".github",
      "count": 5
    },
    {
      "name": "stt",
      "count": 4
    },
    {
      "name": "ui-mocks",
      "count": 4
    },
    {
      "name": "releases",
      "count": 3
    },
    {
      "name": ".gitignore",
      "count": 1
    },
    {
      "name": "BUILD_LOG.md",
      "count": 1
    },
    {
      "name": "LICENSE",
      "count": 1
    },
    {
      "name": "openworker-zh-test-report.md",
      "count": 1
    },
    {
      "name": "pyproject.toml",
      "count": 1
    },
    {
      "name": "README.md",
      "count": 1
    },
    {
      "name": "start-openworker-gui.sh",
      "count": 1
    },
    {
      "name": "start-openworker-server.sh",
      "count": 1
    }
  ],
  "highlights": [
    {
      "title": "桌面壳",
      "files": [
        "surfaces/gui/src-tauri/src/lib.rs",
        "surfaces/gui/src-tauri/tauri.conf.json"
      ],
      "summary": "Tauri 负责启动窗口、托盘、原生权限、语音输入、更新检查和 Python sidecar 生命周期。"
    },
    {
      "title": "前端工作台",
      "files": [
        "surfaces/gui/src/App.tsx",
        "surfaces/gui/src/api.ts",
        "surfaces/gui/src/components"
      ],
      "summary": "React 工作台承载会话、审批、收件箱、连接器、模型配置、产物和实时事件流。"
    },
    {
      "title": "本地服务",
      "files": [
        "coworker/server/app.py",
        "coworker/server/manager.py"
      ],
      "summary": "FastAPI sidecar 暴露 REST 与 WebSocket，集中协调会话、任务、审计、自动化和持久化。"
    },
    {
      "title": "Agent 运行核心",
      "files": [
        "coworker/engine.py",
        "coworker/permissions.py",
        "coworker/tools",
        "coworker/providers"
      ],
      "summary": "TurnEngine、PermissionEngine、工具注册表和 ProviderRouter 组成 model-tool 循环。"
    },
    {
      "title": "连接器与 MCP",
      "files": [
        "coworker/connectors",
        "coworker/mcp",
        "surfaces/gui/src/connectors"
      ],
      "summary": "内置连接器、MCP server 管理和 OAuth/账户视图把外部系统接入本地运行时。"
    },
    {
      "title": "中文站与发布物",
      "files": [
        "website",
        "docs",
        "releases"
      ],
      "summary": "中文站、架构信息图、源码分析、日志周报和 macOS DMG 下载入口随仓库维护。"
    }
  ],
  "architectureFlow": [
    "用户目标",
    "React/Tauri 工作台",
    "FastAPI sidecar",
    "SessionManager",
    "TurnEngine",
    "ProviderRouter",
    "模型",
    "工具/MCP/连接器",
    "权限与审计",
    "交付物"
  ],
  "runtimeFlow": [
    "下载 DMG 或源码启动",
    "Tauri/浏览器加载 GUI",
    "sidecar 选择端口并生成 token",
    "GUI 通过 REST/WebSocket 连接本地服务",
    "用户发起目标与上下文",
    "模型提出计划与工具调用",
    "权限系统判断风险与批准策略",
    "工具结果写入会话、审计、Inbox 或文件",
    "最终结果返回用户"
  ],
  "apiGroups": [
    {
      "name": "健康与启动",
      "examples": [
        "/v1/health",
        "WebSocket /ws/events"
      ]
    },
    {
      "name": "会话",
      "examples": [
        "/v1/sessions",
        "/ws/session/{sessionId}"
      ]
    },
    {
      "name": "模型提供商",
      "examples": [
        "/v1/providers",
        "/v1/providers/models"
      ]
    },
    {
      "name": "连接器",
      "examples": [
        "/v1/connectors/*",
        "OAuth 状态轮询"
      ]
    },
    {
      "name": "MCP",
      "examples": [
        "/v1/mcp/*",
        "stdio / streamable-http server"
      ]
    },
    {
      "name": "自动化与 Inbox",
      "examples": [
        "/v1/automations/*",
        "/v1/inbox/*"
      ]
    },
    {
      "name": "本地文件与产物",
      "examples": [
        "文件工具",
        "目录授权",
        "产物预览"
      ]
    }
  ],
  "recentCommits": [
    {
      "hash": "a107546",
      "date": "2026-08-04",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "141aae5",
      "date": "2026-08-04",
      "subject": "site: add OpenWorker recommendation article"
    },
    {
      "hash": "14c394f",
      "date": "2026-08-03",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "6039c07",
      "date": "2026-08-04",
      "subject": "docs: record deferred signing prerequisites"
    },
    {
      "hash": "97ac065",
      "date": "2026-08-03",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "d0002c6",
      "date": "2026-08-04",
      "subject": "release: prepare signed Chinese auto updates (#3)"
    },
    {
      "hash": "d4c6985",
      "date": "2026-08-03",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "c6c4704",
      "date": "2026-08-04",
      "subject": "docs: refresh reports after Cloudflare deploy"
    },
    {
      "hash": "6aeb622",
      "date": "2026-08-03",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "f4fabd1",
      "date": "2026-08-04",
      "subject": "sync: merge upstream OpenWorker 01b6f83 (#2)"
    },
    {
      "hash": "7df3ca0",
      "date": "2026-08-03",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "a6b5334",
      "date": "2026-08-04",
      "subject": "docs: add source analysis and update reports pages"
    }
  ],
  "weeklyCommits": [
    {
      "hash": "a107546",
      "date": "2026-08-04",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "141aae5",
      "date": "2026-08-04",
      "subject": "site: add OpenWorker recommendation article"
    },
    {
      "hash": "14c394f",
      "date": "2026-08-03",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "6039c07",
      "date": "2026-08-04",
      "subject": "docs: record deferred signing prerequisites"
    },
    {
      "hash": "97ac065",
      "date": "2026-08-03",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "d0002c6",
      "date": "2026-08-04",
      "subject": "release: prepare signed Chinese auto updates (#3)"
    },
    {
      "hash": "d4c6985",
      "date": "2026-08-03",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "c6c4704",
      "date": "2026-08-04",
      "subject": "docs: refresh reports after Cloudflare deploy"
    },
    {
      "hash": "6aeb622",
      "date": "2026-08-03",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "f4fabd1",
      "date": "2026-08-04",
      "subject": "sync: merge upstream OpenWorker 01b6f83 (#2)"
    },
    {
      "hash": "7df3ca0",
      "date": "2026-08-03",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "a6b5334",
      "date": "2026-08-04",
      "subject": "docs: add source analysis and update reports pages"
    },
    {
      "hash": "f36b220",
      "date": "2026-08-04",
      "subject": "Update README download and site preview"
    },
    {
      "hash": "11fd242",
      "date": "2026-08-04",
      "subject": "Add localized macOS app download"
    },
    {
      "hash": "6a46c2a",
      "date": "2026-08-04",
      "subject": "Distinguish Chinese macOS app bundle"
    },
    {
      "hash": "96db0d2",
      "date": "2026-08-03",
      "subject": "Add OpenWorker architecture infographic page"
    },
    {
      "hash": "0759ba3",
      "date": "2026-08-03",
      "subject": "Add Cloudflare deployment config for website"
    },
    {
      "hash": "cc6d867",
      "date": "2026-08-03",
      "subject": "Merge pull request #1 from zhanglunet/agent/add-openworker-cn-site"
    },
    {
      "hash": "617c4fb",
      "date": "2026-08-03",
      "subject": "Add OpenWorker Chinese website"
    },
    {
      "hash": "80098ae",
      "date": "2026-08-03",
      "subject": "Merge remote-tracking branch 'origin/main'"
    },
    {
      "hash": "14833d9",
      "date": "2026-08-03",
      "subject": "chore(gui): 汉化 macOS 权限弹窗说明、托盘菜单与语音输入提示文案"
    },
    {
      "hash": "a1912fc",
      "date": "2026-08-03",
      "subject": "docs: rewrite README with full install, usage, and localization guide"
    },
    {
      "hash": "3f50a54",
      "date": "2026-08-03",
      "subject": "docs: add BUILD_LOG.md with full localization setup notes"
    },
    {
      "hash": "d0ccdc9",
      "date": "2026-08-03",
      "subject": "Initial commit: OpenWorker 全量汉化版"
    },
    {
      "hash": "4b19f8b",
      "date": "2026-08-03",
      "subject": "Initial commit"
    }
  ]
} as const;
