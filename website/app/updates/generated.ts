export const repoReport = {
  "generatedAt": "2026-08-04T07:00:26+09:00",
  "branch": "codex/sync-upstream-20260804",
  "head": "26d9a4c944b03bd4467670983912355c6c161367",
  "shortHead": "26d9a4c",
  "totalFiles": 521,
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
      "count": 77
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
      "name": "json",
      "count": 11
    },
    {
      "name": "md",
      "count": 11
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
      "name": "js",
      "count": 2
    },
    {
      "name": "lock",
      "count": 2
    },
    {
      "name": "plist",
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
      "count": 35
    },
    {
      "name": "packaging",
      "count": 10
    },
    {
      "name": "docs",
      "count": 6
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
      "name": "releases",
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
      "hash": "26d9a4c",
      "date": "2026-08-04",
      "subject": "docs: refresh reports after upstream sync"
    },
    {
      "hash": "02e4172",
      "date": "2026-08-04",
      "subject": "Merge remote-tracking branch 'upstream/main' into codex/sync-upstream-20260804"
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
    }
  ],
  "weeklyCommits": [
    {
      "hash": "26d9a4c",
      "date": "2026-08-04",
      "subject": "docs: refresh reports after upstream sync"
    },
    {
      "hash": "02e4172",
      "date": "2026-08-04",
      "subject": "Merge remote-tracking branch 'upstream/main' into codex/sync-upstream-20260804"
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
    },
    {
      "hash": "01b6f83",
      "date": "2026-08-01",
      "subject": "Merge pull request #393 from andrewyng/issue/ope-46"
    },
    {
      "hash": "997b2a9",
      "date": "2026-08-01",
      "subject": "Merge branch 'main' into issue/ope-46"
    },
    {
      "hash": "70e4610",
      "date": "2026-08-01",
      "subject": "Add support for Skills (#391)"
    },
    {
      "hash": "e0cb129",
      "date": "2026-07-30",
      "subject": "Merge pull request #356 from andrewyng/rpMacIntelBuild"
    },
    {
      "hash": "bfabfaa",
      "date": "2026-07-30",
      "subject": "ci: build macOS Intel on macos-15-intel"
    },
    {
      "hash": "ae7256f",
      "date": "2026-07-30",
      "subject": "Prepare app release 0.1.7: version bump"
    },
    {
      "hash": "907752b",
      "date": "2026-07-30",
      "subject": "Merge pull request #354 from andrewyng/rpArtifactWalkAndContextBar"
    },
    {
      "hash": "25dc283",
      "date": "2026-07-30",
      "subject": "fix: stop artifact walk entering OS app-data dirs; context bar off by default"
    },
    {
      "hash": "11d9f72",
      "date": "2026-07-30",
      "subject": "Merge pull request #353 from andrewyng/rpSsrfFollowup"
    },
    {
      "hash": "e5c5699",
      "date": "2026-07-30",
      "subject": "security: block CGNAT range and guard browser_open_url"
    },
    {
      "hash": "7e69398",
      "date": "2026-07-30",
      "subject": "Merge pull request #290 from Mr-Neutr0n/security/block-ssrf-in-url-tools"
    },
    {
      "hash": "38e1f03",
      "date": "2026-07-30",
      "subject": "Merge pull request #161 from psssnikhil/fix/inbox-reply-word-boundaries"
    },
    {
      "hash": "98445fe",
      "date": "2026-07-30",
      "subject": "Merge pull request #352 from andrewyng/rpMcpGlobalWins"
    },
    {
      "hash": "6217dbc",
      "date": "2026-07-30",
      "subject": "mcp: global config wins on name clash with a trusted workspace"
    },
    {
      "hash": "5071451",
      "date": "2026-07-30",
      "subject": "Merge pull request #351 from andrewyng/rpCompactionPolish"
    },
    {
      "hash": "cca0421",
      "date": "2026-07-30",
      "subject": "Merge pull request #215 from HaoChiBao/security/workspace-mcp-trust-gate"
    },
    {
      "hash": "fe034c8",
      "date": "2026-07-30",
      "subject": "models: Kimi K3 via Together (1M window, vision); right-align the more/less toggle"
    },
    {
      "hash": "1e819e0",
      "date": "2026-07-30",
      "subject": "transcript: clamp long user messages with a more…/less… toggle"
    },
    {
      "hash": "f9f51c9",
      "date": "2026-07-30",
      "subject": "compaction: live progress signal + user-message cap"
    },
    {
      "hash": "b303823",
      "date": "2026-07-30",
      "subject": "Merge pull request #347 from andrewyng/review/ope-27"
    },
    {
      "hash": "330010c",
      "date": "2026-07-29",
      "subject": "compaction: harden the smoke against per-turn event loops (OPE-27)"
    },
    {
      "hash": "0bf9b87",
      "date": "2026-07-29",
      "subject": "compaction: repeated-compaction smoke through the manager (OPE-27 4/4)"
    },
    {
      "hash": "4fa8acf",
      "date": "2026-07-29",
      "subject": "compaction: Settings overrides + GUI divider (OPE-27 3/4)"
    },
    {
      "hash": "f08a3c4",
      "date": "2026-07-29",
      "subject": "compaction: engine hook, failure policy, persistence (OPE-27 2/4)"
    },
    {
      "hash": "028d42e",
      "date": "2026-07-29",
      "subject": "compaction: pure module + tests (OPE-27 1/4)"
    },
    {
      "hash": "55362ab",
      "date": "2026-07-29",
      "subject": "Merge branch 'main' of https://github.com/andrewyng/openworker into issue/ope-46"
    },
    {
      "hash": "ff86735",
      "date": "2026-07-28",
      "subject": "security: block loopback/private/metadata addresses in model-supplied URL fetches"
    },
    {
      "hash": "f96ad4c",
      "date": "2026-07-28",
      "subject": "Merge pull request #304 from andrewyng/rpTokenMetering"
    },
    {
      "hash": "8674e30",
      "date": "2026-07-28",
      "subject": "Pin mcp<2 — 2.0.0 removed streamablehttp_client"
    },
    {
      "hash": "27311cd",
      "date": "2026-07-28",
      "subject": "Usage popover: 'Uncached input' when a cache split exists"
    },
    {
      "hash": "d1524b3",
      "date": "2026-07-28",
      "subject": "Usage popover: label rows as session totals"
    },
    {
      "hash": "a35b505",
      "date": "2026-07-28",
      "subject": "Usage popover: add cumulative Total input row"
    },
    {
      "hash": "92c1833",
      "date": "2026-07-28",
      "subject": "Usage popover: one field per line"
    },
    {
      "hash": "a7df344",
      "date": "2026-07-28",
      "subject": "Gitignore .env for local BYO-key smoke runs"
    },
    {
      "hash": "0de0da1",
      "date": "2026-07-28",
      "subject": "Docs: reflect the Responses/Chat-Completions provider split"
    },
    {
      "hash": "9d3f6d3",
      "date": "2026-07-28",
      "subject": "Route native OpenAI (blank endpoint) to the Responses provider"
    },
    {
      "hash": "26b4c80",
      "date": "2026-07-28",
      "subject": "OpenAI Responses provider: reasoning + tools for native OpenAI models"
    },
    {
      "hash": "8991d30",
      "date": "2026-07-27",
      "subject": "Enable prompt caching on the Anthropic provider"
    },
    {
      "hash": "7a108b2",
      "date": "2026-07-27",
      "subject": "Show per-session token usage in the composer"
    },
    {
      "hash": "979badb",
      "date": "2026-07-27",
      "subject": "Meter token usage across all model providers"
    },
    {
      "hash": "3766805",
      "date": "2026-07-27",
      "subject": "Merge pull request #259 from andrewyng/rpModelProviders"
    },
    {
      "hash": "d386396",
      "date": "2026-07-27",
      "subject": "Update README with badge from trendshift"
    }
  ]
} as const;
