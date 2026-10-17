# Playbook 第 2 章：三仓同步（T3 正文）

> PRD-030/T3（trend #183）。依据：`docs/enterprise/UPSTREAM_SYNC.md`（v1.0，2026-08-04）
> 与 `docs/enterprise/templates/` 下模板。本章是 playbook 第 2 章正文，对应 T1 大纲
> （`docs/plans/2026-10-17-enterprise-playbook-outline.md`）的第 2 章。
>
> 目标读者：下一次企业换肤打包的执行人（可能是第一次干这活的人）。
> 使用方式：按 1→2→3 节顺序走，第 5 节检查清单全勾才能进第 3 章（部署）。

## 1. 本章输入 / 输出

- **输入**：第 1 章的换肤记录单。关键字段只有一个——**汉化版基线 tag**（知道这版企业定制是从汉化版哪个版本长出来的）。
- **输出**：三仓版本对应表（模板如下，每次同步后更新一行）。

| 企业版版本 | 汉化版基线 tag | 上游对应 tag/commit | 汉化版 SHA（企业版实际消化到的） | 同步日期 | 同步人 |
|---|---|---|---|---|---|
| 0.1.7-corp.3 | v0.1.7 | andrewyng/openworker vX.Y.Z | abc1234 | 2026-10-20 | 张三 |

版本规则（UPSTREAM_SYNC §3.3）：企业版本号 = `<汉化版基线>-corp.<n>`，
如 `0.1.7-corp.3`；tag 触发企业发布流水线。此处是 `tauri.conf.json` 里的
version，不是 tag（tag 格式见 playbook 第 1 章 §3.1 的 `corp-vX.Y.Z`）。每次合并同步 PR 后，
在 PR 描述里记录消化到的汉化版 SHA，便于追溯"企业版含上游哪一天的功能"。

## 2. 三仓定义与代码流向（UPSTREAM_SYNC §1）

| 仓库 | 角色 | 说明 |
|---|---|---|
| `andrewyng/openworker`（公开） | 上游：功能真相 | 快速迭代中的 open beta |
| `Lenovo202409/openworker-zh`（公开） | 中转层 | 汉化版直接基于它二次整理 |
| `zhanglunet/openworker-zh-localized`（公开） | 汉化版：汉化基线 | 每日消化上游（含冲突处理与中文文案维护） |
| `<corp>/openworker-enterprise`（私有） | 企业版：企业定制 | 只消化汉化版，拿到"上游功能 + 中文界面"的合成结果 |

**单向逐级流动**：上游 → 汉化版 → 企业版。

打个比方：这像一条三级净水管线——上游是原水，汉化版是第一级滤芯（顺手把水里的英文"杂质"翻成中文），
企业版是第二级滤芯（只管加企业自己的"矿物质"）。企业版不需要直接对接上游，
因为汉化版已经每日把上游消化好了。

为什么不让企业版同时拉上游和汉化版两个 remote？
两条链路会把同一批上游提交以不同合并历史送达，制造重复冲突。
单链条 + git 三方合并（共同祖先清晰）是冲突最小的拓扑。

## 3. 同步顺序与工程保障

### 3.1 同步顺序（日常操作）

1. 上游有更新 → 汉化版 `sync-upstream.yml`（每日 01:35 UTC）自动 merge，人工审阅后合并。
   这一步是 PRD-029 的检测范围（见 §4），本章不重复造检测机制。
2. 汉化版有新提交 → 企业版 `sync-localized.yml`（每日 03:35 UTC，
   故意错开汉化版 2 小时，让当天上游变更先经汉化版消化）在 `sync/localized-main`
   分支自动 merge → 开 PR → CI（含冒烟测试，见 §3.4）+ 人工确认 → 合并进 `main`。
3. **永不直推 `main`**：同步永远走 PR。"实时"由每日节拍 + 随时手动触发保障，
   延迟上限 24h，比直推安全得多。
4. **同步 PR 必须用 merge commit 合并，禁止 squash / rebase 合并**：
   squash 会把合并结果压成单亲提交，被同步方的 tip 从此不再是本仓祖先——
   下一次同步会把已解决过的冲突**全部重放**。这是真实教训：
   汉化仓的上游同步 PR #2 就因 squash 导致约 20 个文件重放冲突。
   企业仓应在 GitHub 仓库设置中对 `sync/*` 分支的 PR 仅允许 merge commit。
5. 想立即拿到某个上游修复：先在汉化仓手动触发 `sync-upstream.yml` 并合并，
   再在企业仓手动触发 `sync-localized.yml`。
6. 同步 PR 冲突：按自动开的 Issue 中的命令本地 merge，冲突处优先保留
   `enterprise/` 挂载点行 + 接受汉化版其余改动，push 到 `sync/localized-main` 更新 PR。
7. 上游大版本重构：冻结同步 → 在 `sync/localized-main` 上集中处理 →
   企业冒烟全绿后合并（预算 1-2 天）。

### 3.2 工程保障：目录隔离 + 挂载点（UPSTREAM_SYNC §2）

同步安全的根本不在 git 技巧，而在**改动面设计**。企业版全部定制遵守三条规则：

**规则 A：新增优先，独立目录。**
企业独有内容一律放在上游/汉化版**不存在的路径**下，merge 时物理上不可能冲突：

```
enterprise/                      # 企业定制根目录（上游永远不会有）
├── skills/                      # 企业技能包（含 excel-ai-analyst 大表哥）
├── branding/                    # 主题 CSS 变量、图标源文件、DMG 背景、名称清单
├── config/                      # 默认 config.toml 模板、Provider 预置 profile
├── mcp/                         # 企业 CLI / 知识库 MCP server 配置与封装脚本
├── connectors/                  # 企业内部系统连接器（Python 模块，被挂载点 import）
├── tools/                       # 企业内置工具（如 excel_ai 工具封装）
└── site/                        # 企业站定制（基于 website/ 的品牌覆盖层）
.github/workflows/sync-localized.yml   # 新增，不与上游文件重名
.github/workflows/release-corp.yml     # 企业发布流水线，独立文件
```

**规则 B：改动收敛到"挂载点"。**
确实要动上游文件时，只加**一行注册/一处 import**，不重排不重写。
预期挂载点清单（每个文件的 diff 控制在几行内）：

| 挂载点文件 | 改动 | 目的 |
|-----------|------|------|
| `coworker/providers/registry.py` | DESCRIPTORS 追加企业 Provider 条目（一行即可，仿 stepfun 条目） | 预置私有模型入口 |
| `coworker/providers/matrix.py` | MATRIX 追加企业模型能力条目 | 避免能力被启发式降级 |
| `coworker/connectors/descriptors.py` | 追加"企业子包加载 + 白名单过滤"（仿 `connectors/experimental/` 加载段） | 企业连接器 |
| `coworker/agent.py`（`_skill_dirs`） | 追加企业技能目录一行 | 企业技能包加载 |
| `surfaces/gui/src/App.tsx`（或路由注册处） | 追加「表格助手」入口一行 | 大表哥前端入口 |
| `surfaces/gui/src-tauri/tauri.conf.json` | 品牌字段（productName/identifier/icon/updater） | 品牌与更新源 |
| `surfaces/gui/tailwind.config.js` + 全局 CSS | 引入 `enterprise/branding` 主题变量 | 换肤 |
| `pyproject.toml` | 追加企业依赖（如有） | 依赖管理 |

经验规则：挂载点冲突时，几行 diff 的三方合并几乎总能自动完成；
即使失败，人工处理一个挂载点 < 10 分钟。

**规则 C：禁止的做法。**
- ❌ 在上游文件中大段插入企业逻辑（应放 `enterprise/` 后 import）
- ❌ 重命名/移动上游文件（git 三方合并对 rename + 修改的组合最脆弱）
- ❌ 全局格式化上游代码（制造全文件 diff）
- ❌ fork 后直接改上游函数体实现企业行为（用配置注入或子类/包装）

### 3.3 流水线模板（开箱即用）

- `docs/enterprise/templates/sync-localized.yml`：完整可用版本（含冲突自动开 Issue、
  PR 正文禁止 squash 警告、定制存活冒烟 check run、凭据卫生处理）。
  由 `docs/enterprise/templates/init-enterprise-repo.sh` 自动安装到企业仓——
  建仓时跑一次即可，不用手抄。
- 首次建仓见 `docs/enterprise/DEPLOYMENT.md` 第 2 节：用 `git clone --bare` +
  `push --mirror` 建私有镜像，保留全部历史，使三方合并有正确的共同祖先
  （**不要用 GitHub 网页 Import 或下载 zip 重新 init**，会丢祖先导致每次同步全文件冲突）。

### 3.4 防覆盖的最后一道闸：企业定制冒烟测试（UPSTREAM_SYNC §3.4）

同步 PR 的 CI 必须包含**企业定制存活检查**
（`docs/enterprise/templates/test_enterprise_customization.py`）：

- 企业技能目录可被 SkillLoader 发现（catalog 含 excel-ai-analyst 等）
- 企业 Provider 配置可构建 client（mock 端点）
- 品牌字段断言：`tauri.conf.json` 的 productName/identifier/updater endpoints 为企业值
- 前端构建产物含企业入口（构建后 grep 关键标识）

任何一条失败 = 同步覆盖了定制，PR 自动标红，不可能"静默丢失定制"。

## 4. 与 PRD-029 的分工（重要：不重复造轮子）

| | PRD-029（trend #175–#180） | 本章（PRD-030 第 2 章） |
|---|---|---|
| 管什么 | 汉化版**怎么跟上游**（检测） | 企业版层面**怎么同步**（执行） |
| 输出 | 汉化 diff 报告（变更矩阵/工作量估算/优先级） | 三仓版本对应表 |
| 机制 | 检测脚本 + 监控清单 + 告警 | `sync-localized.yml` 流水线 + 冒烟测试 |

衔接点（本章 §5 检查清单第 2 项的展开，T1 评审要求的"外部引用展开"）：

- 确认"汉化版基线 tag ↔ 上游 tag 的对应关系"时，**直接引用 PRD-029 的同步报告**，
  不要自己再跑一遍检测。具体读
  `docs/plans/2026-10-17-upstream-sync-policy.md` §4.4"两层对照"的一句话结论
  （如"L2 已同步 L1 vX.Y.Z，本轮只需处理 L2 增量"），把结论填进 §1 的对应表即可。
- PRD-029 的报告归档在汉化仓 `docs/updates/`；无 P0 变更时不打扰，
  直接取最新一份报告的结论填表。
- 降级预案联动：若 PRD-029 报告注明"L2（中转层）连续 3 个月无更新，降级只看 L1"，
  本章对应表的"上游对应"列直接填 L1（`andrewyng/openworker`）的 tag。
  > 实况提示（2026-10-17）：L2 最后推送是 2026-07-25，已近 3 个月无更新，
  > PRD-029/T2 的首次检测运行大概率直接触发降级——这是符合策略的正常行为，不是 bug。
  > 填表时若报告已注明降级，"上游对应"列就填 L1 tag，不要再等 L2。

## 5. 检查清单（展开版）

- [ ] 企业版基线 = 汉化版**某 tag**（不是某次随手 commit）。
  为什么：tag 是发布流水线的触发器，也是版本对应表的锚点；
  随手 commit 无法追溯、无发布语义，下次同步时"基线是哪版"说不清。
- [ ] 已拿到 PRD-029 最新同步报告，确认汉化版基线 tag ↔ 上游 tag 的对应关系
  （读报告 §4.4 一句话结论，见 §4）。
- [ ] `sync-localized.yml` 已安装到企业仓（`templates/init-enterprise-repo.sh`），
  每日 03:35 UTC 节拍正常（看 Actions 页最近一次运行）。
- [ ] 三仓版本对应表已更新：企业版 vX.Y.Z ← 汉化版 tag ← 上游 tag
  （含汉化版 SHA、同步日期、同步人，模板见 §1）。
- [ ] 同步 PR 的冒烟测试（`test_enterprise_customization.py`）全绿，无定制被覆盖。
- [ ] 同步 PR 用 merge commit 合并（仓库设置中 `sync/*` 分支 PR 仅允许 merge commit）。

## 6. 来源与回指

本章引用的原文节（按出现顺序）：

1. `docs/enterprise/UPSTREAM_SYNC.md` §1 三仓关系 —— 本章 §2
2. `docs/enterprise/UPSTREAM_SYNC.md` §2 规则 A/B/C（目录隔离 + 挂载点） —— 本章 §3.2
3. `docs/enterprise/UPSTREAM_SYNC.md` §3.2 `sync-localized.yml` 机制 —— 本章 §3.1/§3.3
4. `docs/enterprise/UPSTREAM_SYNC.md` §3.3 版本与标签策略 —— 本章 §1
5. `docs/enterprise/UPSTREAM_SYNC.md` §3.4 冒烟测试 —— 本章 §3.4
6. `docs/enterprise/UPSTREAM_SYNC.md` §4 日常操作手册 —— 本章 §3.1（第 5–7 条）
7. `docs/enterprise/templates/sync-localized.yml` —— 本章 §3.3
8. `docs/enterprise/templates/test_enterprise_customization.py` —— 本章 §3.4
9. `docs/enterprise/templates/init-enterprise-repo.sh` —— 本章 §3.3
10. `docs/plans/2026-10-17-upstream-sync-policy.md` §4.4（PRD-029 同步报告两层对照） —— 本章 §4/§5

建议的回指文案（只给文案建议，不改原文；T5 定稿时由维护者决定是否加）：

- 在 `UPSTREAM_SYNC.md` §1 末尾加：
  > 本节已被企业定制 playbook 第 2 章《三仓同步》引用为三仓定义的依据
  >（`docs/plans/2026-10-17-playbook-ch2-sync.md` §2）。
- 在 `UPSTREAM_SYNC.md` §2 末尾加：
  > 本节规则 A/B/C 已被 playbook 第 2 章 §3.2 萃取为同步前的工程检查项。
- 在 `UPSTREAM_SYNC.md` §3.2 末尾加：
  > 流水线模板的安装与日常操作见 playbook 第 2 章 §3.1 / §3.3。
