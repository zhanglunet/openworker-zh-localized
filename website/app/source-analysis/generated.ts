export const repoReport = {
  "generatedAt": "2026-11-19T08:10:06+09:00",
  "branch": "main",
  "head": "1f432ce2649755583d60ad032b973ddccdf47673",
  "shortHead": "1f432ce2",
  "totalFiles": 2994,
  "byExt": [
    {
      "name": "py",
      "count": 757
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
      "count": 306
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
      "count": 646
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
      "count": 250
    },
    {
      "name": "deploy",
      "count": 160
    },
    {
      "name": "scripts",
      "count": 57
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
    }
  ],
  "weeklyCommits": [
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
    },
    {
      "hash": "a57aa57f",
      "date": "2026-11-14",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "738a4804",
      "date": "2026-11-14",
      "subject": "Merge pull request #145 from zhanglunet/trend/prd-122-t5-acceptance"
    },
    {
      "hash": "904e0edf",
      "date": "2026-11-14",
      "subject": "Merge pull request #144 from zhanglunet/trend/prd-122-t3-sync-check"
    },
    {
      "hash": "85944fd4",
      "date": "2026-11-14",
      "subject": "Merge pull request #143 from zhanglunet/trend/prd-122-t4-sync-en"
    },
    {
      "hash": "d368a111",
      "date": "2026-11-14",
      "subject": "Merge pull request #142 from zhanglunet/trend/prd-122-t2-crosslink"
    },
    {
      "hash": "7abc79f0",
      "date": "2026-11-14",
      "subject": "Merge pull request #141 from zhanglunet/trend/prd-121-t5-acceptance"
    },
    {
      "hash": "3039932c",
      "date": "2026-11-14",
      "subject": "Merge pull request #140 from zhanglunet/trend/prd-121-t4-readme-demo"
    },
    {
      "hash": "1688a681",
      "date": "2026-11-14",
      "subject": "Merge pull request #139 from zhanglunet/trend/prd-121-t3-clean-ci"
    },
    {
      "hash": "d1df810e",
      "date": "2026-11-14",
      "subject": "Merge pull request #138 from zhanglunet/trend/prd-121-t2-default-zh-config"
    },
    {
      "hash": "ad61ed95",
      "date": "2026-11-13",
      "subject": "Keep the cluster recording instructions in the guide"
    },
    {
      "hash": "c0fcba07",
      "date": "2026-11-13",
      "subject": "test(prd-122): T5 验收——3 节抽查+检查器与全链复跑（4 tests green，本链 15）"
    },
    {
      "hash": "43ad3cb0",
      "date": "2026-11-13",
      "subject": "ci(prd-122): T3 章节同步检查——H2 结构比对脚本+i18n-check job 新步+漂移检出钉值（trend #611，4 tests green）"
    },
    {
      "hash": "957029a8",
      "date": "2026-11-13",
      "subject": "docs(prd-122): T4 英文版同步——补 One-line Install+Bonus 两节+重编号+双 TOC 同步（trend #612，4 tests green）"
    },
    {
      "hash": "ccfd745f",
      "date": "2026-11-13",
      "subject": "test(prd-122): T2 互链钉值——双向顶部链接+语言正确（trend #610，3 tests green；互链 T1 已交付，本单为验收钉值）"
    },
    {
      "hash": "a2f47e6a",
      "date": "2026-11-13",
      "subject": "test(prd-121): T5 验收——干净克隆全链走查+文档命令与脚本旗标一致+10 分钟预算表（3 tests green，本链 17）"
    },
    {
      "hash": "2c6a9c11",
      "date": "2026-11-13",
      "subject": "docs(prd-121): T4 README 首屏一行安装+5 张演示示意图+带图安装指南（trend #607，6 tests green）"
    },
    {
      "hash": "51e52c08",
      "date": "2026-11-14",
      "subject": "ci(prd-121): T3 干净环境 CI——ubuntu:24.04 容器内 self-test+T1/T2 套件+预演零写入（trend #606）"
    },
    {
      "hash": "559f960e",
      "date": "2026-11-13",
      "subject": "feat(prd-121): T2 默认中文配置——install --write-config 写占位配置件(zh-CN/600/幂等)+T1 self-test 可移植性修复(BASH_ABS)（8 tests green）"
    },
    {
      "hash": "c5a04fa4",
      "date": "2026-11-13",
      "subject": "Merge pull request #895 from andrewyng/fix/cluster-installation-release"
    },
    {
      "hash": "60bd6e39",
      "date": "2026-11-13",
      "subject": "Bound the approval snippet compilation to its section"
    },
    {
      "hash": "b3799eed",
      "date": "2026-11-13",
      "subject": "Fix guide example compilation and cancellation race"
    },
    {
      "hash": "cf2c0790",
      "date": "2026-11-13",
      "subject": "Wait for the initial UI session check before sign-in"
    },
    {
      "hash": "f1daf752",
      "date": "2026-11-13",
      "subject": "Merge verified SDK fixes into cluster qualification"
    },
    {
      "hash": "ce3bb66b",
      "date": "2026-11-13",
      "subject": "Merge pull request #897 from andrewyng/fix/service-attachment-admission"
    },
    {
      "hash": "63b21f97",
      "date": "2026-11-13",
      "subject": "Merge pull request #891 from andrewyng/fix/sdk-approval-visibility"
    },
    {
      "hash": "38df9f7e",
      "date": "2026-11-13",
      "subject": "Add Desktop App docs"
    },
    {
      "hash": "4a34f789",
      "date": "2026-11-13",
      "subject": "Integrate cancellation cleanup and approval fixes"
    },
    {
      "hash": "087be5a9",
      "date": "2026-11-13",
      "subject": "Integrate embedded helper qualification fixes"
    },
    {
      "hash": "6877196b",
      "date": "2026-11-13",
      "subject": "Merge main and preserve combined SDK release behavior"
    },
    {
      "hash": "8c99b01e",
      "date": "2026-11-13",
      "subject": "Merge pull request #893 from andrewyng/feat/owcluster-cli"
    },
    {
      "hash": "bf754ba5",
      "date": "2026-11-13",
      "subject": "Merge pull request #890 from andrewyng/fix/sdk-activity-metadata"
    },
    {
      "hash": "098bcbdd",
      "date": "2026-11-13",
      "subject": "Merge pull request #889 from andrewyng/fix/sdk-release-qualification"
    },
    {
      "hash": "be7f6f5b",
      "date": "2026-11-13",
      "subject": "fix: inspect service attachments without a worker lease"
    },
    {
      "hash": "c851e610",
      "date": "2026-11-13",
      "subject": "fix: accept DNS case variation in private cluster tunnel"
    },
    {
      "hash": "a67cfad9",
      "date": "2026-11-13",
      "subject": "fix: reconcile completed AWS infrastructure before installation"
    },
    {
      "hash": "7390f061",
      "date": "2026-11-13",
      "subject": "test: report runtime causes in assistant regressions"
    },
    {
      "hash": "c6797d58",
      "date": "2026-11-13",
      "subject": "fix: preserve deployment review prices across restarts"
    },
    {
      "hash": "6f8eec29",
      "date": "2026-11-13",
      "subject": "test: keep unrelated GCP fixtures unchanged"
    },
    {
      "hash": "0c79d486",
      "date": "2026-11-13",
      "subject": "Ignore local example credentials and signing files"
    },
    {
      "hash": "95d175a2",
      "date": "2026-11-13",
      "subject": "fix: preserve private installation access and recording schema setup"
    },
    {
      "hash": "7a0ea3c2",
      "date": "2026-11-11",
      "subject": "Fix private Azure image publication across Docker image stores"
    },
    {
      "hash": "d47ceb69",
      "date": "2026-11-11",
      "subject": "Support reviewed OpenShell 0.1.8 deployments"
    },
    {
      "hash": "9cd45522",
      "date": "2026-11-11",
      "subject": "Simplify deployment configuration and qualify local Kubernetes"
    },
    {
      "hash": "9fda56b2",
      "date": "2026-11-11",
      "subject": "Add Azure AWS and local cluster configuration examples"
    },
    {
      "hash": "abcbeadc",
      "date": "2026-11-11",
      "subject": "Add CLI controls for management UI and trace storage"
    },
    {
      "hash": "febd5c03",
      "date": "2026-11-13",
      "subject": "test: keep legacy runtime runner paths nonoptional"
    },
    {
      "hash": "cdaa290c",
      "date": "2026-11-13",
      "subject": "fix: handle optional runners in examples and partner packages"
    },
    {
      "hash": "1ccb4838",
      "date": "2026-11-13",
      "subject": "fix: wait for cancellation cleanup before surfacing interruptions"
    },
    {
      "hash": "59a17fc9",
      "date": "2026-11-13",
      "subject": "feat: use owcluster with a compatible ows alias"
    },
    {
      "hash": "7effd296",
      "date": "2026-11-13",
      "subject": "fix: start tool-free embedded agents without a runner helper"
    },
    {
      "hash": "164acdbb",
      "date": "2026-11-13",
      "subject": "fix: expose approval decisions and safe denial context"
    },
    {
      "hash": "53359495",
      "date": "2026-11-13",
      "subject": "fix: expose tool activity names and arguments"
    },
    {
      "hash": "a6a8c9b8",
      "date": "2026-11-13",
      "subject": "Fix SDK errors for conflicting agent definitions"
    },
    {
      "hash": "9f7a2e18",
      "date": "2026-11-13",
      "subject": "Keep release versions in compatibility documentation"
    },
    {
      "hash": "70c2c491",
      "date": "2026-11-13",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "6aff67a5",
      "date": "2026-11-14",
      "subject": "Merge pull request #137 from zhanglunet/trend/prd406-t5-collab-session-acceptance"
    },
    {
      "hash": "49d0251e",
      "date": "2026-11-14",
      "subject": "Merge pull request #136 from zhanglunet/trend/prd406-t4-collab-session-boundary"
    },
    {
      "hash": "be21c668",
      "date": "2026-11-14",
      "subject": "Merge pull request #135 from zhanglunet/trend/prd406-t3-collab-session-gates"
    },
    {
      "hash": "0599c0ac",
      "date": "2026-11-14",
      "subject": "Merge pull request #134 from zhanglunet/trend/prd406-t2-collab-session-impl"
    },
    {
      "hash": "0b0a48f8",
      "date": "2026-11-14",
      "subject": "Merge pull request #133 from zhanglunet/trend/prd406-t1-collab-session"
    },
    {
      "hash": "5dd216d8",
      "date": "2026-11-13",
      "subject": "Refresh SDK guides and published-package examples"
    },
    {
      "hash": "89c42e3f",
      "date": "2026-11-14",
      "subject": "test(prd-406): T5 验收试运行——全链两遍逐字节一致+失败演练+链复跑+文档无密钥"
    },
    {
      "hash": "1def4bd7",
      "date": "2026-11-14",
      "subject": "test(prd-406): T4 划界断言——下游载体零导入+借鉴仓零符号+标准库-only+R1~R4 红线钉值"
    },
    {
      "hash": "655b9a3b",
      "date": "2026-11-14",
      "subject": "feat(prd-406): T3 会话闸门——append_only LEDGER_DRIFT + accept 双向对账 + outlet 拦截 + gate_summary 一票否决"
    },
    {
      "hash": "83ba737b",
      "date": "2026-11-14",
      "subject": "feat(prd-406): T2 中文 skill 协同评审会话内核——propose/accept/reject 署名事件+单向状态机+JSONL append-only 账本+outlet 出口包装"
    },
    {
      "hash": "1682dc57",
      "date": "2026-11-14",
      "subject": "docs(prd-406): T1 中文 skill 协同评审会话设计——事件 schema/状态机/三码闸门/划界表+PR 门槛四项自查"
    },
    {
      "hash": "01e96a56",
      "date": "2026-11-12",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "3256bf34",
      "date": "2026-11-13",
      "subject": "Merge pull request #132 from zhanglunet/trend/prd-383-t5-checklist-failure-verify-bench-acceptance"
    },
    {
      "hash": "a30f15e0",
      "date": "2026-11-13",
      "subject": "Merge pull request #131 from zhanglunet/trend/prd-383-t4-checklist-failure-verify-bench-boundary"
    },
    {
      "hash": "130e9988",
      "date": "2026-11-13",
      "subject": "Merge pull request #130 from zhanglunet/trend/prd-383-t3-checklist-failure-verify-bench-gate"
    },
    {
      "hash": "ee83f4ea",
      "date": "2026-11-13",
      "subject": "Merge pull request #129 from zhanglunet/trend/prd-383-t2-checklist-failure-verify-bench-impl"
    },
    {
      "hash": "30316f33",
      "date": "2026-11-13",
      "subject": "Merge pull request #128 from zhanglunet/trend/prd-383-t1-checklist-failure-verify-bench"
    },
    {
      "hash": "4af48474",
      "date": "2026-11-12",
      "subject": "Merge pull request #888 from andrewyng/docs/readme-walkthrough"
    },
    {
      "hash": "5b2007b9",
      "date": "2026-11-12",
      "subject": "docs: lead SDK onboarding with architecture and builder skill"
    },
    {
      "hash": "93877871",
      "date": "2026-11-12",
      "subject": "docs: improve Desktop App and SDK getting started guides"
    },
    {
      "hash": "e6301931",
      "date": "2026-11-12",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "319850e8",
      "date": "2026-11-13",
      "subject": "Merge pull request #127 from zhanglunet/docs/16-align-enterprise-release-tags"
    },
    {
      "hash": "a4f2328a",
      "date": "2026-11-12",
      "subject": "Merge pull request #887 from andrewyng/docs/readme-product-story"
    },
    {
      "hash": "fedef572",
      "date": "2026-11-13",
      "subject": "docs: clarify wording flagged by terminology checks"
    },
    {
      "hash": "8945cd1d",
      "date": "2026-11-12",
      "subject": "docs: connect Desktop App and Harness SDK in README"
    },
    {
      "hash": "7af264be",
      "date": "2026-11-12",
      "subject": "Merge pull request #886 from andrewyng/docs/harness-readme-refresh"
    },
    {
      "hash": "ea495cd0",
      "date": "2026-11-12",
      "subject": "docs: simplify Harness SDK onboarding and add architecture visual"
    },
    {
      "hash": "b6008ee5",
      "date": "2026-11-12",
      "subject": "Merge pull request #885 from andrewyng/docs/sdk-readme-and-builder-skill"
    },
    {
      "hash": "8b27b396",
      "date": "2026-11-12",
      "subject": "feat(skills): confirm replacement and retain installation backups"
    },
    {
      "hash": "43f7e63c",
      "date": "2026-11-12",
      "subject": "docs: clarify SDK tools, approvals and builder skill usage"
    },
    {
      "hash": "3fcc22f4",
      "date": "2026-11-12",
      "subject": "test(prd-383): T5 验收试运行——验证台接入点全链演练（run_checklist 失败项→verify_failures→VERIFIED 转人工拍板来源形态→JSONL 落账→闸门全 pass）两遍逐字节一致+UNVERIFIED 拦截演练（误报失败拦在人工拍板外）落账留痕+checkers 变更二次验证关闭演练（STALE 拒绝复用）+零改写复验+append-only+链复跑子进程实测+文档无密钥（trend #1887 的 T5 环节，6 例全绿）"
    },
    {
      "hash": "044f9254",
      "date": "2026-11-12",
      "subject": "test(prd-383): T4 checklist 失败验证台划界断言——验证台面与收件箱/机检引擎/解析器/重放双向模块隔离+零外部仓内耦合钉值（gates 只 import 同链 checkers_fingerprint）+R1/R2/R3/R4 红线钉值+借鉴仓零符号（仅代码标识符）+§3 引擎/收件箱面符号不变"
    },
    {
      "hash": "a7261df5",
      "date": "2026-11-12",
      "subject": "feat(prd-383): T3 checklist 失败验证台闸门——mark_baseline+append_only_gate 账本只增不删复核（LEDGER_DRIFT）+verdict_gate 结论与复现证据双向对账（BENCH_REPRO_MISMATCH/BENCH_INCOMPLETE）+stale_gate checkers 指纹复核（BENCH_STALE）+gate_summary 一票否决+ERROR_CODES 随模块导出（348 教训）+零改写词面 AST+闸门只读（trend #1887 的 T3 环节，15 例全绿，T2 回归 11 例仍绿）"
    },
    {
      "hash": "d92cc207",
      "date": "2026-11-12",
      "subject": "feat(prd-383): T2 checklist 失败验证台最小实现——verify_failure 逐条失败复跑验证（recheck_fn 注入重跑同一 checker 集经 run_checklist 引擎，复现=同 check_id+状态 fail 匹配；机检器已修复→复现不出 UNVERIFIED 防误报失败进人工拍板）+verify_failures 人工拍板来源包装（UNVERIFIED 拦下）+FailureBenchLedger JSONL append-only 真实落库+reverify checkers 变更二次验证（BENCH_STALE 拒绝复用）+checkers_fingerprint（checker 名清单 canonical JSON sha16）+零改写词面 AST（trend #1887 的 T2 环节，11 例全绿，devlog 落库）"
    },
    {
      "hash": "5acc3763",
      "date": "2026-11-12",
      "subject": "docs: PRD-383/T1 checklist 失败验证台设计——失败复跑验证过才进人工拍板（run_checklist 失败项→verify_failure→decision_inbox.collect(manual_reviews) 接入点+重跑同一机检器复算+JSONL 落账+TAMPERED 红线不变，trend #1887）"
    },
    {
      "hash": "797f86eb",
      "date": "2026-11-13",
      "subject": "docs: align enterprise release tags and version examples"
    },
    {
      "hash": "a482680e",
      "date": "2026-11-12",
      "subject": "Merge pull request #884 from andrewyng/feat/sdk-review-guidance"
    },
    {
      "hash": "b8d7616f",
      "date": "2026-11-12",
      "subject": "fix(sdk): bound managed admission stack usage"
    },
    {
      "hash": "685b6d12",
      "date": "2026-11-12",
      "subject": "feat(sdk): add reviewer and compaction guidance"
    }
  ]
} as const;
