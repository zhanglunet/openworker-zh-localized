# PRD-030/T5：企业定制 playbook 定稿与换肤走查报告

> trend #185。T5 两件事：**定稿**（三章一致性 + 回指文案写回）与**走查**
> （桌面推演一次完整换肤）。
>
> **诚实声明（T1 大纲附则要求）**：本次为**桌面推演**，非真实客户交付。
> 无真实企业客户、无真实签名证书、无真实构建运行；所有"执行"均为按文档
> 逐步推演 + 对仓库现状的 API 核对。时间均为估算。

## 0. 推演设定

- 模拟企业：**Acme（艾克米科技）**，`CORP_ID=acme`，`CORP_NAME=AcmeWorker`，
  应用名"艾克米智能助手"，Bundle ID `com.acme.openworker`。
- 汉化版基线：`v0.1.7`（2026-10-17 当天 main 上 `tauri.conf.json` 的 `version`，
  已用 API 核对）。
- 走查方式：第 1 章按 §0→§5 逐步推演（每步记录动作/估算耗时/卡点）；
  第 2、3 章走关键路径（输入输出衔接、检查清单可执行性），不重复第 1 章已覆盖的细节。

## 1. 第 1 章走查（换肤打包）

| 步骤 | 推演动作 | 估算耗时 | 卡点/缺口 |
|---|---|---|---|
| §0 输入 | 确认基线 tag `v0.1.7`（API 核对 `tauri.conf.json`：productName `OpenWorker 中文版`、identifier `com.openworker.desktop.zh`、version `0.1.7`，与文档一致）；列出品牌素材包清单 | 0.5h（含素材收集等待） | 无 |
| §1 产品决策 | 定 Bundle ID `com.acme.openworker`；定隐藏 Cloud 入口 | 0.5h（主要是等人拍板） | **有**：`Sidebar.tsx` 路径写错（实际在 `components/` 下）；`cloud_*` 键位置不明（见修订 1、2） |
| §2.1 主题 | 按示例写 `enterprise/branding/theme.css`，核对变量名 | 1–2h | 无：`--accent`/`--accent-soft`/`--solid`/`--on-solid` 四个变量在 `styles.css` 里都存在（API 核对） |
| §2.2 应用名/Bundle ID | 改 `tauri.conf.json` 5 个字段 | 0.5h | 无：`wix.language: ["zh-CN"]` 已在 main 上（文档"本仓库已修复"属实） |
| §2.3 图标 | `npx tauri icon` 生成全套 | 0.5h | 无 |
| §2.4 文案 | 替换品牌词；`humanize.ts` 补译抽查 | 2–4h | **有**：三个文件缺路径前缀（见修订 3）；`lib.rs` 内 5 处 "OpenWorker"（API 核对，与文档"替换其中字样"一致） |
| §2.5 免责声明 | 定稿文案，配 `branding.json` | 0.5h | 无 |
| §3.1 打 tag | `git tag corp-v0.1.7`，核对 version 一致规则 | 0.2h | 无：与企业仓真实 tag（`corp-v0.1.9`）格式一致 |
| §3.2 preflight | CI 自动跑 | ~10min | 无：5 挂载点默认值与 main 现状一致（已核对） |
| §3.3 构建 | CI 矩阵三平台 | 30–60min/平台 | 无：`packaging/` 下 5 个脚本/配置都存在（API 核对）；`macos-15-intel` label 存在（T4 评审已修掉无依据的日期） |
| §3.4 签名 | 首次配证书 | 1–2 天（含等 Apple/CA） | 关键路径：证书办理周期 1–2 周，文档 §1 前置清单已要求提前启动 |
| §3.5 更新源 | 改 endpoints + pubkey，`make_update_manifest.py` | 1h | 无：脚本存在（API 核对） |
| §4 验证清单 | 7 项逐项过 | 0.5–1 天 | 无 |
| §5 记录单 | 填写归档 | 0.2h | 无 |

**首次换肤总估算：约 3–5 人日**（含等证书、等拍板的时间；不含 Apple Developer 账号申请的 1–2 周前置）。

## 2. 第 2 章走查（关键路径）

- 输入衔接 ✓：换肤记录单的"汉化版基线 tag"字段就是本章 §1 对应表的输入，链条闭合。
- 版本口径 ✓：`0.1.7-corp.3` 是 version（T5 已加注"非 tag"），tag 口径 `corp-vX.Y.Z`
  与第 1 章 §3.1、OWE 真实 tag 一致。
- merge-commit-only ✓：汉化仓 PR #2 的合并提交确为单 parent（squash），"重放冲突"
  教训属实，规则有真实依据。
- PRD-029 衔接 ✓：§4 的"读 §4.4 一句话结论填表"可执行；引用的政策文档路径
  `docs/plans/2026-10-17-upstream-sync-policy.md` 在 main 上存在。
- 未真实跑 `init-enterprise-repo.sh`（推演限制，已注明）。

## 3. 第 3 章走查（关键路径）

- 前置清单 ✓：6 项齐全，证书 1–2 周是关键路径，文档已要求提前启动。
- §2.2 Secrets/Variables 清单 ✓：与 `release-corp.yml` 头部注释的变量名一致
  （`CORP_NAME`/`CORP_ID`/`CORP_UPDATE_BASE_URL`）。
- §2.3 A1–A5 ✓：步骤具体到点击路径；A1 的"Secret 名写错只打 notice 绿灯通过"
  是真实坑，文档已写明；25 MiB 上限与 Workers 静态资源限制一致。
- 两条红线 ✓：`openworker-cn-site` 的命名冲突风险真实存在（企业仓由汉化仓镜像而来）。
- 回滚 ✓：`latest-<corp>.json` 回指 + "不要删旧文件"闭环。
- 未真实跑发布流水线（推演限制，已注明）；§5 的 T5 实演事项已列出。

## 4. playbook 修订清单（走查输出，T1 附则硬要求 ≥1 处）

以下 3 处已在本 PR 直接修进第 1 章正文：

1. **第 1 章 §1**：`Sidebar.tsx` → `surfaces/gui/src/components/Sidebar.tsx`；
   补充说明 `cloud_*` 键在**运行时**应用 state 目录的 `config.toml` 里，
   仓库内无此文件。原因：推演中按文档路径找不到文件，且该组件内无 `cloud_*`
   引用（API 全仓库核对），`cloud_relay_ws_url` 只出现在运行时配置语境
   （`DEPLOYMENT.md` §4.2 注释）。
2. **第 1 章 §2.4**：三个文件补全路径
   （`surfaces/gui/src/components/Sidebar.tsx`、`surfaces/gui/src/App.tsx`、
   `surfaces/gui/src/components/Onboarding.tsx`）。原因：`App.tsx` 在
   `src/` 根目录而非 `components/` 下，无路径会找错。
3. **第 1 章 §4**："默认 `config.toml`" → "运行时 `config.toml`
  （应用 state 目录，非仓库文件）"。原因同修订 1。

**企业文档侧待办**（超出本 PR"只加引用行"范围，不改，记在此处供维护者处理）：

4. `docs/enterprise/DEPLOYMENT.md` §6 的"打 tag `v0.1.7-corp.1`"与 playbook
   的 `corp-vX.Y.Z` 口径不一致（后者与企业仓真实 tag、流水线白名单一致，
   应为新口径）。建议企业文档维护者更新该行。

## 5. 定稿结论

- **一致性**：术语（汉化版/汉化仓/中转层）、tag（`corp-vX.Y.Z`）/version
  （`X.Y.Z-corp.n`）口径、章节交叉引用（记录单→第 2 章、对应表→第 3 章）
  三章一致；T2–T4 评审修过的不一致未复发。
- **回指写回**：`BRANDING_PACKAGING.md`（顶部 1 行）、`UPSTREAM_SYNC.md`
  （§1/§2/§3.2 末尾各 1 行）、`DEPLOYMENT.md`（§3/§6/§7 顶部各 1 行）、
  `templates/release-corp.yml`（头部注释 2 行）——只加引用行，未改原文实质。
- **走查**：桌面推演完成，3 处修订已修进正文，1 处企业文档侧待办已记录。
  PRD-030 五个任务（T1–T5）至此全部落地。
