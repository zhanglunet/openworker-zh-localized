export const repoReport = {
  "generatedAt": "2026-10-26T08:57:57+08:00",
  "branch": "main",
  "head": "6b00b3aacbad502e6d256661716b629daaec5472",
  "shortHead": "6b00b3a",
  "totalFiles": 668,
  "byExt": [
    {
      "name": "py",
      "count": 276
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
      "count": 70
    },
    {
      "name": "png",
      "count": 25
    },
    {
      "name": "svg",
      "count": 23
    },
    {
      "name": "json",
      "count": 20
    },
    {
      "name": "yml",
      "count": 15
    },
    {
      "name": "html",
      "count": 8
    },
    {
      "name": "[none]",
      "count": 7
    },
    {
      "name": "sh",
      "count": 5
    },
    {
      "name": "css",
      "count": 4
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
      "name": "dmg",
      "count": 2
    },
    {
      "name": "js",
      "count": 2
    },
    {
      "name": "jsonc",
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
      "count": 134
    },
    {
      "name": "tests",
      "count": 114
    },
    {
      "name": "docs",
      "count": 94
    },
    {
      "name": "website",
      "count": 36
    },
    {
      "name": ".github",
      "count": 11
    },
    {
      "name": "role-packs",
      "count": 11
    },
    {
      "name": "packaging",
      "count": 10
    },
    {
      "name": "scripts",
      "count": 7
    },
    {
      "name": "ui-mocks",
      "count": 6
    },
    {
      "name": "stt",
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
      "name": "README.en.md",
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
      "hash": "6b00b3a",
      "date": "2026-10-26",
      "subject": "Merge pull request #53 from zhanglunet/trend/prd-184-t3-build-in-public-template"
    },
    {
      "hash": "d2abaf7",
      "date": "2026-10-26",
      "subject": "Merge pull request #52 from zhanglunet/trend/prd-183-t3-zh-role-packs"
    },
    {
      "hash": "32da465",
      "date": "2026-10-26",
      "subject": "Merge pull request #51 from zhanglunet/trend/prd-184-t2-build-in-public-template"
    },
    {
      "hash": "d40bf1f",
      "date": "2026-10-26",
      "subject": "Merge pull request #50 from zhanglunet/trend/prd-183-t2-zh-role-packs"
    },
    {
      "hash": "d371746",
      "date": "2026-10-26",
      "subject": "Merge pull request #49 from zhanglunet/trend/prd-184-t1-zh-build-in-public"
    },
    {
      "hash": "18ad9e7",
      "date": "2026-10-26",
      "subject": "Merge pull request #48 from zhanglunet/trend/prd-183-t1-zh-role-skill-pack"
    },
    {
      "hash": "80aadb9",
      "date": "2026-10-25",
      "subject": "feat: PRD-184/T3 构建实录首篇发布 + 2 篇草案大纲（Refs zhanglunet/trend#922）"
    },
    {
      "hash": "ea09499",
      "date": "2026-10-25",
      "subject": "feat: PRD-183/T3 角色包发行门——质量门未过不可发行（Refs zhanglunet/trend#917）"
    },
    {
      "hash": "c831a55",
      "date": "2026-10-25",
      "subject": "feat: PRD-184/T2 构建实录首更模板与栏目索引骨架（Refs zhanglunet/trend#921）"
    },
    {
      "hash": "bdf907b",
      "date": "2026-10-25",
      "subject": "feat: PRD-183/T2 中文销售/法务/人力三包最小集（Refs zhanglunet/trend#916）"
    },
    {
      "hash": "aaccd1d",
      "date": "2026-10-25",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "3f83eba",
      "date": "2026-10-25",
      "subject": "Merge pull request #47 from zhanglunet/trend/prd-155-t5-dsh-context-zh-panel"
    }
  ],
  "weeklyCommits": [
    {
      "hash": "6b00b3a",
      "date": "2026-10-26",
      "subject": "Merge pull request #53 from zhanglunet/trend/prd-184-t3-build-in-public-template"
    },
    {
      "hash": "d2abaf7",
      "date": "2026-10-26",
      "subject": "Merge pull request #52 from zhanglunet/trend/prd-183-t3-zh-role-packs"
    },
    {
      "hash": "32da465",
      "date": "2026-10-26",
      "subject": "Merge pull request #51 from zhanglunet/trend/prd-184-t2-build-in-public-template"
    },
    {
      "hash": "d40bf1f",
      "date": "2026-10-26",
      "subject": "Merge pull request #50 from zhanglunet/trend/prd-183-t2-zh-role-packs"
    },
    {
      "hash": "d371746",
      "date": "2026-10-26",
      "subject": "Merge pull request #49 from zhanglunet/trend/prd-184-t1-zh-build-in-public"
    },
    {
      "hash": "18ad9e7",
      "date": "2026-10-26",
      "subject": "Merge pull request #48 from zhanglunet/trend/prd-183-t1-zh-role-skill-pack"
    },
    {
      "hash": "80aadb9",
      "date": "2026-10-25",
      "subject": "feat: PRD-184/T3 构建实录首篇发布 + 2 篇草案大纲（Refs zhanglunet/trend#922）"
    },
    {
      "hash": "ea09499",
      "date": "2026-10-25",
      "subject": "feat: PRD-183/T3 角色包发行门——质量门未过不可发行（Refs zhanglunet/trend#917）"
    },
    {
      "hash": "c831a55",
      "date": "2026-10-25",
      "subject": "feat: PRD-184/T2 构建实录首更模板与栏目索引骨架（Refs zhanglunet/trend#921）"
    },
    {
      "hash": "bdf907b",
      "date": "2026-10-25",
      "subject": "feat: PRD-183/T2 中文销售/法务/人力三包最小集（Refs zhanglunet/trend#916）"
    },
    {
      "hash": "aaccd1d",
      "date": "2026-10-25",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "3f83eba",
      "date": "2026-10-25",
      "subject": "Merge pull request #47 from zhanglunet/trend/prd-155-t5-dsh-context-zh-panel"
    },
    {
      "hash": "560b526",
      "date": "2026-10-25",
      "subject": "docs: PRD-184/T1 栏目信息架构与更新节奏"
    },
    {
      "hash": "fa5aa8f",
      "date": "2026-10-25",
      "subject": "docs: PRD-183/T1 中文角色包规范与术语表"
    },
    {
      "hash": "b7c94bc",
      "date": "2026-10-25",
      "subject": "test: PRD-155/T5 收尾复核——全量回归复跑入档（flaky 用例判定，Refs #779）"
    },
    {
      "hash": "a2836cb",
      "date": "2026-10-25",
      "subject": "test: PRD-155/T5 面板开箱验收——走查记录+验收测试+真实截图+文档收尾（Refs #779）"
    },
    {
      "hash": "376bd42",
      "date": "2026-10-24",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "cee346b",
      "date": "2026-10-24",
      "subject": "Merge pull request #46 from zhanglunet/trend/prd-155-t4-dsh-context-zh-panel"
    },
    {
      "hash": "d9e6731",
      "date": "2026-10-24",
      "subject": "Merge pull request #44 from zhanglunet/trend/prd-155-t3-dsh-context-zh-panel"
    },
    {
      "hash": "546297f",
      "date": "2026-10-24",
      "subject": "Merge pull request #43 from zhanglunet/trend/prd-155-t2-dsh-context-zh-panel"
    },
    {
      "hash": "c046465",
      "date": "2026-10-24",
      "subject": "Merge pull request #42 from zhanglunet/trend/prd-155-t1-dsh-context-zh-panel"
    },
    {
      "hash": "ab0b985",
      "date": "2026-10-24",
      "subject": "docs: PRD-155/T4 开箱文档——README §9 + 使用指南 + 截图占位（Refs #778）"
    },
    {
      "hash": "cc1c28f",
      "date": "2026-10-24",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "64cfee9",
      "date": "2026-10-24",
      "subject": "docs: 记录汉化版定位、目标与愿景 (#45)"
    },
    {
      "hash": "4b550ac",
      "date": "2026-10-24",
      "subject": "feat: PRD-155/T3 调用演进时间线（页签②点亮）"
    },
    {
      "hash": "4ecc6fc",
      "date": "2026-10-24",
      "subject": "feat: PRD-155/T2 能力组成视图（演示数据）"
    },
    {
      "hash": "d64f866",
      "date": "2026-10-23",
      "subject": "docs: PRD-155/T1 中文面板信息架构与文案表"
    },
    {
      "hash": "d7c8bbc",
      "date": "2026-10-20",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "af20945",
      "date": "2026-10-20",
      "subject": "Merge PR #37: PRD-102/T3 README 双语示范改造"
    },
    {
      "hash": "a3c4b6f",
      "date": "2026-10-20",
      "subject": "docs: PRD-102/T3 新增英文 README（同结构浓缩版，英文技术描述）"
    },
    {
      "hash": "7f33922",
      "date": "2026-10-20",
      "subject": "docs: PRD-102/T3 README 顶部五层双语改造（语言切换 + slogan + 数字副标语）"
    },
    {
      "hash": "8b85bbb",
      "date": "2026-10-19",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "4f0c32a",
      "date": "2026-10-19",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "840408c",
      "date": "2026-10-19",
      "subject": "Merge pull request #32 from zhanglunet/trend/fix-084-f1-fence-check"
    },
    {
      "hash": "7810b75",
      "date": "2026-10-19",
      "subject": "chore: 更新上游哨兵水位（PRD-068）"
    },
    {
      "hash": "023b53a",
      "date": "2026-10-19",
      "subject": "fix: self_check_terms fence 感知（F1）"
    },
    {
      "hash": "981513f",
      "date": "2026-10-19",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "fd32b32",
      "date": "2026-10-19",
      "subject": "Merge pull request #31 from zhanglunet/trend/prd-084-t5-trial"
    },
    {
      "hash": "d5b5958",
      "date": "2026-10-19",
      "subject": "docs: PRD-084/T5 翻译流水线试运行报告"
    },
    {
      "hash": "48282a4",
      "date": "2026-10-19",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "283ff71",
      "date": "2026-10-19",
      "subject": "Merge pull request #30 from zhanglunet/trend/prd-084-t4-trigger"
    },
    {
      "hash": "c365bd7",
      "date": "2026-10-19",
      "subject": "Merge pull request #29 from zhanglunet/trend/prd-084-t3-ci"
    },
    {
      "hash": "167b4ee",
      "date": "2026-10-19",
      "subject": "[PRD-084/T4] 与哨兵联动：一键触发翻译"
    },
    {
      "hash": "d0a630b",
      "date": "2026-10-19",
      "subject": "[PRD-084/T3] CI 校验：术语锁定 + 链接检查"
    },
    {
      "hash": "dd40a95",
      "date": "2026-10-19",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "e441847",
      "date": "2026-10-19",
      "subject": "Merge pull request #28 from zhanglunet/trend/prd-084-t2-pipeline"
    },
    {
      "hash": "2751874",
      "date": "2026-10-19",
      "subject": "feat: PRD-084/T2 翻译流水线实现"
    },
    {
      "hash": "41b7462",
      "date": "2026-10-19",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "9e17262",
      "date": "2026-10-19",
      "subject": "Merge pull request #27 from zhanglunet/trend/prd-084-t1-design"
    }
  ]
} as const;
