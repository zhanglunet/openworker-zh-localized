# OpenWorker 企业定制版 · 开发计划

- 版本：v1.0 · 2026-08-04
- 需求来源：[PRD.md](PRD.md)（F1–F14）
- 周期：8 周（3 名开发 + 1 名 IT 协同的基准配置；单人全职则乘以 ~2.5）

---

## 1. 里程碑总览

```
第1周   M0 地基     私有仓 + 同步流水线 + 冒烟闸门 + 企业站雏形
第2-3周 M1 内测版   P0 全部落地 → 0.x-corp.1（内部试用）
第4-5周 M2 试点版   P1 落地 → 试点部门推广
第6-8周 M3 正式版   P2 落地 + 硬化 → 全员发布
贯穿    每日上游同步消化（M0 后自动化，冲突随到随处理）
```

## 2. M0 · 地基（第 1 周）

| # | 任务 | 需求 | 产出/验收 | 估算 |
|---|------|------|-----------|------|
| 0.1 | 镜像建私有仓 `<corp>/openworker-enterprise`（`git push --mirror`，保共同祖先） | — | 私有仓可克隆，历史完整 | 0.5d |
| 0.2 | 建 `enterprise/` 目录骨架 + `sync-localized.yml` + `release-corp.yml` 空跑 | — | 手动触发同步显示 already-synced | 1d |
| 0.3 | 企业定制冒烟测试框架（`enterprise/tests/`，接入 CI 必过） | — | 技能加载/品牌字段/Provider 构建三类断言跑通 | 1.5d |
| 0.4 | 证书流程启动：Apple Developer 组织账号、Windows 签名证书申请（外部周期长，第 1 天就发起） | F6 | 申请提交回执 | 0.5d |
| 0.5 | 企业站雏形：`website/` 品牌化副本部署到企业域名（形态 A 或 B） | F14 | 企业域名可访问占位站 | 1.5d |
| 0.6 | Tauri updater 企业密钥对生成入库 Secrets | F6 | 密钥对生成，公钥待写入配置 | 0.5d |

**出口条件**：同步流水线演练一次真实同步（汉化仓当日有提交时）PR 自动出现，冒烟闸门生效。

## 3. M1 · 内测版（第 2-3 周，P0）

| # | 任务 | 需求 | 关键改动点 | 估算 |
|---|------|------|-----------|------|
| 1.1 | 私有模型接入验证：Custom Provider 连企业 vLLM/网关（base_url + 端口 + 模型名），Ollama 备选路径验证 | F1 | 纯配置（`coworker/providers/registry.py` 的 `_build_custom`/`_build_ollama` 已支持） | 1d |
| 1.2 | 模型能力登记：企业模型上下文窗口/工具调用能力入能力矩阵 | F1 | `coworker/providers/matrix.py`、`capabilities.py`（挂载点小改） | 1d |
| 1.3 | 配置预置：首启复制 `enterprise/config/config.default.toml` → `~/.config/coworker/config.toml`；审批策略、命令白名单定稿 | F2 | 桌面壳首启逻辑（挂载点）+ 配置文件 | 2d |
| 1.4 | 企业技能包 v1：excel-ai-analyst（大表哥 L1）+ ≥5 个企业 SOP 技能编写与评测。含**首启拷贝逻辑开发**（技能无包内分发通道：PyInstaller 不带数据目录，需桌面壳/后端首启把打包资源拷入 `state_dir()/skills`） | F3, F4 | `enterprise/skills/`（SKILL.md 规范）+ 首启逻辑挂载点 | 3d |
| 1.4b | 语音输入内网化：预置/镜像 whisper 模型（默认从 huggingface 拉英文 base 模型，`stt/src/lib.rs` DEFAULT_MODEL_URL），评估换中文模型 | F2 | `stt/` 挂载点小改 + 模型资产 | 1d |
| 1.5 | 大表哥 L2：前端「表格助手」入口。快赢路径：`SessionIntro.tsx` 加一张任务卡（onPrefill 预填提示词触发技能，半天）；完整路径：App.tsx 的 surface 联合类型 + 渲染链加 `sheets` 分支 + `Sidebar.tsx` 回调（参照 IntegrationsView 模式）新整页面板 | F4 | `surfaces/gui/src/`（无路由库，surface 状态机挂载） | 3d |
| 1.6 | 品牌换肤：`enterprise/branding/theme.css`（亮/暗）、图标全套（`tauri icon` 生成）、productName/identifier/publisher、DMG 背景、Info.plist/lib.rs 品牌词 | F5 | 见 BRANDING_PACKAGING.md 清单 | 2d |
| 1.7 | 企业更新源：updater endpoints/pubkey 改企业值，`make_update_manifest.py` 出 `latest-corp.json`，托管打通 | F6 | `tauri.conf.json` + `release-corp.yml` | 2d |
| 1.8 | 三平台首构建：macOS arm64/x64 + Windows 出包（可暂未签名），内测群分发 | F5/F6 | tag `v0.x-corp.1` 走 `release-corp.yml` | 1d |
| 1.9 | 内测反馈通道与问题清单机制 | — | Issue 模板 + 每日 triage | 0.5d |

**出口条件**：PRD 3.5 验收场景（表格分析全流程）+ 断公网对话验收通过；内测 ≥10 人安装成功。

## 4. M2 · 试点版（第 4-5 周，P1）

| # | 任务 | 需求 | 关键改动点 | 估算 |
|---|------|------|-----------|------|
| 2.1 | 知识库 v1：同步盘挂载规范 + 文件根接入指引 + 常用检索技能 | F7 | `coworker/roots.py` 机制复用，零代码 | 2d |
| 2.2 | 企业 CLI MCP：首个企业 CLI 封装 stdio MCP server + 预置注册 | F8 | `enterprise/mcp/corp-cli/` | 3d |
| 2.3 | 目录白名单：Provider/连接器目录过滤（隐藏海外 SaaS 入口） | F9 | `coworker/catalog.py` / `connectors/descriptors.py` 挂载点 | 2d |
| 2.4 | 审计外发：audit 日志增加企业 SIEM sink（内网 HTTP/syslog） | F10 | `coworker/audit.py` 挂载点 + `enterprise/` 实现 | 2d |
| 2.5 | 签名公证接入：Apple 证书/Notary Key 到位后接入 `release-corp.yml`，出首个签名公证版 | F6 | Secrets 配置（照 `docs/release-signed-updates.md`） | 1d |
| 2.6 | 企业站正式版：下载页（三平台 + SHA-256）、使用指南、技能包说明、更新日志页 | F14 | `website/` 品牌副本 | 3d |
| 2.7 | 试点部门推广（1-2 个部门），培训材料 + 反馈周会 | — | 试点 ≥30 人 | 贯穿 |

**出口条件**：试点部门周活跃 ≥60%；同步流水线在此期间至少消化 2 次上游更新且冒烟全绿。

## 5. M3 · 正式版（第 6-8 周，P2 + 硬化）

| # | 任务 | 需求 | 估算 |
|---|------|------|------|
| 3.1 | 大表哥 L3：`excel_ai.py` 注册为内置工具（`coworker/tools/` 模板参照现有工具），报告落会话产物 | F11 | 4d |
| 3.2 | 知识库 v2：企业知识库 MCP 检索服务（对接 Confluence/语雀/自建 RAG，服务端权限校验） | F12 | 5d |
| 3.3 | 首个企业内部系统连接器（OA/工单，descriptor 模式开发 + 审批风险分级）🟡 模板与接入指南已交付（[CONNECTOR_GUIDE.md](CONNECTOR_GUIDE.md)），**剩下的 ~2d 卡在拿到内网接口文档**：拿到后走路线 A 是写一份 `api.json`，走路线 B 是填 `CONFIG` + `CORP_TOOLS` 加 5 行挂载点 | F13 | 5d（已完成 3d） |
| 3.4 | Windows 代码签名接入（证书到位后） | F6 | 1d |
| 3.5 | 性能与稳定性硬化：冷启动、超大表引导、断网降级提示 | NFR | 3d |
| 3.6 | 安全审查：网络出口审计（抓包验证 G2）、更新链路攻击面复查、密钥轮换预案 | NFR | 2d |
| 3.7 | 全员发布：分发方案执行（企业站 + MDM）、IT 运维手册、回滚演练 | — | 2d |

**出口条件**：PRD G1–G5 全部达标；上线验收清单（DEPLOYMENT.md 第 7 节）逐项通过。

## 6. 长期例行（M3 后）

- **同步节拍**：自动同步 PR 随到随审（预算每周 ≤2h，超预算即触发挂载点瘦身复盘）
- **技能包迭代**：企业技能独立版本号，每两周一版
- **上游大版本**：冻结-集中合并-冒烟流程（UPSTREAM_SYNC.md 第 4 节）
- **季度安全复查**：密钥轮换、依赖审计、审计日志抽查

## 7. 团队分工建议

| 角色 | 职责 |
|------|------|
| 后端开发（1） | Provider/能力矩阵、MCP、审计外发、连接器、excel_ai 工具化 |
| 前端开发（1） | 换肤、表格助手入口、目录白名单 UI、企业站 |
| 全栈/DevOps（1） | 同步与发布流水线、打包签名、更新托管、冒烟闸门 |
| IT 协同（0.5） | 证书办理、MDM 分发、内网托管、SIEM 对接 |
| 业务专家（兼职） | 企业 SOP 技能编写与评测、试点组织 |

## 8. 关键依赖与风险缓冲

| 依赖/风险 | 影响面 | 缓冲策略 |
|-----------|--------|---------|
| Apple 证书办理周期（外部，1-2 周+） | M2 签名版 | M0 第 1 天发起；M1 用未签名包 + 右键打开/MDM 白名单过渡 |
| 企业模型 API 兼容性（工具调用/流式支持不全） | F1 核心体验 | M1 第 1 天做兼容性测试矩阵（chat、tool-call、stream、长上下文）；不达标项反馈 AI 平台组 |
| 上游 Beta 期大改（如目录重构） | 同步成本 | 挂载点纪律 + 冒烟闸门；重构周冻结同步集中处理 |
| anp.asia 大表哥资产授权/交付形态 | F4 | L1 技能层不依赖外部页面可先行；L2 内嵌页面作为增强项解耦排期 |
| 试点反馈导致需求变更 | M3 范围 | P2 需求在 M2 末重新排序，允许换入换出 |
