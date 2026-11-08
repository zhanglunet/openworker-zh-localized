export const repoReport = {
  "generatedAt": "2026-11-09T00:07:08+09:00",
  "branch": "main",
  "head": "9a9920774590172cac82eb7648ef3b10a27e573b",
  "shortHead": "9a99207",
  "totalFiles": 751,
  "byExt": [
    {
      "name": "py",
      "count": 335
    },
    {
      "name": "ts",
      "count": 105
    },
    {
      "name": "md",
      "count": 91
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
      "count": 155
    },
    {
      "name": "coworker",
      "count": 134
    },
    {
      "name": "docs",
      "count": 114
    },
    {
      "name": "website",
      "count": 36
    },
    {
      "name": "scripts",
      "count": 26
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
    }
  ],
  "weeklyCommits": [
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
    },
    {
      "hash": "7034f06",
      "date": "2026-11-02",
      "subject": "docs: refresh generated site reports"
    },
    {
      "hash": "793b981",
      "date": "2026-11-02",
      "subject": "chore: 更新上游哨兵水位（PRD-068）"
    }
  ]
} as const;
