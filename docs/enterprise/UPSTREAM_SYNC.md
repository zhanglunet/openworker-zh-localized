# 三仓同步方案：上游 → 汉化版 → 企业定制版

- 版本：v1.0 · 2026-08-04
- 目标：企业私有仓**持续、近实时**地获得上游功能更新与汉化版界面更新，同时**永不覆盖**企业定制的功能与界面。

---

## 1. 三仓关系

```
andrewyng/openworker (公开, 上游)            ──┐ 每日 01:35 UTC 定时
        │                                     │ sync-upstream.yml
        ▼  merge（已有流水线，冲突自动开 Issue）    │ 自动 PR，人工合并
zhanglunet/openworker-zh-localized (公开, 汉化版)
        │
        ▼  merge（新增流水线 sync-localized.yml，同款机制）
<corp>/openworker-enterprise (私有, 企业定制版)
        └── 企业站（公开或内网）+ 企业发布流水线
```

**单向逐级流动**：上游 → 汉化版 → 企业版。企业版不需要直接对接上游——汉化版已经每日消化上游（含冲突处理与中文文案维护），企业版只需消化汉化版，拿到的是"上游功能 + 中文界面"的合成结果。这样每级只处理一类冲突：

| 同步链路 | 冲突类型 | 由谁处理 |
|---------|---------|---------|
| 上游 → 汉化版 | 英文文案改动 vs 中文文案（前端 tsx、Tauri lib.rs） | 汉化版维护者（现有 `sync-upstream.yml` 已运转） |
| 汉化版 → 企业版 | 汉化版文件改动 vs 企业挂载点小改 | 企业定制团队（冲突面被设计压到个位数文件） |

> 为什么不让企业版同时拉上游和汉化版两个 remote？两条链路会把同一批上游提交以不同合并历史送达，制造重复冲突。单链条 + git 三方合并（共同祖先清晰）是冲突最小的拓扑。

## 2. 「不覆盖定制」的工程保障：目录隔离 + 挂载点

同步安全的根本不在 git 技巧，而在**改动面设计**。企业版全部定制遵守两条规则：

### 规则 A：新增优先，独立目录

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

### 规则 B：改动收敛到"挂载点"

确实要动上游文件时，只加**一行注册/一处 import**，不重排不重写。预期挂载点清单（每个文件的 diff 控制在几行内）：

| 挂载点文件 | 改动 | 目的 |
|-----------|------|------|
| `coworker/providers/registry.py` | DESCRIPTORS 追加企业 Provider 条目（一行 `_compat(...)` 即可，仿 stepfun 条目） | 预置私有模型入口 |
| `coworker/providers/matrix.py` | MATRIX 追加企业模型能力条目（键为 `custom:<模型>` 完整路由 id） | 避免能力被启发式降级 |
| `coworker/connectors/descriptors.py` | 追加一段"企业子包加载 + 白名单过滤"（仿现有 `connectors/experimental/` 的加载段），企业连接器本体放 `enterprise/connectors/` | 目录定制与企业连接器 |
| `coworker/agent.py`（`_skill_dirs`） | 追加企业技能目录一行 | 企业技能包加载 |
| `surfaces/gui/src/App.tsx`（或路由注册处） | 追加「表格助手」入口一行 | 大表哥前端入口 |
| `surfaces/gui/src-tauri/tauri.conf.json` | 品牌字段（productName/identifier/icon/updater） | 品牌与更新源 |
| `surfaces/gui/tailwind.config.js` + 全局 CSS | 引入 `enterprise/branding` 主题变量 | 换肤 |
| `pyproject.toml` | 追加企业依赖（如有） | 依赖管理 |

> 经验规则：挂载点冲突时，几行 diff 的三方合并几乎总能自动完成；即使失败，人工处理一个挂载点 < 10 分钟。这就是 PRD 中 G4（每次同步 ≤2h）的依据。

### 规则 C：禁止的做法

- ❌ 在上游文件中大段插入企业逻辑（应放 `enterprise/` 后 import）
- ❌ 重命名/移动上游文件（git 三方合并对 rename + 修改的组合最脆弱）
- ❌ 全局格式化上游代码（制造全文件 diff）
- ❌ fork 后直接改上游函数体实现企业行为（用配置注入或子类/包装）

## 3. 同步流水线实现

### 3.1 现有：上游 → 汉化版（已运转）

`.github/workflows/sync-upstream.yml`：每日 01:35 UTC（+ 手动触发），fetch `upstream/main` → 若有新提交则在 `sync/upstream-main` 分支 merge → 成功则重新生成站点报告并开 PR 人工审阅；冲突则自动开 Issue「上游同步需要人工解决冲突」并给出本地处理命令。**企业版直接复用此模式。**

### 3.2 新增：汉化版 → 企业版 `sync-localized.yml`

放在企业私有仓，机制与 3.1 同款，仅换 remote 与分支名：

```yaml
name: Sync localized OpenWorker
on:
  schedule:
    - cron: "35 3 * * *"    # 每日 03:35 UTC，错开汉化版同步 2 小时，
                            # 让当天上游变更先经汉化版消化
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write
  issues: write

jobs:
  sync-localized:
    if: github.actor != 'github-actions[bot]'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0, token: "${{ secrets.GITHUB_TOKEN }}" }
      - name: Configure git identity
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
      - name: Fetch localized repo
        run: |
          git remote add localized https://github.com/zhanglunet/openworker-zh-localized.git
          git fetch localized main --tags
      - name: Check whether localized has new commits
        id: diff
        run: |
          if git merge-base --is-ancestor localized/main HEAD; then
            echo "changed=false" >> "$GITHUB_OUTPUT"
          else
            echo "changed=true" >> "$GITHUB_OUTPUT"
            echo "localized_sha=$(git rev-parse --short localized/main)" >> "$GITHUB_OUTPUT"
          fi
      - name: Merge localized into sync branch
        if: steps.diff.outputs.changed == 'true'
        id: merge
        continue-on-error: true
        run: |
          git switch -c sync/localized-main
          git merge --no-edit localized/main
      # 冲突 → 自动开 Issue（同 sync-upstream.yml 的 github-script 段，
      # 提示保留 enterprise/ 目录与挂载点定制）
      # 成功 → peter-evans/create-pull-request 开 PR，人工审阅后合并
```

要点：

- **永不直推 `main`**：同步永远走 PR，企业 CI（含企业冒烟用例，见 3.4）通过 + 人工确认后合并。"实时"由每日节拍 + 随时手动触发保障；比直推安全得多，延迟上限 24h，满足 G4。
- **同步 PR 必须用 merge commit 合并，禁止 squash / rebase 合并**：squash 会把合并结果压成单亲提交，被同步方的 tip 从此不再是本仓祖先——下一次同步会把已解决过的冲突**全部重放**。这不是理论风险：汉化仓的上游同步 PR #2 就因 squash 导致 `upstream/main` 脱离祖先链，实测下次合并会在约 20 个文件重放冲突（registry.py、manager.py、tauri.conf.json、App.tsx 等）。企业仓应在 GitHub 仓库设置中对 `sync/*` 分支的 PR 仅允许 merge commit。
- **冲突兜底**：merge 失败自动开 Issue，附带本地解决命令；`main` 不受影响。
- 私有仓访问公开汉化仓无需额外凭据（公开仓可匿名 fetch；若汉化仓将来转私有，配一个只读 PAT 到 `secrets`）。

> **汉化仓待办（影响企业链路的上游卫生）**：因上述 PR #2 squash，汉化仓需做一次性祖先链修复——在 `sync/upstream-main` 上 `git merge upstream/main`，人工把这批已知冲突再解一次，以 **merge commit** 合入 `main`；此后 `merge-base --is-ancestor` 判定恢复正常，企业链路拿到的将是干净的合并历史。

### 3.3 版本与标签策略

- 企业版本号：`<汉化版基线>-corp.<n>`，如 `0.1.7-corp.3`；tag 触发企业发布流水线
- 每次合并同步 PR 后，在 PR 描述记录消化到的汉化版 SHA，便于追溯"企业版含上游哪一天的功能"

### 3.4 防覆盖的最后一道闸：企业定制冒烟测试

同步 PR 的 CI 必须包含**企业定制存活检查**（放 `enterprise/tests/`）：

- 企业技能目录可被 SkillLoader 发现（catalog 含 excel-ai-analyst 等）
- 企业 Provider 配置可构建 client（mock 端点）
- 品牌字段断言：`tauri.conf.json` 的 productName/identifier/updater endpoints 为企业值
- 前端构建产物含企业入口（构建后 grep 关键标识）

任何一条失败 = 同步覆盖了定制，PR 自动标红，不可能"静默丢失定制"。

## 4. 日常操作手册

| 场景 | 操作 |
|------|------|
| 每日例行 | 无事可做；有更新时收到同步 PR，看 CI 绿灯后合并 |
| 同步 PR 冲突 | 按 Issue 中命令本地 merge，冲突处优先保留 enterprise 挂载点行 + 接受汉化版其余改动，push 到 `sync/localized-main` 更新 PR |
| 想立即拿到某个上游修复 | 先在汉化仓手动触发 `sync-upstream.yml` 并合并，再在企业仓手动触发 `sync-localized.yml` |
| 企业定制开发 | 正常在企业仓 feature 分支开发，遵守第 2 节规则 A/B/C，与同步互不干扰 |
| 上游大版本重构 | 冻结同步 → 在 `sync/localized-main` 上集中处理 → 企业冒烟全绿后合并（预算 1-2 天） |

## 5. 首次建仓步骤

见 [DEPLOYMENT.md](DEPLOYMENT.md) 第 2 节——用 `git clone --bare` + `push --mirror` 建私有镜像，保留全部历史，使三方合并有正确的共同祖先（**不要用 GitHub 网页 Import 或下载 zip 重新 init**，会丢祖先导致每次同步全文件冲突）。
