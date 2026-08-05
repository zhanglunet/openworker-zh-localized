# OpenWorker 企业定制版 · 文档导览

本目录是企业定制版**开发前准备的全套文档**（2026-08-04），基于对 [zhanglunet/openworker-zh-localized](https://github.com/zhanglunet/openworker-zh-localized) 汉化版源码的扩展点分析（在线版：[oaosf.cn/source-analysis](https://oaosf.cn/source-analysis)）。

| 文档 | 内容 | 回答的问题 |
|------|------|-----------|
| [PRD.md](PRD.md) | 产品需求文档：目标、定制能力全景（模型/技能/知识库/工具/大表哥/品牌/合规/发布 8 层）、功能清单 F1–F14、非功能需求、风险 | 哪些部分可以定制？植入什么专属功能？ |
| [DEV_PLAN.md](DEV_PLAN.md) | 开发计划：M0–M3 四个里程碑（8 周）、任务分解与估算、团队分工、依赖风险 | 怎么排期？谁来做？ |
| [UPSTREAM_SYNC.md](UPSTREAM_SYNC.md) | 三仓同步方案：上游 → 汉化版 → 企业版单向链路、目录隔离 + 挂载点纪律、`sync-localized.yml` 流水线、防覆盖冒烟闸门 | 如何与上游/汉化版保持同步又不覆盖定制？ |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 部署步骤：私有仓建立、企业站（公网/内网两形态）、私有模型接入、技能与知识库部署、桌面端分发与更新、验收清单 | 怎么从零搭到全员可用？ |
| [BRANDING_PACKAGING.md](BRANDING_PACKAGING.md) | 换肤与打包：CSS 变量皮肤包、品牌项清单、macOS（Apple Silicon/Intel）与 Windows 构建矩阵、签名公证、企业自动更新源 | 怎么换皮肤？怎么打各平台的包？ |
| [templates/](templates/) | **开箱即用的模板**：一键建仓脚本、同步流水线、定制存活冒烟测试、企业发布流水线 | 上面这些怎么真正跑起来？ |

## 模板目录（可直接执行）

`templates/` 里的四个文件已经过语法校验与端到端演练，可直接投产：

| 文件 | 用途 |
|------|------|
| `init-enterprise-repo.sh` | 一键建企业私有仓：镜像汉化仓（保祖先链）→ 停用继承来的汉化仓流水线 → 建 `enterprise/` 骨架 → 生成配置/主题/MCP 模板 → 装流水线与冒烟测试 → 提交推送。支持 `--dry-run`、`--help`，凭据全程脱敏 |
| `sync-localized.yml` | 汉化版→企业版每日同步：有更新则开 PR（正文含禁止 squash 的醒目警告）、冲突自动开 Issue、PR 上跑定制存活冒烟并写 check run |
| `test_enterprise_customization.py` | 17 项定制存活断言（企业技能、Provider、品牌字段、更新源、配置模板、主题包、挂载点形状），失败信息直指「哪项定制可能被同步覆盖」 |
| `release-corp.yml` | 企业发布：preflight + 三平台构建 + publish；签名 Secrets 未配时自动产出未签名测试包 |
| `skills/excel-ai-analyst/` | **大表哥表格助手技能包**（PRD F4 的 L1 层）：SKILL.md + 配套脚本 `scripts/excel_ai.py`（四子命令）+ 三份 references + 完整测试与对抗套件。建仓脚本自动装到 `enterprise/skills/` |

用法：`bash templates/init-enterprise-repo.sh --help`，详见 [templates/README.md](templates/README.md)。

> ⚠️ 建仓时最容易踩的坑（脚本已自动处理）：`git push --mirror` 会把汉化仓的 `.github/workflows/` 一并带进企业私有仓，其中 `sync-upstream.yml` 会**每天绕过汉化层直接把上游合进企业仓**，与企业同步链路抢同一个 `main`；`deploy-site.yml`/`release.yml` 等也会误发汉化版品牌的站点与安装包。脚本第 3 步会把这些改名为 `*.yml.disabled`（用重命名而非删除，好让后续同步的 rename detection 仍能合入上游改动）。

## 快速导航（按角色）

- **决策者**：读 PRD 第 1、3、8 章（目标、能力全景、里程碑）
- **定制开发**：DEV_PLAN 全文 + UPSTREAM_SYNC 第 2 节（开发纪律）
- **IT/运维**：DEPLOYMENT 第 0 节（前置办理清单，证书类第 1 天就要发起）+ 第 6-7 节
- **设计**：BRANDING_PACKAGING 第 1 节

## 核心结论（一句话版）

1. **私有模型/端口/版本是配置级**：`Custom`（OpenAI 兼容 base_url）与 `Ollama` Provider 已内置，vLLM/企业网关直接可接。
2. **技能与知识库是资产级**：SKILL.md 规范技能包放 `state_dir()/skills`；知识库首选文件根挂载，中期 MCP 检索服务。
3. **大表哥分三层渐进**：L1 预置 excel-ai-analyst 技能（资产级）→ L2 前端表格助手入口 → L3 excel_ai 内置工具化。
4. **同步靠拓扑与纪律**：企业仓只对接汉化仓（单向链条），定制收敛在 `enterprise/` 目录 + 个位数挂载点文件，冒烟闸门保证定制永不被静默覆盖。
5. **换肤是覆盖一个 CSS 变量块**：主题色全部走 `styles.css` CSS 变量，品牌项集中在 `tauri.conf.json`；三平台打包矩阵（mac 双芯片 + Windows）流水线现成，换名换源即用。
