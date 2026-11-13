# PRD-121/T4 开发记录：中文 README 首屏一行安装 + 演示示意图 + 带图指南（2026-11-14）

> trend issue #607（含 10-22 补充：带截图安装指南）。

## 交付

- README.md 首屏新增「一行安装（开箱即用）」节：命令块 + 演示 SVG + 指南链接；双语切换链接保持不动。
- docs/install-guide-zh.md：4 步带图安装指南（克隆→一行安装→默认中文配置→启动确认），命令可复制 + 常见问题。
- docs/assets/install-zh-{demo,step1..4}.svg：5 张终端风格示意图，诚实标注「示意图，非真实截图」，地址全占位（example.invalid/localhost）。
- tests/test_prd121_t4_readme_demo.py：6 例全绿（README 一行安装/双语链接完整/指南步骤配图/图片文件存在/占位扫描/无密钥）。

## 诚实声明

- 动图以静态示意图呈现（本环境无 GUI 截图能力）；PRD 原文「演示动图」按 SVG 示意图如实降级并在图内标注，不伪装真实截图。
- 图片为演示环境示意，零真实主机/密钥。

## PR 门槛合规核对（repos.yaml default_pr_gate）

| 门槛 | 落实 |
|---|---|
| require_integration_point | README 首屏=新用户入口（一行安装+演示）；指南链接挂在首屏 |
| no_missing_channel | 纯文档+SVG 本地文件，零新外部渠道；外链仅占位 |
| no_duplicate_module | 只改 README 首屏与新增指南/图，不动既有双语结构（PRD-122 T1 产物保持） |
| impl_requires_devlog | 本文件即开发记录 |

## 合规核对

- 示例全占位；T1 测试禁词扫描口径在文档测试中同样适用（拼接 needle）。
