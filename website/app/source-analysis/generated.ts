export const repoReport = {
  "generatedAt": "2026-10-20T15:38:39+08:00",
  "branch": "main",
  "head": "af2094519ae5d7e3a4090b7a66fb155ae67686cc",
  "shortHead": "af20945",
  "totalFiles": 634,
  "byExt": [
    {
      "name": "py",
      "count": 269
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
      "count": 49
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
      "count": 19
    },
    {
      "name": "yml",
      "count": 15
    },
    {
      "name": "[none]",
      "count": 7
    },
    {
      "name": "html",
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
      "count": 108
    },
    {
      "name": "docs",
      "count": 80
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
      "name": "packaging",
      "count": 10
    },
    {
      "name": "scripts",
      "count": 6
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
    }
  ],
  "weeklyCommits": [
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
    },
    {
      "hash": "612253d",
      "date": "2026-10-19",
      "subject": "docs: PRD-084/T1 翻译流水线设计稿"
    },
    {
      "hash": "51cd463",
      "date": "2026-10-18",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "904c8df",
      "date": "2026-10-19",
      "subject": "Merge pull request #26 from zhanglunet/trend/prd-068-t5-trial"
    },
    {
      "hash": "e6241fa",
      "date": "2026-10-18",
      "subject": "docs: PRD-068/T5 上游周报试运行报告"
    },
    {
      "hash": "e56cb47",
      "date": "2026-10-18",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "abfcae7",
      "date": "2026-10-18",
      "subject": "Merge pull request #25 from zhanglunet/trend/prd-067-t5-trial"
    },
    {
      "hash": "ef61d3f",
      "date": "2026-10-18",
      "subject": "Merge pull request #24 from zhanglunet/trend/prd-068-t4-cron"
    },
    {
      "hash": "2e3d4f0",
      "date": "2026-10-18",
      "subject": "docs: PRD-067/T5 质量门试运行报告"
    },
    {
      "hash": "6cca6b1",
      "date": "2026-10-18",
      "subject": "ci: PRD-068/T4 上游周报 cron 调度"
    },
    {
      "hash": "733191d",
      "date": "2026-10-18",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "11156f7",
      "date": "2026-10-18",
      "subject": "Merge pull request #23 from zhanglunet/trend/prd-067-t4-baseline"
    },
    {
      "hash": "01fd065",
      "date": "2026-10-18",
      "subject": "Merge pull request #22 from zhanglunet/trend/prd-068-t3-template"
    },
    {
      "hash": "3f34270",
      "date": "2026-10-18",
      "subject": "Merge pull request #21 from zhanglunet/trend/prd-067-t3-ci"
    },
    {
      "hash": "873480b",
      "date": "2026-10-18",
      "subject": "docs: PRD-067/T4 质量门基线建立（trend #290）"
    },
    {
      "hash": "c8604fc",
      "date": "2026-10-18",
      "subject": "docs: PRD-068/T3 上游周报模板 + 手填示例"
    },
    {
      "hash": "a64f630",
      "date": "2026-10-18",
      "subject": "ci: PRD-067/T3 质量门 CI 集成（术语一致性，失败阻断）"
    },
    {
      "hash": "c8cf75e",
      "date": "2026-10-18",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "e499626",
      "date": "2026-10-18",
      "subject": "Merge pull request #20 from zhanglunet/trend/prd-068-t2-impact"
    },
    {
      "hash": "fac17ef",
      "date": "2026-10-18",
      "subject": "Merge pull request #19 from zhanglunet/trend/prd-067-t2-suite"
    },
    {
      "hash": "aee92d0",
      "date": "2026-10-18",
      "subject": "feat: PRD-068/T2 影响面分析实现（upstream_common 抽取 + weekly 哨兵）"
    },
    {
      "hash": "216f49c",
      "date": "2026-10-18",
      "subject": "feat: PRD-067/T2 测试套件实现（三类检查脚本，纯标准库）"
    },
    {
      "hash": "091fe4f",
      "date": "2026-10-18",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "1b3859b",
      "date": "2026-10-18",
      "subject": "[PRD-067/T1] 质量门测试用例设计（方案 A；术语表已拍板）(#18)"
    },
    {
      "hash": "48c1d20",
      "date": "2026-10-18",
      "subject": "[PRD-068/T1] 监控脚本设计：上游 diff 哨兵方案 (#17)"
    },
    {
      "hash": "d18f7aa",
      "date": "2026-10-18",
      "subject": "docs: 记录用户拍板结论（方案 A；术语表 25 条已认可）"
    },
    {
      "hash": "7cd5b13",
      "date": "2026-10-18",
      "subject": "docs: PRD-067/T1 质量门测试用例设计（现状盘点+三类检查规则+术语表初版）"
    },
    {
      "hash": "8ae8c5e",
      "date": "2026-10-18",
      "subject": "docs: PRD-068/T1 上游 diff 监控脚本设计（哨兵方案）"
    },
    {
      "hash": "2edc2c4",
      "date": "2026-10-17",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "dd3b1cb",
      "date": "2026-10-17",
      "subject": "feat: PRD-029/T5 增强①②（additions 透出 + 测试文件排除）(#15)"
    },
    {
      "hash": "7630087",
      "date": "2026-10-17",
      "subject": "feat: T5 复盘建议①②（classify 透出 additions/deletions；敏感区排除测试文件）"
    },
    {
      "hash": "cf1d84e",
      "date": "2026-10-17",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "9d2cbf8",
      "date": "2026-10-17",
      "subject": "docs: PRD-030/T5 定稿与换肤走查 (#14)"
    },
    {
      "hash": "dc56fa7",
      "date": "2026-10-17",
      "subject": "docs: PRD-029/T5 试运行复盘 (#13)"
    },
    {
      "hash": "fe012b1",
      "date": "2026-10-17",
      "subject": "docs: PRD-029/T4 冲突分级 (#12)"
    },
    {
      "hash": "7446e58",
      "date": "2026-10-17",
      "subject": "fix: 评审修订（回退演练改为下次试运行，T5 已跑完）"
    },
    {
      "hash": "2ceba58",
      "date": "2026-10-17",
      "subject": "docs: PRD-030/T5 定稿与换肤走查（回指写回 + Acme 桌面推演 + 3 处修订）"
    },
    {
      "hash": "2977a54",
      "date": "2026-10-17",
      "subject": "docs: PRD-029/T5 试运行复盘报告"
    },
    {
      "hash": "1a30d0a",
      "date": "2026-10-17",
      "subject": "docs: PRD-029/T4 冲突分级、处理与回退"
    },
    {
      "hash": "af681ab",
      "date": "2026-10-17",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "0cdb8bd",
      "date": "2026-10-17",
      "subject": "docs: PRD-030/T4 部署章节正文 (#10)"
    },
    {
      "hash": "a0da1b6",
      "date": "2026-10-17",
      "subject": "docs: PRD-030/T3 三仓同步章节正文 (#8)"
    },
    {
      "hash": "6868257",
      "date": "2026-10-17",
      "subject": "docs: PRD-030/T2 换肤打包章节正文 (#9)"
    },
    {
      "hash": "be43494",
      "date": "2026-10-17",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "b8c055b",
      "date": "2026-10-17",
      "subject": "docs: PRD-029/T3 汉化 diff 报告模板 (#11)"
    },
    {
      "hash": "87358ba",
      "date": "2026-10-17",
      "subject": "fix: 评审修订（对应表版本号注明为 version 非 tag）"
    },
    {
      "hash": "e5aa520",
      "date": "2026-10-17",
      "subject": "fix: 评审修订（macos-15-intel 可用性以 GitHub 公告为准）"
    },
    {
      "hash": "492f514",
      "date": "2026-10-17",
      "subject": "fix: 评审修订（示例 P0 口径、渲染器 additions 判定、模板 P0 来源）"
    },
    {
      "hash": "a3dc967",
      "date": "2026-10-17",
      "subject": "docs: PRD-029/T3 汉化 diff 报告模板（模板说明+渲染器+真实示例）"
    },
    {
      "hash": "f602080",
      "date": "2026-10-17",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "2af441a",
      "date": "2026-10-17",
      "subject": "docs: PRD-029/T2 上游变更检测方案 (#7)"
    },
    {
      "hash": "c96e33e",
      "date": "2026-10-17",
      "subject": "fix: 评审修订（L2 无基线 guard 对齐 fail-quiet；releases 过滤 draft）"
    },
    {
      "hash": "0c7d5dd",
      "date": "2026-10-17",
      "subject": "docs: PRD-030/T4 部署章节正文"
    },
    {
      "hash": "0c23a90",
      "date": "2026-10-17",
      "subject": "docs: PRD-030/T2 换肤打包章节正文"
    },
    {
      "hash": "1fba9a3",
      "date": "2026-10-17",
      "subject": "docs: PRD-030/T3 三仓同步章节正文"
    },
    {
      "hash": "5c4eb16",
      "date": "2026-10-17",
      "subject": "docs: PRD-029/T2 上游变更检测方案（设计稿+检测脚本草稿）"
    },
    {
      "hash": "86dbfe8",
      "date": "2026-10-17",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "8628a7e",
      "date": "2026-10-17",
      "subject": "docs: PRD-030/T1 企业定制版 playbook 大纲 (#6)"
    },
    {
      "hash": "2c46738",
      "date": "2026-10-17",
      "subject": "docs: 填实 PRD-030/T1 playbook 章节↔docs/enterprise/ 文件对应关系"
    },
    {
      "hash": "cf7aabe",
      "date": "2026-10-17",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "b0e4242",
      "date": "2026-10-17",
      "subject": "docs: PRD-029/T1 上游同步策略 (#5)"
    },
    {
      "hash": "89dba93",
      "date": "2026-10-17",
      "subject": "docs: 修订 PRD-029/T1 上游同步策略（P0 告警归属/双周标题/L2 停更降级）"
    },
    {
      "hash": "dff313e",
      "date": "2026-10-17",
      "subject": "docs: PRD-030/T1 企业定制版 playbook 大纲"
    },
    {
      "hash": "4cb7064",
      "date": "2026-10-17",
      "subject": "docs: PRD-029/T1 上游同步策略"
    }
  ]
} as const;
