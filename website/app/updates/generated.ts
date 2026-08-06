export const repoReport = {
  "generatedAt": "2026-08-06T01:22:36Z",
  "branch": "main",
  "head": "d182a246427e53e4ff9099816f4048443e219efb",
  "shortHead": "d182a24",
  "totalFiles": 578,
  "byExt": [
    {
      "name": "py",
      "count": 250
    },
    {
      "name": "ts",
      "count": 105
    },
    {
      "name": "tsx",
      "count": 79
    },
    {
      "name": "md",
      "count": 28
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
      "count": 13
    },
    {
      "name": "yml",
      "count": 9
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
      "name": "sh",
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
      "count": 229
    },
    {
      "name": "coworker",
      "count": 132
    },
    {
      "name": "tests",
      "count": 100
    },
    {
      "name": "docs",
      "count": 45
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
      "name": ".github",
      "count": 7
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
  "enterpriseLayers": [
    {
      "layer": "模型层 · 私有模型",
      "grade": "配置级",
      "summary": "Provider 注册表内置 Custom（OpenAI 兼容 base_url）与 Ollama 构建器，企业 vLLM/网关的端点、端口与模型版本直接配置接入；模型能力在能力矩阵登记。",
      "files": [
        "coworker/providers/registry.py",
        "coworker/providers/matrix.py",
        "docs/config.example.toml"
      ]
    },
    {
      "layer": "技能层 · 企业技能包",
      "grade": "资产级",
      "summary": "SKILL.md 规范（YAML frontmatter + 渐进式加载），全局 state_dir()/skills 与工作区 .coworker/skills 双目录；企业 SOP 技能与大表哥 excel-ai-analyst 预置即用。",
      "files": [
        "coworker/skills/base.py",
        "coworker/skills/store.py"
      ]
    },
    {
      "layer": "知识层 · 企业知识库",
      "grade": "资产级起步",
      "summary": "无内置向量 RAG；现实路径是文件根挂载 + 技能内置知识起步，中期把企业知识库封装成 MCP 检索服务，权限留在知识库侧。",
      "files": [
        "coworker/roots.py",
        "coworker/project.py",
        "coworker/memory"
      ]
    },
    {
      "layer": "工具层 · 企业 CLI 与内部系统",
      "grade": "配置级 + 代码级",
      "summary": "企业 CLI 首选封装为 MCP server 注册；内部系统按连接器 descriptor 模式扩展；allowed_commands 白名单与审批模式管控执行边界。",
      "files": [
        "coworker/mcp",
        "coworker/connectors/descriptors.py",
        "coworker/cli.py"
      ]
    },
    {
      "layer": "专属功能 · 大表哥表格助手",
      "grade": "三层渐进",
      "summary": "L1 预置 excel-ai-analyst 技能（表格当代码逆向：探测/公式链/全量验证）→ L2 前端表格助手入口 → L3 excel_ai 注册为内置工具。",
      "files": [
        "coworker/tools",
        "surfaces/gui/src/App.tsx"
      ]
    },
    {
      "layer": "品牌层 · 换肤与命名",
      "grade": "资产级",
      "summary": "颜色单一事实源是 styles.css 的 CSS 变量（Tailwind 仅映射 token），换肤=覆盖一个变量块；应用名/Bundle ID/图标/更新源集中在 tauri.conf.json。",
      "files": [
        "surfaces/gui/src/styles.css",
        "surfaces/gui/tailwind.config.js",
        "surfaces/gui/src-tauri/tauri.conf.json"
      ]
    },
    {
      "layer": "同步层 · 三仓不覆盖同步",
      "grade": "流水线",
      "summary": "上游→汉化版每日自动合并开 PR、冲突自动开 Issue；企业私有仓复制同款流水线单向对接汉化仓，配合 enterprise/ 目录隔离与挂载点纪律实现定制零覆盖。",
      "files": [
        ".github/workflows/sync-upstream.yml"
      ]
    },
    {
      "layer": "发布层 · 多平台打包与更新",
      "grade": "流水线",
      "summary": "发布矩阵覆盖 macOS Apple Silicon/Intel 双 DMG 与 Windows MSI/NSIS，latest-zh.json 驱动 Tauri 自动更新；企业版换名称、签名密钥与更新源即用。",
      "files": [
        ".github/workflows/release.yml",
        "packaging/build_dmg.sh",
        "packaging/make_update_manifest.py"
      ]
    }
  ],
  "recentCommits": [
    {
      "hash": "d182a24",
      "date": "2026-08-06",
      "subject": "feat: 知识库常驻挂载 + 企业 CLI→MCP 桥（M2 的 2.1 与 2.2）"
    },
    {
      "hash": "d86177b",
      "date": "2026-08-06",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "ee6e05b",
      "date": "2026-08-06",
      "subject": "feat(provisioning): 首启把已发布的默认值种进空的状态目录（M1 配置预置）"
    },
    {
      "hash": "3e2fdca",
      "date": "2026-08-06",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "f2bcad5",
      "date": "2026-08-06",
      "subject": "feat(providers): 私有模型能力声明覆盖层 + 端点能力实测脚本（M1）"
    },
    {
      "hash": "5dd7db0",
      "date": "2026-08-06",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "dfd9907",
      "date": "2026-08-06",
      "subject": "feat(sheets): excel_ai 注册为内置工具（大表哥 L3）"
    },
    {
      "hash": "fa89654",
      "date": "2026-08-06",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "78a126d",
      "date": "2026-08-06",
      "subject": "feat(gui): 表格助手入口（大表哥 L2）"
    },
    {
      "hash": "b9c6deb",
      "date": "2026-08-06",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "068e1db",
      "date": "2026-08-06",
      "subject": "docs(upstream): 归档调度器竞态的上游提交材料"
    },
    {
      "hash": "b09e893",
      "date": "2026-08-06",
      "subject": "test(automation): 补上 skip-on-overlap 竞态的确定性回归用例"
    }
  ],
  "weeklyCommits": [
    {
      "hash": "d182a24",
      "date": "2026-08-06",
      "subject": "feat: 知识库常驻挂载 + 企业 CLI→MCP 桥（M2 的 2.1 与 2.2）"
    },
    {
      "hash": "d86177b",
      "date": "2026-08-06",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "ee6e05b",
      "date": "2026-08-06",
      "subject": "feat(provisioning): 首启把已发布的默认值种进空的状态目录（M1 配置预置）"
    },
    {
      "hash": "3e2fdca",
      "date": "2026-08-06",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "f2bcad5",
      "date": "2026-08-06",
      "subject": "feat(providers): 私有模型能力声明覆盖层 + 端点能力实测脚本（M1）"
    },
    {
      "hash": "5dd7db0",
      "date": "2026-08-06",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "dfd9907",
      "date": "2026-08-06",
      "subject": "feat(sheets): excel_ai 注册为内置工具（大表哥 L3）"
    },
    {
      "hash": "fa89654",
      "date": "2026-08-06",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "78a126d",
      "date": "2026-08-06",
      "subject": "feat(gui): 表格助手入口（大表哥 L2）"
    },
    {
      "hash": "b9c6deb",
      "date": "2026-08-06",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "068e1db",
      "date": "2026-08-06",
      "subject": "docs(upstream): 归档调度器竞态的上游提交材料"
    },
    {
      "hash": "b09e893",
      "date": "2026-08-06",
      "subject": "test(automation): 补上 skip-on-overlap 竞态的确定性回归用例"
    },
    {
      "hash": "28c1e42",
      "date": "2026-08-06",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "7347760",
      "date": "2026-08-06",
      "subject": "fix(automation): 定时任务在 skip-on-overlap 下仍可能重复执行"
    },
    {
      "hash": "3923f58",
      "date": "2026-08-05",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "5f790df",
      "date": "2026-08-05",
      "subject": "feat(enterprise): 大表哥 excel-ai-analyst 技能包（PRD F4 的 L1 层）"
    },
    {
      "hash": "661dfe9",
      "date": "2026-08-05",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "6cbe8c2",
      "date": "2026-08-05",
      "subject": "docs(enterprise): 新增可直接执行的企业仓模板（建仓/同步/冒烟/发布）"
    },
    {
      "hash": "1647e48",
      "date": "2026-08-05",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "12a7c83",
      "date": "2026-08-05",
      "subject": "fix(windows): MSI 打包指定 zh-CN WiX 语言，修复中文产品名构建失败"
    },
    {
      "hash": "0394aa2",
      "date": "2026-08-05",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "8546ba0",
      "date": "2026-08-05",
      "subject": "ci: 测试版 Windows 只出 NSIS，并加 MSI 中文代码页诊断实验"
    },
    {
      "hash": "fb1b810",
      "date": "2026-08-05",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "fc875a3",
      "date": "2026-08-05",
      "subject": "ci: 测试版流水线支持手动触发发布并修正校验和生成"
    },
    {
      "hash": "ab204cf",
      "date": "2026-08-05",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "5f4e397",
      "date": "2026-08-05",
      "subject": "ci: 新增未签名测试版发布流水线"
    },
    {
      "hash": "5279588",
      "date": "2026-08-05",
      "subject": "sync: 记录上游 OpenWorker 01b6f83 已并入（修复祖先链）"
    },
    {
      "hash": "1dbebca",
      "date": "2026-08-05",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "41b32bd",
      "date": "2026-08-05",
      "subject": "ci: 新增中文站 Cloudflare 自动部署流水线"
    },
    {
      "hash": "aaeec98",
      "date": "2026-08-05",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "255da25",
      "date": "2026-08-04",
      "subject": "docs: 并入完整性检查发现的关键事实"
    },
    {
      "hash": "ed541e8",
      "date": "2026-08-04",
      "subject": "docs: 补充 sidecar 企业包打包与 updater 密钥切换断链说明"
    },
    {
      "hash": "726b11a",
      "date": "2026-08-04",
      "subject": "docs: 企业定制版全套准备文档 + 站点企业定制扩展点章节"
    },
    {
      "hash": "614f87e",
      "date": "2026-08-04",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "60c2e76",
      "date": "2026-08-04",
      "subject": "site: update Cloudflare compatibility date"
    },
    {
      "hash": "826d5c3",
      "date": "2026-08-04",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "cf6d1d0",
      "date": "2026-08-04",
      "subject": "site: remove redundant Cloudflare compat flag"
    },
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
    }
  ]
} as const;
