export const repoReport = {
  "generatedAt": "2026-11-01T02:22:09+09:00",
  "branch": "main",
  "head": "5140b3215c63ed2dadc32c9ab576680f0ac3978e",
  "shortHead": "5140b32",
  "totalFiles": 717,
  "byExt": [
    {
      "name": "py",
      "count": 307
    },
    {
      "name": "ts",
      "count": 105
    },
    {
      "name": "md",
      "count": 87
    },
    {
      "name": "tsx",
      "count": 79
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
      "count": 6
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
      "name": "tests",
      "count": 137
    },
    {
      "name": "coworker",
      "count": 134
    },
    {
      "name": "docs",
      "count": 111
    },
    {
      "name": "website",
      "count": 36
    },
    {
      "name": "scripts",
      "count": 16
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
      "hash": "5140b32",
      "date": "2026-11-01",
      "subject": "Merge pull request #84 from zhanglunet/trend/prd-212-t5-acceptance"
    },
    {
      "hash": "97db0dc",
      "date": "2026-10-31",
      "subject": "test: PRD-212/T5 验收试运行——多工具环境记录完整（四工具 fixture/全量状态表/probe CSV/修复指引可达，3 例）（trend #1064）"
    },
    {
      "hash": "c3ba05a",
      "date": "2026-10-31",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "a6ac61a",
      "date": "2026-11-01",
      "subject": "Merge pull request #82 from zhanglunet/trend/prd-211-t4-crosslink"
    },
    {
      "hash": "2950a26",
      "date": "2026-10-31",
      "subject": "feat: PRD-211/T4 与 PRD-121 开箱叙事互链（叙事页与手册页双向可达/链接不悬空/术语预检零失败，4 例）（trend #1058）"
    },
    {
      "hash": "cc33ad8",
      "date": "2026-10-31",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "d920ddc",
      "date": "2026-11-01",
      "subject": "Merge pull request #83 from zhanglunet/trend/prd-212-t4-remediation-guide"
    },
    {
      "hash": "d699329",
      "date": "2026-10-31",
      "subject": "feat: PRD-212/T4 漂移修复指引（CN-SYNC-01~12 全编号覆盖/状态枚举对齐 T2/诊断命令引真实脚本/术语预检零失败，4 例）（trend #1063）"
    },
    {
      "hash": "8035b12",
      "date": "2026-10-31",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "a4132cf",
      "date": "2026-10-31",
      "subject": "Merge pull request #81 from zhanglunet/trend/prd-212-t3-probe"
    },
    {
      "hash": "ad404a1",
      "date": "2026-10-31",
      "subject": "Merge pull request #80 from zhanglunet/trend/prd-211-t3-templates"
    },
    {
      "hash": "f5136c4",
      "date": "2026-10-31",
      "subject": "feat: PRD-212/T3 中文触发词可用性抽查（14 条样本集/注入式唤起/三层通过标准/probe CSV 记录完整可回溯，8 例）（trend #1062）"
    }
  ],
  "weeklyCommits": [
    {
      "hash": "5140b32",
      "date": "2026-11-01",
      "subject": "Merge pull request #84 from zhanglunet/trend/prd-212-t5-acceptance"
    },
    {
      "hash": "97db0dc",
      "date": "2026-10-31",
      "subject": "test: PRD-212/T5 验收试运行——多工具环境记录完整（四工具 fixture/全量状态表/probe CSV/修复指引可达，3 例）（trend #1064）"
    },
    {
      "hash": "c3ba05a",
      "date": "2026-10-31",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "a6ac61a",
      "date": "2026-11-01",
      "subject": "Merge pull request #82 from zhanglunet/trend/prd-211-t4-crosslink"
    },
    {
      "hash": "2950a26",
      "date": "2026-10-31",
      "subject": "feat: PRD-211/T4 与 PRD-121 开箱叙事互链（叙事页与手册页双向可达/链接不悬空/术语预检零失败，4 例）（trend #1058）"
    },
    {
      "hash": "cc33ad8",
      "date": "2026-10-31",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "d920ddc",
      "date": "2026-11-01",
      "subject": "Merge pull request #83 from zhanglunet/trend/prd-212-t4-remediation-guide"
    },
    {
      "hash": "d699329",
      "date": "2026-10-31",
      "subject": "feat: PRD-212/T4 漂移修复指引（CN-SYNC-01~12 全编号覆盖/状态枚举对齐 T2/诊断命令引真实脚本/术语预检零失败，4 例）（trend #1063）"
    },
    {
      "hash": "8035b12",
      "date": "2026-10-31",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "a4132cf",
      "date": "2026-10-31",
      "subject": "Merge pull request #81 from zhanglunet/trend/prd-212-t3-probe"
    },
    {
      "hash": "ad404a1",
      "date": "2026-10-31",
      "subject": "Merge pull request #80 from zhanglunet/trend/prd-211-t3-templates"
    },
    {
      "hash": "f5136c4",
      "date": "2026-10-31",
      "subject": "feat: PRD-212/T3 中文触发词可用性抽查（14 条样本集/注入式唤起/三层通过标准/probe CSV 记录完整可回溯，8 例）（trend #1062）"
    },
    {
      "hash": "8e57f36",
      "date": "2026-10-31",
      "subject": "feat: PRD-211/T3 中文模板库（配置/首任务/角色包/会话续跑/纠正反馈五类，TOML 实测解析+键名对齐仓库样例+占位符规范+零密钥形态，6 例）（trend #1057）"
    },
    {
      "hash": "891d4f4",
      "date": "2026-10-31",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "fedc5ab",
      "date": "2026-10-31",
      "subject": "Merge pull request #79 from zhanglunet/trend/prd-212-t2-sync-checklist"
    },
    {
      "hash": "af87a22",
      "date": "2026-10-31",
      "subject": "feat: PRD-212/T2 中文技能包跨工具同步检查脚本（CN-SYNC-01~09，只读）（trend #1061）"
    },
    {
      "hash": "4ddc3b6",
      "date": "2026-10-31",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "d2a505b",
      "date": "2026-10-31",
      "subject": "Merge pull request #78 from zhanglunet/trend/prd-211-t2-howto"
    },
    {
      "hash": "f3d7769",
      "date": "2026-10-31",
      "subject": "fix: PRD-211/T2 场景表命令改写避免术语混排 + 修复 upstream-weekly $date 全角邻接隐患"
    },
    {
      "hash": "4769544",
      "date": "2026-10-31",
      "subject": "docs: PRD-211/T2 中文图解上手指南（安装→首任务→场景→下一步）"
    },
    {
      "hash": "c0c686a",
      "date": "2026-10-31",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "438fb3a",
      "date": "2026-10-31",
      "subject": "Merge pull request #38 from zhanglunet/cursor/prd-121-t1-install-e933"
    },
    {
      "hash": "99e7afd",
      "date": "2026-10-31",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "7ecfb4f",
      "date": "2026-10-31",
      "subject": "Merge pull request #71 from zhanglunet/trend/prd-267-t5-acceptance"
    },
    {
      "hash": "eca50e8",
      "date": "2026-10-31",
      "subject": "Merge pull request #72 from zhanglunet/trend/prd-268-t5-acceptance"
    },
    {
      "hash": "df5e9eb",
      "date": "2026-10-31",
      "subject": "Merge pull request #77 from zhanglunet/trend/prd-285-t5-acceptance"
    },
    {
      "hash": "556d861",
      "date": "2026-10-31",
      "subject": "Merge pull request #69 from zhanglunet/trend/prd-267-t4-intake-gate"
    },
    {
      "hash": "24c5dd0",
      "date": "2026-10-31",
      "subject": "Merge pull request #70 from zhanglunet/trend/prd-268-t4-boundary-doc"
    },
    {
      "hash": "acb0c29",
      "date": "2026-10-31",
      "subject": "Merge pull request #76 from zhanglunet/trend/prd-285-t4-local-only-assertions"
    },
    {
      "hash": "7b6fad2",
      "date": "2026-10-31",
      "subject": "Merge pull request #67 from zhanglunet/trend/prd-267-t3-zh-skills"
    },
    {
      "hash": "cb28c89",
      "date": "2026-10-31",
      "subject": "Merge pull request #68 from zhanglunet/trend/prd-268-t3-zh-sources"
    },
    {
      "hash": "96be411",
      "date": "2026-10-31",
      "subject": "Merge pull request #75 from zhanglunet/trend/prd-285-t3-spotcheck-archive"
    },
    {
      "hash": "356c9a9",
      "date": "2026-10-31",
      "subject": "Merge pull request #65 from zhanglunet/trend/prd-267-t2-zh-skills"
    },
    {
      "hash": "0f7da6b",
      "date": "2026-10-31",
      "subject": "Merge pull request #66 from zhanglunet/trend/prd-268-t2-zh-sources"
    },
    {
      "hash": "79374ca",
      "date": "2026-10-31",
      "subject": "Merge pull request #74 from zhanglunet/trend/prd-285-t2-skillpack-snapshot"
    },
    {
      "hash": "05398fd",
      "date": "2026-10-31",
      "subject": "Merge pull request #39 from zhanglunet/docs/prd-122-t1-readme-en"
    },
    {
      "hash": "6f7a746",
      "date": "2026-10-31",
      "subject": "Merge pull request #57 from zhanglunet/trend/prd-211-t1-howto-design"
    },
    {
      "hash": "e7352d1",
      "date": "2026-10-31",
      "subject": "Merge pull request #58 from zhanglunet/trend/prd-239-t1-layering-design"
    },
    {
      "hash": "1d77b7f",
      "date": "2026-10-31",
      "subject": "Merge pull request #59 from zhanglunet/trend/prd-212-t1-pi"
    },
    {
      "hash": "2fbbef6",
      "date": "2026-10-31",
      "subject": "Merge pull request #60 from zhanglunet/trend/prd-240-t1-pi"
    },
    {
      "hash": "31d2e42",
      "date": "2026-10-31",
      "subject": "Merge pull request #63 from zhanglunet/trend/prd-267-t1-zh-skills"
    },
    {
      "hash": "44937c6",
      "date": "2026-10-31",
      "subject": "Merge pull request #64 from zhanglunet/trend/prd-268-t1-zh-sources"
    },
    {
      "hash": "d3a89fe",
      "date": "2026-10-31",
      "subject": "Merge pull request #73 from zhanglunet/trend/prd-285-t1-skillpack-upgrade-snapshot"
    },
    {
      "hash": "60d0825",
      "date": "2026-10-30",
      "subject": "test: PRD-285/T5 中文技能包升级快照验收试运行（全流程演练 snapshot→包面损坏→抽查检出→自动回滚→旧包+抽查落档+指纹校验+本地断言，8 例）（trend #1430）"
    },
    {
      "hash": "4873ff6",
      "date": "2026-10-29",
      "subject": "test: PRD-285/T4 本地处理断言（快照/回滚/抽查全链零网络：AST import 扫描 + 源码网络字面量扫描 + socket/urllib/http.client 封桩运行期三道，6 例）"
    },
    {
      "hash": "2ef3cb9",
      "date": "2026-10-29",
      "subject": "feat: PRD-285/T3 抽查记录落档与升级流程（spotcheck-record-v1 六字段固定·计数一致 fail-close/append-only JSONL 落档+全量读回坏行带行号拒绝/upgrade_flow_with_check 升级→抽查→failed>0 自动回滚（restore_fn 注入式）·回滚可再回滚/确定性同输入同记录同字节/与 T2 松耦合端到端 spot_check+restore/10 例）（trend #1428）"
    },
    {
      "hash": "d55af45",
      "date": "2026-10-29",
      "subject": "feat: PRD-285/T2 中文技能包升级快照最小实现"
    },
    {
      "hash": "1aa0736",
      "date": "2026-10-29",
      "subject": "docs: PRD-285/T1 中文技能包升级快照设计（skillpack-snapshot-v1 schema：包目录+manifest/目录两枚指纹·按指纹承载身份/restore 单槽位上一版·fail-close·可再回滚/spot_check 抽样校验五项·抽查与回滚记录一并落档 audit.jsonl/全链零网络 AST 断言红线/与 PRD-267 划界：267 管来源 285 管升级可逆/T2–T5 拆分与中文虚构演练样本）（trend #1426）"
    },
    {
      "hash": "f0c3a89",
      "date": "2026-10-28",
      "subject": "test: PRD-268/T5 中文公开源验收试运行（12 例：故障时间线 degraded→failed→failover 事件断言/429 throttled 分列/disallowed 停用不参与切换/恢复切回留痕/违规条目拒载 auth≠none·robots≠true·缺 tos/平台预算叠加不超/doctor 英文 JSON+中文文本/零网络 AST 断言/无登录墙绕过代码路径断言/零密钥扫描）（Refs zhanglunet/trend#1344）"
    },
    {
      "hash": "8a63998",
      "date": "2026-10-28",
      "subject": "test: PRD-267/T5 中文技能录制验收试运行（12 例：虚构中文任务回放时间线 say_zh 在场/Z-1 全角手机号阻断/canonical+colloquial>=3 语料溯源/触发演示命中与不命中/未 review 入库拒/冲突复检拒/三条件过收 0.1.0/本地零网络 AST 断言/密钥扫描/确定性）（Refs zhanglunet/trend#1339）"
    },
    {
      "hash": "1062496",
      "date": "2026-10-28",
      "subject": "docs: PRD-268/T4 与 PRD-184/211 边界文档（184 管栏目叙事/268 管来源健康·(source_handle,health_meta) 对接不自建请求/211 素材人工采集审核不变·268 不自动下载图片/ASCII 分层图/边界一句话·占位符纪律，7 例）（trend #1343）"
    },
    {
      "hash": "3a6cd66",
      "date": "2026-10-28",
      "subject": "feat: PRD-267/T4 人 review 入库门（review.state=approved+reviewer/decided_at 齐签硬拒/触发词冲突复检重叠率>0.5/Z-1~Z-2 正文与 frontmatter 复扫/任一失败 admitted=False+原因可读/入库 version 0.1.0 起，9 例）（trend #1338）"
    },
    {
      "hash": "f498485",
      "date": "2026-10-28",
      "subject": "feat: PRD-268/T3 主备切换与审计（failed 自动切备 standby_in_use+zh_source_failover/恢复探测切回 zh_source_restore/disallowed 备源不参与/切换不清零计数/export_events 可序列化，7 例）（trend #1342）"
    },
    {
      "hash": "15fe5e7",
      "date": "2026-10-28",
      "subject": "feat: PRD-267/T3 中文技能草稿与口语化触发词（say_zh 原句截取 8-24 字/colloquial>=3 不足 action_zh 补足/语料不足拒产不编造/冲突检查交集并集>0.5/触发演示 trigger_match，17 例）（trend #1337）"
    },
    {
      "hash": "587e29f",
      "date": "2026-10-28",
      "subject": "feat: PRD-268/T2 中文公开源能力层最小实现（zh-source-v1 robots 必填校验/平台级限流预算/健康四态含 disallowed/doctor 中英分离，13 例）（trend #1341）"
    },
    {
      "hash": "2279e04",
      "date": "2026-10-28",
      "subject": "feat: PRD-267/T2 中文实操录制管线最小实现（zh-capture-v1 含 say_zh 口语字段/Z-1 全半角/Z-3 替换类/值类禁录 FORBIDDEN，12 例）（trend #1336）"
    },
    {
      "hash": "722a9af",
      "date": "2026-10-28",
      "subject": "docs: PRD-268/T1 中文公开源能力层设计（zh-source-v1 平台枚举/平台级限流预算/robots+disallowed 停用语义/184-211 边界）"
    },
    {
      "hash": "b2632af",
      "date": "2026-10-28",
      "subject": "docs: PRD-267/T1 中文实操转中文技能设计（zh-capture-v1 含 say_zh 解说字段/Z 四维全半角脱敏/口语化触发词 canonical+colloquial 双层规范/冲突检查）"
    },
    {
      "hash": "3512df1",
      "date": "2026-10-27",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "209c7f7",
      "date": "2026-10-27",
      "subject": "Merge pull request #62 from zhanglunet/trend/prd-184-t5-acceptance"
    },
    {
      "hash": "efcbdb0",
      "date": "2026-10-27",
      "subject": "Merge pull request #61 from zhanglunet/trend/prd-183-t5-acceptance"
    },
    {
      "hash": "23c5d2e",
      "date": "2026-10-27",
      "subject": "test: PRD-184/T5 构建实录栏目验收——可浏览走查、隐私扫描、术语统一（Refs zhanglunet/trend#924）"
    },
    {
      "hash": "d819ec9",
      "date": "2026-10-27",
      "subject": "test: PRD-183/T5 三包验收——演示走查、质量门报告齐全、无密钥（Refs zhanglunet/trend#919）"
    },
    {
      "hash": "3788cb3",
      "date": "2026-10-27",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "78340c1",
      "date": "2026-10-27",
      "subject": "Merge pull request #55 from zhanglunet/trend/prd-184-t4-bilingual-links"
    },
    {
      "hash": "2426aa7",
      "date": "2026-10-27",
      "subject": "Merge pull request #54 from zhanglunet/trend/prd-183-t4-release-gate-ci"
    },
    {
      "hash": "57a7ed3",
      "date": "2026-10-26",
      "subject": "docs: PRD-240/T1 中文结构化知识引擎"
    },
    {
      "hash": "500e039",
      "date": "2026-10-26",
      "subject": "docs: PRD-212/T1 中文 skill 跨工具同步清单"
    },
    {
      "hash": "278f3ea",
      "date": "2026-10-26",
      "subject": "docs: PRD-239/T1 中文角色包盘点与分场景映射设计"
    },
    {
      "hash": "889a6c7",
      "date": "2026-10-26",
      "subject": "docs: PRD-211/T1 图解上手指南信息架构与图解规范（设计草稿）"
    },
    {
      "hash": "8f079f8",
      "date": "2026-10-26",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "58323a7",
      "date": "2026-10-26",
      "subject": "chore: 更新上游哨兵水位（PRD-068）"
    },
    {
      "hash": "71dace6",
      "date": "2026-10-26",
      "subject": "docs: PRD-184/T4 双语传播交叉链接——中英入口在本目录汇合（Refs #923）"
    },
    {
      "hash": "8af13b1",
      "date": "2026-10-26",
      "subject": "docs: PRD-183/T4 角色包开箱指南（对接 PRD-121，10 分钟跟做）（Refs #918）"
    },
    {
      "hash": "5d40e59",
      "date": "2026-10-26",
      "subject": "docs: refresh generated site reports"
    },
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
    }
  ]
} as const;
