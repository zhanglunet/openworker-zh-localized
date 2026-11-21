export const repoReport = {
  "generatedAt": "2026-11-21T09:15:11+09:00",
  "branch": "main",
  "head": "f60fb1e3c53fec9d01a9e3e8e0d61c278ce4ed76",
  "shortHead": "f60fb1e3",
  "totalFiles": 3008,
  "byExt": [
    {
      "name": "py",
      "count": 769
    },
    {
      "name": "rs",
      "count": 436
    },
    {
      "name": "json",
      "count": 313
    },
    {
      "name": "md",
      "count": 308
    },
    {
      "name": "mjs",
      "count": 273
    },
    {
      "name": "ts",
      "count": 254
    },
    {
      "name": "tsx",
      "count": 196
    },
    {
      "name": "png",
      "count": 52
    },
    {
      "name": "svg",
      "count": 51
    },
    {
      "name": "[none]",
      "count": 40
    },
    {
      "name": "js",
      "count": 38
    },
    {
      "name": "jsonl",
      "count": 37
    },
    {
      "name": "yaml",
      "count": 33
    },
    {
      "name": "css",
      "count": 27
    },
    {
      "name": "toml",
      "count": 25
    },
    {
      "name": "html",
      "count": 24
    },
    {
      "name": "yml",
      "count": 20
    },
    {
      "name": "sh",
      "count": 16
    }
  ],
  "byTopDir": [
    {
      "name": "harness",
      "count": 920
    },
    {
      "name": "tests",
      "count": 654
    },
    {
      "name": "surfaces",
      "count": 466
    },
    {
      "name": "coworker",
      "count": 309
    },
    {
      "name": "docs",
      "count": 252
    },
    {
      "name": "deploy",
      "count": 160
    },
    {
      "name": "scripts",
      "count": 61
    },
    {
      "name": "docs-site",
      "count": 42
    },
    {
      "name": "website",
      "count": 36
    },
    {
      "name": "skills",
      "count": 31
    },
    {
      "name": "packaging",
      "count": 17
    },
    {
      "name": ".github",
      "count": 16
    },
    {
      "name": "role-packs",
      "count": 11
    },
    {
      "name": "ui-mocks",
      "count": 6
    },
    {
      "name": "skill-eval",
      "count": 4
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
      "name": ".claude",
      "count": 1
    },
    {
      "name": ".dockerignore",
      "count": 1
    },
    {
      "name": ".gitattributes",
      "count": 1
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
      "name": "CONTRIBUTING.md",
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
      "name": "openworker-zh.default.json",
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
      "name": "SECURITY.md",
      "count": 1
    },
    {
      "name": "start-openworker-gui.sh",
      "count": 1
    },
    {
      "name": "start-openworker-server.sh",
      "count": 1
    },
    {
      "name": "uv.lock",
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
      "hash": "f60fb1e3",
      "date": "2026-11-21",
      "subject": "[PRD-581/T4] 巡检划界断言（trend #2918） (#192)"
    },
    {
      "hash": "0810f3d8",
      "date": "2026-11-21",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "7c586dd3",
      "date": "2026-11-21",
      "subject": "[PRD-581/T3] 巡检校验闸门（trend #2917） (#191)"
    },
    {
      "hash": "fa40582f",
      "date": "2026-11-21",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "52d977e4",
      "date": "2026-11-21",
      "subject": "[PRD-581/T2] 巡检台最小实现（trend #2916） (#190)"
    },
    {
      "hash": "ff256313",
      "date": "2026-11-21",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "4e43343d",
      "date": "2026-11-21",
      "subject": "[PRD-581/T1] 中文产物红队巡检设计草稿（trend #2915） (#189)"
    },
    {
      "hash": "117286d7",
      "date": "2026-11-20",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "37f4bc05",
      "date": "2026-11-21",
      "subject": "fix: 链复跑放行 rc=5（unittest 空跑=pytest 原生文件） (#188)"
    },
    {
      "hash": "e7253da7",
      "date": "2026-11-20",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "67675343",
      "date": "2026-11-21",
      "subject": "fix: 单引号 pytest 复跑 unittest 化 (#187)"
    },
    {
      "hash": "3ae25399",
      "date": "2026-11-20",
      "subject": "docs: refresh generated site reports"
    }
  ],
  "weeklyCommits": [
    {
      "hash": "f60fb1e3",
      "date": "2026-11-21",
      "subject": "[PRD-581/T4] 巡检划界断言（trend #2918） (#192)"
    },
    {
      "hash": "0810f3d8",
      "date": "2026-11-21",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "7c586dd3",
      "date": "2026-11-21",
      "subject": "[PRD-581/T3] 巡检校验闸门（trend #2917） (#191)"
    },
    {
      "hash": "fa40582f",
      "date": "2026-11-21",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "52d977e4",
      "date": "2026-11-21",
      "subject": "[PRD-581/T2] 巡检台最小实现（trend #2916） (#190)"
    },
    {
      "hash": "ff256313",
      "date": "2026-11-21",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "4e43343d",
      "date": "2026-11-21",
      "subject": "[PRD-581/T1] 中文产物红队巡检设计草稿（trend #2915） (#189)"
    },
    {
      "hash": "117286d7",
      "date": "2026-11-20",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "37f4bc05",
      "date": "2026-11-21",
      "subject": "fix: 链复跑放行 rc=5（unittest 空跑=pytest 原生文件） (#188)"
    },
    {
      "hash": "e7253da7",
      "date": "2026-11-20",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "67675343",
      "date": "2026-11-21",
      "subject": "fix: 单引号 pytest 复跑 unittest 化 (#187)"
    },
    {
      "hash": "3ae25399",
      "date": "2026-11-20",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "695dd27f",
      "date": "2026-11-21",
      "subject": "fix: 复跑块括号修复（] 替代误写的 )） (#186)"
    },
    {
      "hash": "2471523d",
      "date": "2026-11-20",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "fd86ead0",
      "date": "2026-11-21",
      "subject": "fix: 剩余 pytest 复跑（TESTS 变量多行形态）unittest 化 (#185)"
    },
    {
      "hash": "95d0ee23",
      "date": "2026-11-20",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "d2155be0",
      "date": "2026-11-21",
      "subject": "fix: SCRIPTS-form rerun to unittest discover (#184)"
    },
    {
      "hash": "947b4c6e",
      "date": "2026-11-20",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "496311d4",
      "date": "2026-11-21",
      "subject": "fix: 老链 T5 复跑 pytest→unittest discover（CI 裸 python 无 pytest） (#182)"
    },
    {
      "hash": "f8c75e01",
      "date": "2026-11-20",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "6171c17f",
      "date": "2026-11-20",
      "subject": "fix: 准入批遗留测试路径修正（MODULE_DIR/复跑/doc glob） (#180)"
    },
    {
      "hash": "b9510cd6",
      "date": "2026-11-19",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "15b2fe17",
      "date": "2026-11-20",
      "subject": "test(prd-558): T5 验收试运行 (#178)"
    },
    {
      "hash": "1e576757",
      "date": "2026-11-20",
      "subject": "test(prd-558): T4 划界断言 (#177)"
    },
    {
      "hash": "60cc1a59",
      "date": "2026-11-20",
      "subject": "feat(prd-558): T3 准入检查校验闸门 (#176)"
    },
    {
      "hash": "90c41586",
      "date": "2026-11-20",
      "subject": "feat(prd-558): T2 准入检查最小实现 (#175)"
    },
    {
      "hash": "9a39345b",
      "date": "2026-11-20",
      "subject": "docs(prd-558): T1 准入检查设计草稿 (#174)"
    },
    {
      "hash": "06e2e5fa",
      "date": "2026-11-18",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "1f432ce2",
      "date": "2026-11-19",
      "subject": "[PRD-535/T5] openworker-zh-localized 中文 skill 方法论包验收试运行（真实任务走包） (#172)"
    },
    {
      "hash": "38145113",
      "date": "2026-11-19",
      "subject": "[PRD-535/T4] openworker-zh-localized 中文 skill 方法论包划界断言（无方法论包不成套） (#171)"
    },
    {
      "hash": "807c67d5",
      "date": "2026-11-19",
      "subject": "[PRD-535/T3] openworker-zh-localized 中文 skill 方法论包方法论包校验闸门 (#170)"
    },
    {
      "hash": "cb9156d2",
      "date": "2026-11-19",
      "subject": "[PRD-535/T2] 方法论包落账 (#173)"
    },
    {
      "hash": "ff8bc258",
      "date": "2026-11-19",
      "subject": "docs(prd-535): T1 openworker-zh-localized 中文 skill 方法论包设计——方法论包四件套（workflow/skill 集/命令入口/模式库）+划界表+PR 门槛自查 (#169)"
    },
    {
      "hash": "1b238f32",
      "date": "2026-11-18",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "1797ba10",
      "date": "2026-11-19",
      "subject": "[PRD-488/T5] 技能评估验收试运行（本链收官） (#168)"
    },
    {
      "hash": "11a25f37",
      "date": "2026-11-19",
      "subject": "[PRD-488/T4] 技能评估划界断言 (#167)"
    },
    {
      "hash": "61b53c72",
      "date": "2026-11-19",
      "subject": "[PRD-488/T3] 中文技能评估监督回路闸门 (#166)"
    },
    {
      "hash": "eeede55f",
      "date": "2026-11-19",
      "subject": "feat(prd-488): T2 中文技能包评估最小实现——质量门+重叠检测跑通真实技能包，首份评估报告落账（5 例全绿） (#165)"
    },
    {
      "hash": "bcc78140",
      "date": "2026-11-18",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "9c50e01a",
      "date": "2026-11-18",
      "subject": "[PRD-488/T1] 中文技能评估设计草稿 (#159)"
    },
    {
      "hash": "a132862c",
      "date": "2026-11-17",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "4aa39c92",
      "date": "2026-11-18",
      "subject": "PRD-511/T5：验收试运行（全链两遍逐字节一致+失败演练+链复跑+文档无密钥） (#164)"
    },
    {
      "hash": "9f8cafc1",
      "date": "2026-11-18",
      "subject": "PRD-511/T4：划界断言（下游载体零导入+借鉴仓零符号+红线钉值） (#163)"
    },
    {
      "hash": "dd5e862d",
      "date": "2026-11-18",
      "subject": "PRD-511/T3：契约闸门（LEDGER_DRIFT+一票否决） (#162)"
    },
    {
      "hash": "0c5f8400",
      "date": "2026-11-18",
      "subject": "PRD-511/T2：翻译技能契约内核（五件套注册+调用校验+append-only 账本） (#161)"
    },
    {
      "hash": "2999a860",
      "date": "2026-11-18",
      "subject": "docs(prd-511): T1 翻译技能契约设计——契约五件套 schema/校验流程/四码闸门/划界表+PR 门槛四项自查 (#160)"
    },
    {
      "hash": "7890d943",
      "date": "2026-11-16",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "6b94b0e1",
      "date": "2026-11-17",
      "subject": "Merge pull request #158 from zhanglunet/feat/prd-452-t5-translation-supervision-acceptance"
    },
    {
      "hash": "2f1ed13a",
      "date": "2026-11-17",
      "subject": "Merge pull request #157 from zhanglunet/feat/prd-452-t4-translation-supervision-boundary"
    },
    {
      "hash": "8101f1c8",
      "date": "2026-11-17",
      "subject": "Merge pull request #156 from zhanglunet/feat/prd-452-t3-translation-supervision-gate"
    },
    {
      "hash": "8393c0d8",
      "date": "2026-11-17",
      "subject": "Merge pull request #155 from zhanglunet/feat/prd-452-t2-translation-supervision-bench"
    },
    {
      "hash": "4460f0b4",
      "date": "2026-11-16",
      "subject": "test(prd-452): T5 验收试运行——真实监督回路全链两遍逐字节一致+失败演练+链复跑（9 tests green，本链 35）"
    },
    {
      "hash": "7ff38589",
      "date": "2026-11-16",
      "subject": "test(prd-452): T4 划界断言——收件箱裁决权零触碰+下游零导入+借鉴仓零符号+R1/R3/留痕钉值（8 tests green）"
    },
    {
      "hash": "37e2598f",
      "date": "2026-11-16",
      "subject": "feat(prd-452): T3 监督回路闸门——原始记录重导放行 fail-closed（无裁决/批注挂起/反馈挂起/点头非最新）+收件箱入口过闸（6 tests green）"
    },
    {
      "hash": "20e0d901",
      "date": "2026-11-16",
      "subject": "feat(prd-452): T2 翻译监督台内核——版本链+批注打包发回+回炉批注对照+关口未点头不进收件箱+点头落账（12 tests green）"
    },
    {
      "hash": "6d1a0654",
      "date": "2026-11-16",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "ec4b1511",
      "date": "2026-11-17",
      "subject": "Merge pull request #153 from zhanglunet/docs/prd-452-t1-translation-supervision-bench"
    },
    {
      "hash": "9db06a75",
      "date": "2026-11-16",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "28eafe7f",
      "date": "2026-11-16",
      "subject": "chore: 更新上游哨兵水位（PRD-068）"
    },
    {
      "hash": "29ca000d",
      "date": "2026-11-15",
      "subject": "[PRD-452/T1] 翻译监督台设计草稿"
    },
    {
      "hash": "b72a1196",
      "date": "2026-11-14",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "fd713c85",
      "date": "2026-11-14",
      "subject": "Merge pull request #152 from zhanglunet/fix/sync-fail-loud"
    },
    {
      "hash": "3aeb47bf",
      "date": "2026-11-15",
      "subject": "ci(sync): 拆假绿——合并失败让运行变红"
    },
    {
      "hash": "940d7265",
      "date": "2026-11-14",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "0c929a67",
      "date": "2026-11-14",
      "subject": "Merge upstream OpenWorker ecb44549 (#151)"
    },
    {
      "hash": "8acfb16b",
      "date": "2026-11-14",
      "subject": "Merge remote-tracking branch 'upstream/main' into codex/sync-upstream-20261114"
    },
    {
      "hash": "795dd7df",
      "date": "2026-11-14",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "6efd8341",
      "date": "2026-11-14",
      "subject": "Merge pull request #150 from zhanglunet/trend/prd-429-t5-review-pipeline-acceptance"
    },
    {
      "hash": "b7a34504",
      "date": "2026-11-14",
      "subject": "Merge pull request #149 from zhanglunet/trend/prd-429-t4-review-pipeline-boundary"
    },
    {
      "hash": "57f66799",
      "date": "2026-11-14",
      "subject": "Merge pull request #148 from zhanglunet/trend/prd-429-t3-review-pipeline-gates"
    },
    {
      "hash": "bd7419b5",
      "date": "2026-11-14",
      "subject": "Merge pull request #147 from zhanglunet/trend/prd-429-t2-review-pipeline-impl"
    },
    {
      "hash": "3347e04a",
      "date": "2026-11-14",
      "subject": "Merge pull request #146 from zhanglunet/trend/prd-429-t1-review-pipeline"
    },
    {
      "hash": "7a27cca5",
      "date": "2026-11-14",
      "subject": "test(prd-429): T5 验收试运行——全链两遍逐字节一致+失败演练+链复跑+文档无密钥"
    },
    {
      "hash": "00bfe4c9",
      "date": "2026-11-14",
      "subject": "test(prd-429): T4 划界断言——下游载体零导入+借鉴仓零符号+标准库-only+R1~R4 红线钉值"
    },
    {
      "hash": "22742842",
      "date": "2026-11-14",
      "subject": "feat(prd-429): T3 评审流水线闸门——append_only LEDGER_DRIFT + verdict 双向对账 + coverage 全判齐 + gate_summary 一票否决"
    },
    {
      "hash": "d58c241f",
      "date": "2026-11-14",
      "subject": "feat(prd-429): T2 翻译评审流水线内核——三确定性规则+judge 注入+三件套 JSONL 落账+outlet 出口拦截"
    },
    {
      "hash": "b43517ea",
      "date": "2026-11-14",
      "subject": "docs(prd-429): T1 翻译评审流水线设计——三件套 schema/规则先行模型后判/三码闸门/划界表+PR 门槛四项自查"
    },
    {
      "hash": "ecb44549",
      "date": "2026-11-13",
      "subject": "Merge pull request #898 from andrewyng/docs/desktop-getting-started"
    },
    {
      "hash": "f68159ee",
      "date": "2026-11-13",
      "subject": "Merge pull request #896 from andrewyng/docs/sdk-launch-guides"
    }
  ]
} as const;
