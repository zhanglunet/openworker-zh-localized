# PRD-122/T5 开发记录：验收（2026-11-14）

> trend issue #613。验收口径：CI 绿，抽查 3 节内容对应。

## 交付

- tests/test_prd122_t5_acceptance.py：4 例全绿（本链合计 15 例：T2 3+T3 4+T4 4+T5 4）。
  - 抽查节①一行安装/One-line Install：命令、演示图、--check 双语齐备。
  - 抽查节②下载与介绍站/Downloads：语义对应（站点 oaosf.cn、Release v0.1.7-zh 双语齐备；源码入口措辞可异——zh 用 website/README.md，en 用 website/）。
  - 抽查节③常见问题/FAQ：三级子锚点数量 1:1。
  - CI 检查器 exit 0 + 本链 T2/T3/T4 测试子进程复跑全绿。

## PR 门槛合规核对（repos.yaml default_pr_gate）

| 门槛 | 落实 |
|---|---|
| require_integration_point | 抽查覆盖双语读者三类入口（安装/下载/FAQ） |
| no_missing_channel | 纯本地测试，零网络 |
| no_duplicate_module | 只消费本链产物，不新增模块 |
| impl_requires_devlog | 本文件即开发记录 |

## 合规核对

- 示例全占位；措辞差异按语义对应口径断言（不伪装逐字一致）。
