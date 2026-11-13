export const repoReport = {
  "generatedAt": "2026-11-14T00:25:30+08:00",
  "branch": "main",
  "head": "6aff67a5e444bb440fa0b6eb832dd48d8746c791",
  "shortHead": "6aff67a",
  "totalFiles": 793,
  "byExt": [
    {
      "name": "py",
      "count": 366
    },
    {
      "name": "ts",
      "count": 105
    },
    {
      "name": "md",
      "count": 102
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
      "count": 21
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
      "name": "lock",
      "count": 3
    },
    {
      "name": "dmg",
      "count": 2
    },
    {
      "name": "js",
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
      "count": 176
    },
    {
      "name": "coworker",
      "count": 134
    },
    {
      "name": "docs",
      "count": 125
    },
    {
      "name": "scripts",
      "count": 36
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
      "name": "skills",
      "count": 2
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
      "hash": "6aff67a",
      "date": "2026-11-14",
      "subject": "Merge pull request #137 from zhanglunet/trend/prd406-t5-collab-session-acceptance"
    },
    {
      "hash": "49d0251",
      "date": "2026-11-14",
      "subject": "Merge pull request #136 from zhanglunet/trend/prd406-t4-collab-session-boundary"
    },
    {
      "hash": "be21c66",
      "date": "2026-11-14",
      "subject": "Merge pull request #135 from zhanglunet/trend/prd406-t3-collab-session-gates"
    },
    {
      "hash": "0599c0a",
      "date": "2026-11-14",
      "subject": "Merge pull request #134 from zhanglunet/trend/prd406-t2-collab-session-impl"
    },
    {
      "hash": "0b0a48f",
      "date": "2026-11-14",
      "subject": "Merge pull request #133 from zhanglunet/trend/prd406-t1-collab-session"
    },
    {
      "hash": "89c42e3",
      "date": "2026-11-14",
      "subject": "test(prd-406): T5 验收试运行——全链两遍逐字节一致+失败演练+链复跑+文档无密钥"
    },
    {
      "hash": "1def4bd",
      "date": "2026-11-14",
      "subject": "test(prd-406): T4 划界断言——下游载体零导入+借鉴仓零符号+标准库-only+R1~R4 红线钉值"
    },
    {
      "hash": "655b9a3",
      "date": "2026-11-14",
      "subject": "feat(prd-406): T3 会话闸门——append_only LEDGER_DRIFT + accept 双向对账 + outlet 拦截 + gate_summary 一票否决"
    },
    {
      "hash": "83ba737",
      "date": "2026-11-14",
      "subject": "feat(prd-406): T2 中文 skill 协同评审会话内核——propose/accept/reject 署名事件+单向状态机+JSONL append-only 账本+outlet 出口包装"
    },
    {
      "hash": "1682dc5",
      "date": "2026-11-14",
      "subject": "docs(prd-406): T1 中文 skill 协同评审会话设计——事件 schema/状态机/三码闸门/划界表+PR 门槛四项自查"
    },
    {
      "hash": "01e96a5",
      "date": "2026-11-12",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "3256bf3",
      "date": "2026-11-13",
      "subject": "Merge pull request #132 from zhanglunet/trend/prd-383-t5-checklist-failure-verify-bench-acceptance"
    }
  ],
  "weeklyCommits": [
    {
      "hash": "6aff67a",
      "date": "2026-11-14",
      "subject": "Merge pull request #137 from zhanglunet/trend/prd406-t5-collab-session-acceptance"
    },
    {
      "hash": "49d0251",
      "date": "2026-11-14",
      "subject": "Merge pull request #136 from zhanglunet/trend/prd406-t4-collab-session-boundary"
    },
    {
      "hash": "be21c66",
      "date": "2026-11-14",
      "subject": "Merge pull request #135 from zhanglunet/trend/prd406-t3-collab-session-gates"
    },
    {
      "hash": "0599c0a",
      "date": "2026-11-14",
      "subject": "Merge pull request #134 from zhanglunet/trend/prd406-t2-collab-session-impl"
    },
    {
      "hash": "0b0a48f",
      "date": "2026-11-14",
      "subject": "Merge pull request #133 from zhanglunet/trend/prd406-t1-collab-session"
    },
    {
      "hash": "89c42e3",
      "date": "2026-11-14",
      "subject": "test(prd-406): T5 验收试运行——全链两遍逐字节一致+失败演练+链复跑+文档无密钥"
    },
    {
      "hash": "1def4bd",
      "date": "2026-11-14",
      "subject": "test(prd-406): T4 划界断言——下游载体零导入+借鉴仓零符号+标准库-only+R1~R4 红线钉值"
    },
    {
      "hash": "655b9a3",
      "date": "2026-11-14",
      "subject": "feat(prd-406): T3 会话闸门——append_only LEDGER_DRIFT + accept 双向对账 + outlet 拦截 + gate_summary 一票否决"
    },
    {
      "hash": "83ba737",
      "date": "2026-11-14",
      "subject": "feat(prd-406): T2 中文 skill 协同评审会话内核——propose/accept/reject 署名事件+单向状态机+JSONL append-only 账本+outlet 出口包装"
    },
    {
      "hash": "1682dc5",
      "date": "2026-11-14",
      "subject": "docs(prd-406): T1 中文 skill 协同评审会话设计——事件 schema/状态机/三码闸门/划界表+PR 门槛四项自查"
    },
    {
      "hash": "01e96a5",
      "date": "2026-11-12",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "3256bf3",
      "date": "2026-11-13",
      "subject": "Merge pull request #132 from zhanglunet/trend/prd-383-t5-checklist-failure-verify-bench-acceptance"
    },
    {
      "hash": "a30f15e",
      "date": "2026-11-13",
      "subject": "Merge pull request #131 from zhanglunet/trend/prd-383-t4-checklist-failure-verify-bench-boundary"
    },
    {
      "hash": "130e998",
      "date": "2026-11-13",
      "subject": "Merge pull request #130 from zhanglunet/trend/prd-383-t3-checklist-failure-verify-bench-gate"
    },
    {
      "hash": "ee83f4e",
      "date": "2026-11-13",
      "subject": "Merge pull request #129 from zhanglunet/trend/prd-383-t2-checklist-failure-verify-bench-impl"
    },
    {
      "hash": "30316f3",
      "date": "2026-11-13",
      "subject": "Merge pull request #128 from zhanglunet/trend/prd-383-t1-checklist-failure-verify-bench"
    },
    {
      "hash": "e630193",
      "date": "2026-11-12",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "319850e",
      "date": "2026-11-13",
      "subject": "Merge pull request #127 from zhanglunet/docs/16-align-enterprise-release-tags"
    },
    {
      "hash": "fedef57",
      "date": "2026-11-13",
      "subject": "docs: clarify wording flagged by terminology checks"
    },
    {
      "hash": "3fcc22f",
      "date": "2026-11-12",
      "subject": "test(prd-383): T5 验收试运行——验证台接入点全链演练（run_checklist 失败项→verify_failures→VERIFIED 转人工拍板来源形态→JSONL 落账→闸门全 pass）两遍逐字节一致+UNVERIFIED 拦截演练（误报失败拦在人工拍板外）落账留痕+checkers 变更二次验证关闭演练（STALE 拒绝复用）+零改写复验+append-only+链复跑子进程实测+文档无密钥（trend #1887 的 T5 环节，6 例全绿）"
    },
    {
      "hash": "044f925",
      "date": "2026-11-12",
      "subject": "test(prd-383): T4 checklist 失败验证台划界断言——验证台面与收件箱/机检引擎/解析器/重放双向模块隔离+零外部仓内耦合钉值（gates 只 import 同链 checkers_fingerprint）+R1/R2/R3/R4 红线钉值+借鉴仓零符号（仅代码标识符）+§3 引擎/收件箱面符号不变"
    },
    {
      "hash": "a7261df",
      "date": "2026-11-12",
      "subject": "feat(prd-383): T3 checklist 失败验证台闸门——mark_baseline+append_only_gate 账本只增不删复核（LEDGER_DRIFT）+verdict_gate 结论与复现证据双向对账（BENCH_REPRO_MISMATCH/BENCH_INCOMPLETE）+stale_gate checkers 指纹复核（BENCH_STALE）+gate_summary 一票否决+ERROR_CODES 随模块导出（348 教训）+零改写词面 AST+闸门只读（trend #1887 的 T3 环节，15 例全绿，T2 回归 11 例仍绿）"
    },
    {
      "hash": "d92cc20",
      "date": "2026-11-12",
      "subject": "feat(prd-383): T2 checklist 失败验证台最小实现——verify_failure 逐条失败复跑验证（recheck_fn 注入重跑同一 checker 集经 run_checklist 引擎，复现=同 check_id+状态 fail 匹配；机检器已修复→复现不出 UNVERIFIED 防误报失败进人工拍板）+verify_failures 人工拍板来源包装（UNVERIFIED 拦下）+FailureBenchLedger JSONL append-only 真实落库+reverify checkers 变更二次验证（BENCH_STALE 拒绝复用）+checkers_fingerprint（checker 名清单 canonical JSON sha16）+零改写词面 AST（trend #1887 的 T2 环节，11 例全绿，devlog 落库）"
    },
    {
      "hash": "5acc376",
      "date": "2026-11-12",
      "subject": "docs: PRD-383/T1 checklist 失败验证台设计——失败复跑验证过才进人工拍板（run_checklist 失败项→verify_failure→decision_inbox.collect(manual_reviews) 接入点+重跑同一机检器复算+JSONL 落账+TAMPERED 红线不变，trend #1887）"
    },
    {
      "hash": "797f86e",
      "date": "2026-11-13",
      "subject": "docs: align enterprise release tags and version examples"
    },
    {
      "hash": "5e9deda",
      "date": "2026-11-11",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "c524679",
      "date": "2026-11-11",
      "subject": "Merge pull request #126 from zhanglunet/trend/baseline-fix-owzh"
    },
    {
      "hash": "1e1090a",
      "date": "2026-11-11",
      "subject": "fix: owzh main baseline — read PRD-341 design doc from local main copy instead of un-fetched branch"
    },
    {
      "hash": "2055054",
      "date": "2026-11-11",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "9d33f91",
      "date": "2026-11-11",
      "subject": "Merge pull request #125 from zhanglunet/trend/prd-369-t5-decision-inbox-acceptance"
    },
    {
      "hash": "316ebf0",
      "date": "2026-11-11",
      "subject": "Merge pull request #124 from zhanglunet/trend/prd-355-t5-zh-call-replay-acceptance"
    },
    {
      "hash": "34a0ffc",
      "date": "2026-11-11",
      "subject": "Merge pull request #123 from zhanglunet/trend/prd-369-t4-decision-inbox-boundary"
    },
    {
      "hash": "b5cfc72",
      "date": "2026-11-11",
      "subject": "Merge pull request #122 from zhanglunet/trend/prd-355-t4-zh-call-replay-boundary"
    },
    {
      "hash": "c816e1a",
      "date": "2026-11-11",
      "subject": "Merge pull request #121 from zhanglunet/trend/prd-355-t3-zh-call-replay-gate"
    },
    {
      "hash": "2a91bc1",
      "date": "2026-11-11",
      "subject": "Merge pull request #120 from zhanglunet/trend/prd-369-t3-decision-inbox-gate"
    },
    {
      "hash": "a07c9e7",
      "date": "2026-11-11",
      "subject": "Merge pull request #119 from zhanglunet/trend/prd-369-t2-decision-inbox-impl"
    },
    {
      "hash": "9d0546b",
      "date": "2026-11-11",
      "subject": "Merge pull request #118 from zhanglunet/trend/prd-355-t2-zh-call-replay-impl"
    },
    {
      "hash": "246ef31",
      "date": "2026-11-11",
      "subject": "Merge pull request #117 from zhanglunet/trend/prd-369-t1-decision-inbox"
    },
    {
      "hash": "fa5ef8f",
      "date": "2026-11-11",
      "subject": "Merge pull request #116 from zhanglunet/trend/prd-355-t1-zh-call-replay"
    },
    {
      "hash": "86a396a",
      "date": "2026-11-11",
      "subject": "fix(prd-369-t3): export ERROR_CODES from decision_inbox_gates + import unittest in T3 test (collection ImportError/NameError)"
    },
    {
      "hash": "6d09d34",
      "date": "2026-11-11",
      "subject": "fix(prd-369-t3): export ERROR_CODES from decision_inbox_gates + import unittest in T3 test (collection ImportError/NameError)"
    },
    {
      "hash": "873c603",
      "date": "2026-11-11",
      "subject": "test(prd-369): T5 验收试运行——人工决策收件箱全链周期演练（收→批→拒→重复裁决→AUTO_EXEC→CHOICE_REQUIRED）确定性可复现+链复跑子进程实测（含 T3 双缺陷订正后全链）+文档无密钥"
    },
    {
      "hash": "4e6dc32",
      "date": "2026-11-11",
      "subject": "test(prd-355): T5 验收试运行——中文调用重放全链回放确定性可复现+MISMATCH/INPUT_DRIFT 演练（三重指纹区分漂移来源）+链复跑子进程实测+文档无密钥"
    },
    {
      "hash": "f990b29",
      "date": "2026-11-11",
      "subject": "fix+test(prd-369): T3 双缺陷订正（ERROR_CODES 导出+测试 unittest 导入）+ T4 人工决策收件箱划界断言"
    },
    {
      "hash": "9641ffe",
      "date": "2026-11-11",
      "subject": "test(prd-355): T4 中文调用重放划界断言——重放面与升级快照/解析器/机检双向模块隔离+lookup_fn 注入唯一耦合钉值+R1/R2/R3/R4 红线钉值"
    },
    {
      "hash": "064f553",
      "date": "2026-11-11",
      "subject": "feat: PRD-355/T3 中文 skill 调用重放闸门——zh_call_replay_gates.py ledger_gate 账本一致性复核（verdict/evidence/指纹与账本最后入账逐字节一致 VERDICT_MISMATCH 显形）+mark_baseline+append_only_gate append-only 复核（基线锚删除与首条改写 LEDGER_DRIFT 显形）+pack_gate 别包冒充 PACK_STALE 显形+gate_summary 多闸一票否决+ERROR_CODES 随模块导出（348 教训）+与 T2 串联（真实 make_pack+replay(lookup)+ReplayLedger 产物三闸全过）+重放零执行 AST 零网络+闸门只读（16 例全绿，355 链+369 链仍绿，trend #1634 的 T3 环节）"
    },
    {
      "hash": "0e29857",
      "date": "2026-11-11",
      "subject": "feat: PRD-369/T3 人工拍板收件箱批阅闸门——decision_inbox_gates.py mark_baseline+append_only_gate events 只增不删复核（基线锚删除与首事件改写 LEDGER_DRIFT 显形）+state_gate 条目状态与 events 双向对账（直接改写/回滚/删除三破坏 STATE_INCONSISTENT 显形——裁决必须双向一致 R1 落地）+gate_summary 多闸一票否决+ERROR_CODES 随模块导出（348 教训）+与 T2 串联（真实 add/approve(CHOICE)/reject 产物过闸全 pass）+闸门只读消费（零裁决调用 零网络）（13 例全绿，369 链+341 链仍绿，trend #1648 的 T3 环节）"
    },
    {
      "hash": "2fad6e0",
      "date": "2026-11-10",
      "subject": "feat: PRD-369/T2 人工拍板收件箱最小实现——decision_inbox.py collect 三源只读汇聚（manual_review/answer_confirm/zh_disambiguation 词表封闭/五件套缺一 INBOX_ITEM_INCOMPLETE 防御分支显形拒绝入箱/manual questions 引用 341 问题清单+answers_ref 引用附答留痕）+InboxLedger 状态机（approve/reject 人批留痕/重复裁决 INBOX_DOUBLE_DECIDE/未知 id/携带 checklist 写/注册表写/附答代填载荷 INBOX_AUTO_EXEC_ATTEMPT 显形拒绝——零 checklist 状态改写零代填 R1 TAMPERED 红线继续 §6.1 零代填裁决/歧义项 approve 必带选中候选且须在列表内 INBOX_CHOICE_REQUIRED）+append-only events+view kind 过滤+与 PRD-341 run_checklist P10–P12 真实串联+AST 零网络零子进程（11 例全绿，341 链 33 例+355 链仍绿，trend #1648 的 T2 环节）"
    },
    {
      "hash": "85cc04b",
      "date": "2026-11-10",
      "subject": "feat: PRD-355/T2 中文 skill 调用重放包最小实现——zh_call_replay.py make_pack（决策 utterance/resolved_skill/status/candidates 投影/原文+归一化+登记册三重指纹+rules_version/length 齐校验；缺任一 PACK_INCOMPLETE）+replay 重放三步（三重指纹分别复核 INPUT_DRIFT 且漂移来源线索可区分——指令原文/登记册变/归一化变/lookup_fn 深拷贝解析层复算与 zh_trigger_registry.lookup+build_registry 真实串联零 skill 执行 R2/decisions 逐字节比对 MISMATCH 首分歧条显形含候选零静默 R3）+ReplayLedger append-only（R4）+AST 零网络零子进程（9 例全绿，341 链 33 例仍绿，trend #1634 的 T2 环节）"
    },
    {
      "hash": "45d1080",
      "date": "2026-11-10",
      "subject": "docs: PRD-369/T1 人工拍板收件箱设计——三类人工项统一收口（manual_review/answer_confirm/zh_disambiguation 词表封闭 R2）+证据四件套（fingerprint+questions/candidates 引用 341 附答留痕 R3）+零 checklist 状态改写零注册表写零附答代填（R1 AUTO_EXEC 拒绝——TAMPERED 红线继续）+歧义项 CHOICE_REQUIRED+append-only 拒绝留痕（R4）+plannotator/t3code 实测只借控制面形态+与 341/299 划界（trend #1648）"
    },
    {
      "hash": "eb40ee1",
      "date": "2026-11-10",
      "subject": "docs: PRD-355/T1 中文 skill 调用重放包设计——三件套（中文指令原文+归一化+注册表三重指纹/解析与歧义候选处理/结果摘要 R1）+重放零 skill 执行红线（只复算 lookup/resolve R2）+MISMATCH 含归一化差异线索显形零静默（R3）+append-only（R4）+AiSOC/OpenBot MIT 实测只借形态+与 285 升级快照/267 技能来源/341 checklist 划界（trend #1634）"
    },
    {
      "hash": "52def00",
      "date": "2026-11-10",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "00f9c5d",
      "date": "2026-11-10",
      "subject": "Merge pull request #115 from zhanglunet/trend/prd-341-t5-acceptance"
    },
    {
      "hash": "de236fe",
      "date": "2026-11-10",
      "subject": "Merge pull request #114 from zhanglunet/trend/prd-341-t4-boundary"
    },
    {
      "hash": "4063e59",
      "date": "2026-11-10",
      "subject": "Merge pull request #113 from zhanglunet/trend/prd-341-t3-gate"
    },
    {
      "hash": "040aab4",
      "date": "2026-11-10",
      "subject": "Merge pull request #112 from zhanglunet/trend/prd-341-t2-checklist-impl"
    },
    {
      "hash": "dd8a640",
      "date": "2026-11-10",
      "subject": "Merge pull request #111 from zhanglunet/trend/prd-341-t1-12factors-design"
    },
    {
      "hash": "413e399",
      "date": "2026-11-10",
      "subject": "Merge pull request #109 from zhanglunet/trend/prd-341-t1-design"
    },
    {
      "hash": "9a05b1e",
      "date": "2026-11-09",
      "subject": "test: PRD-341/T5 十二原则 checklist 验收试运行——test_prd341_t5_acceptance.py（7 例全绿，链上 T2–T4 33 例仍绿）①真实 skill 全量试运行（十二项全跑 机检 9 过+manual 3 附答留痕→READY_FOR_HUMAN 闸门零替人拍板+双 skill batch_gate 汇总逐 skill 裁决平列+回放逐字节可复现）②失败演练三路全显形（机检 fail→BLOCKED 未过项显形零视为通过/manual 未附答→PENDING_MANUAL 问题清单显形/manual 项被篡改为 pass→TAMPERED R4 复核拒绝）③文档无密钥（T1 设计文档经 git show origin/trend/prd-341-t1-12factors-design 扫描零密钥/零 IP/外链仅 github 与 example 域）（trend #1620 的 T5 环节）"
    },
    {
      "hash": "5c68185",
      "date": "2026-11-09",
      "subject": "test: PRD-341/T4 十二原则 checklist 划界断言——test_prd341_t4_boundary.py（7 例全绿）R3 数据驱动断言（run_checklist/checklist_gate 源码零原则 id 零机检器名复钉/gate 的 MANUAL_IDS is 数据模块同一 frozenset 单向引用/增补原则演练：运行时向 CHECKLIST 追加 P13 后 run_checklist 即覆盖新条目零改引擎代码 finally 还原零残留）+R2 零复用抽样断言（十二条 principle 全中文原创含 CJK 零英文 factor 术语/两模块 AST 零 humanlayer/12-factor/swe-agent 借鉴仓符号）+R1 复钉（check_ref 全部指向 scripts/ 既有模块）+与 199/227/303 划界（checklist_gate 单向只读消费零机检器模块导入）+与 PRD-303 重放包划界钉值（trend #1620 的 T4 环节）"
    },
    {
      "hash": "f9e7a1a",
      "date": "2026-11-09",
      "subject": "feat: PRD-341/T3 十二原则 checklist 通过闸门——checklist_gate.py GATE_CODES 四码封闭（READY_FOR_HUMAN/PENDING_MANUAL/BLOCKED/TAMPERED）+checklist_gate 单 skill 通过闸门（机检 fail→BLOCKED failing 显形/机检全过 manual 未附答→PENDING_MANUAL 问题清单显形零视为通过 R4/全备→READY_FOR_HUMAN 荐人工拍板闸门零替人拍板/manual 项状态被篡改为 pass/fail→TAMPERED 显形拒绝 R4 复核 manual 只能是 manual）+batch_gate 全库汇总归重（消费 T2 summarize/任一非 READY 整库归重/逐 skill 裁决平列人工逐个拍板）+与 T2 串联三种真实产物逐一过闸+AST 只读消费零网络零机检器导入（10 例全绿，T2 16 例仍绿，trend #1620 的 T3 环节）"
    },
    {
      "hash": "9b2b02f",
      "date": "2026-11-09",
      "subject": "feat: PRD-341/T2 十二原则 checklist 最小实现——CHECKLIST 声明式数据（check_ref 全部指向 scripts/ 既有模块 zh_trigger_registry/zh_sources/consistency_check/zh_skill_ref/skillpack_snapshot/cn_skill_sync_check/trigger_probe/zh_intake_gate 零新建判定逻辑 R1）+run_checklist 每 skill 一份（§6.1 裁决）+机检器反射注入适配器 honest 三态映射（None=clean/真值 pass/假值 fail 带 reason/异常 fail 显形/未注册 fail 显形——零视为通过 R4）+manual JSON 附答只留痕不改状态非法指向显形拒绝（§6.2 裁决）+summarize 全库汇总视图 failing 清单+引擎零硬编码 R3（数据与逻辑分离 T4 预埋）+模块 stdlib-only R2 零复用预埋（16 例 pytest 全绿）（trend #1620)"
    },
    {
      "hash": "af53436",
      "date": "2026-11-09",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "20fb91f",
      "date": "2026-11-09",
      "subject": "chore: 更新上游哨兵水位（PRD-068）"
    },
    {
      "hash": "f08712b",
      "date": "2026-11-09",
      "subject": "docs: PRD-341/T1 设计——生产级 agent 十二原则（trend #1620）"
    },
    {
      "hash": "23dcd08",
      "date": "2026-11-09",
      "subject": "docs: PRD-341/T1 生产级 agent 十二原则 checklist 设计——十二条自研原则逐条带检查形态封闭词表（P1-P9 机检全部 check_ref 指向既有机检器零新建判定逻辑/P10-P12 人工评审问题清单固定留痕）+checklist 声明式 JSON 数据驱动 R3（机检器零硬编码 T4 预埋）+结果三态 honest R4（pass/fail 带 reason/manual 带评审问题——零视为通过路径 T3 断言预埋）+NOASSERTION 来源零复用收紧（十二条从中文 skill 实际生产风险自研表述零翻译原仓）+与 PRD-199/227/303 重放包划界（check_ref 指向既有机检器复用结论零重复建设 T3 断言预埋）（trend #1620）"
    },
    {
      "hash": "194cf36",
      "date": "2026-11-08",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "0f68ecd",
      "date": "2026-11-09",
      "subject": "test: PRD-327/T4+T5 i18n 发布闸门划界断言 + 验收试运行（6 例，trend #1604 区段） (#108)"
    },
    {
      "hash": "5d588d5",
      "date": "2026-11-08",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "9a99207",
      "date": "2026-11-09",
      "subject": "feat: PRD-327/T3 国际化技能包发布闸门（7 例，trend #1604 区段） (#107)"
    },
    {
      "hash": "0f31bd8",
      "date": "2026-11-08",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "e8de9c5",
      "date": "2026-11-08",
      "subject": "feat: PRD-327/T2 国际化技能包——双语 SKILL.md + manifest（trend #670） (#106)"
    },
    {
      "hash": "7dbae91",
      "date": "2026-11-08",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "9c682a2",
      "date": "2026-11-08",
      "subject": "docs: PRD-327/T1 设计——国际化形态（trend #1606） (#105)"
    },
    {
      "hash": "c0323b3",
      "date": "2026-11-07",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "184bb22",
      "date": "2026-11-08",
      "subject": "test: PRD-313/T5 验收试运行——全链两遍逐字节一致+拒绝零写盘+红线终检+文档无密钥（trend #1580） (#104)"
    },
    {
      "hash": "3ead2ab",
      "date": "2026-11-07",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "50a969d",
      "date": "2026-11-08",
      "subject": "fix(tests): T4 断言文件重生成——补占位符漏替换 (#103)"
    },
    {
      "hash": "d3a7538",
      "date": "2026-11-07",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "7434add",
      "date": "2026-11-08",
      "subject": "feat: PRD-313/T3 重放校验闸门——replay_gate 一票否决+require_gate 异常形态+错误码扩 REPLAY_GATE_REFUSED（trend #1578） (#102)"
    },
    {
      "hash": "b2f3329",
      "date": "2026-11-07",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "189ef7f",
      "date": "2026-11-07",
      "subject": "feat: PRD-313/T2 中文 skill 调用重放包最小实现——replay-pack/v1+登记册指纹+append-only 账本+verify_zh_replay 二值校验（11 例，trend #1577） (#101)"
    },
    {
      "hash": "dcb5d51",
      "date": "2026-11-07",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "7248db7",
      "date": "2026-11-07",
      "subject": "fix(prd299): 补回被合并覆盖的 T3 错误码封闭词表——zh_skill_ref 增加 ERROR_CODES 三码（修复 #97 合并事故，trend #1198） - 根因：PRD-299/T3（#97）合并时 -X theirs 吞掉词表，T3/T4 测试导入失败 → main CI 红 - 验证：PRD-299 链 T2/T3/T4/T5 共 33 例全过"
    },
    {
      "hash": "c2340ce",
      "date": "2026-11-07",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "ce720cc",
      "date": "2026-11-07",
      "subject": "docs: PRD-313/T1 openworker-zh-localized 重放包设计——replay-pack/v1（输入指纹+决策+输出、二值重放结论、重放面只读）（trend #1576） (#100)"
    },
    {
      "hash": "992fd0f",
      "date": "2026-11-07",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "02ab6be",
      "date": "2026-11-07",
      "subject": "PRD-240/T5 验收试运行：抽样知识问答溯源 (#94)"
    },
    {
      "hash": "2348e77",
      "date": "2026-11-07",
      "subject": "PRD-239/T5 验收试运行：中文口语指令抽样 (#93)"
    },
    {
      "hash": "71321c8",
      "date": "2026-11-07",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "ff4eb47",
      "date": "2026-11-07",
      "subject": "feat: PRD-240/T4 一致性校验——consistency_check.py check_consistency 三方对齐（E-DANGLING-REF 悬空引用规则 kb_refs/知识回指原文、E-CIRCULAR-REF 知识→规则反向引用禁止、E-ORPHAN-SOURCE 孤儿原文提示级）+ issues 机读清单（code/location/detail）+ summary errors/warnings/aligned（5 例，trend #1203） (#92)"
    },
    {
      "hash": "bfaf6bc",
      "date": "2026-11-07",
      "subject": "feat: PRD-239/T4 按包加载与检索适配——pack_loader.py load_skills_for_runtime（目录形态加载 role-packs/*/skills/*/SKILL.md 与既有 store.py 同构，现有使用方式不断链不依赖登记资产）+ search_skills 检索（description/name 子串 OR/短词拒绝/确定性）（4 例，trend #1198） (#91)"
    },
    {
      "hash": "eefaa32",
      "date": "2026-11-07",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "b64c3b6",
      "date": "2026-11-07",
      "subject": "feat: PRD-240/T3 规则层计算接口——validate_rule §5 全字段（id 格式/词表/封闭类型/kb_refs 非空不悬空 §6.3/strict）+ evaluate_rule 可算执行（§5.1 四条钉死：纯函数/类型封闭/precondition 不满足统一 not_applicable/可重放）+ 三形态 expr（ast 白名单求值：算术/比较/逻辑/条件/min-max-abs 其余拒绝）/table 判定表/formula 算术，script 拒绝执行须沙箱评审 + 回指原文依据（evidence.sources 经 T2 trace_to_source 到 raw_text）（18 例，trend #1202） (#90)"
    },
    {
      "hash": "380fbac",
      "date": "2026-11-07",
      "subject": "feat: PRD-239/T3 中文触发词登记册——§5.2 字段全量（19 条种子逐句入册+P0 产物名示范+2 条场景词同包多技能冲突示范）、收录冲突处理（check_conflicts：未标注跨技能同词拒绝并列出双方人工消歧，已标注放行）、lookup 口语命中（归一消形差/整句精确/条目短语嵌句、§5.4 裁决 P0→P3 排序、同级跨技能 ambiguous 待澄清可解释、停用留痕不删行）、coverage 三包覆盖检查、诚实边界声明（发行侧登记资产非运行时引擎）（14 例，trend #1197） (#89)"
    },
    {
      "hash": "df71490",
      "date": "2026-11-07",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "7f6ae90",
      "date": "2026-11-07",
      "subject": "PRD-299/T4 与 PRD-267/285 及 239 双路径划界断言 (#98)"
    },
    {
      "hash": "4df6157",
      "date": "2026-11-07",
      "subject": "PRD-299/T3 引用解析歧义闸门：候选列表请用户选，人工消歧留痕 (#97)"
    },
    {
      "hash": "d101d6f",
      "date": "2026-11-07",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "34b6080",
      "date": "2026-11-07",
      "subject": "feat: PRD-299/T5 验收试运行——中文口语指令 @引用 全链回放（6 例，trend #1500） (#99)"
    },
    {
      "hash": "782113b",
      "date": "2026-11-07",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "adb4059",
      "date": "2026-11-07",
      "subject": "PRD-299/T2 引用解析最小实现：@中文技能名（归一/歧义候选/人工消歧留痕） (#96)"
    },
    {
      "hash": "182be98",
      "date": "2026-11-07",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "1ac0d58",
      "date": "2026-11-07",
      "subject": "docs: PRD-299/T1 中文指令 @中文技能名引用解析设计——中文 @语法与禁止形态（版本后缀/通配/中间空白不归一）/ref-resolution/v1 schema（meta_summary 定位+触发词计数零正文读取）/确定性归一四规则显形（全半角/繁简固定映射/去首尾空白——归一是规范化不是模糊匹配）/四错误码封闭词表（歧义列候选含一句话定位请用户选不按频次挑；chosen_from_candidates 人工消歧留痕）/与 239/T3 触发词登记册双路径划界（显式 @ 引用优先级高于口语命中，T4 断言预埋）/与 PRD-267/285 划界表（trend #1496） (#95)"
    }
  ]
} as const;
