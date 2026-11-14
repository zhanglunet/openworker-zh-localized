# PRD-122/T2 开发记录：中英 README 互链（2026-11-14）

> trend issue #610。10-21 批遗留补齐。

## 交付

- tests/test_prd122_t2_crosslink.py：3 例全绿（zh 顶部链 en / en 顶部链 zh / 双文件存在且语言正确）。

## 偏差核验（如实声明）

- 互链在 T1（docs/prd-122-t1-readme-en，已合并）已交付：两份 README 顶部均有「中文 | English」切换行。本单为验收钉值测试，零新增文档改动——不重复劳动，只把验收标准锁进测试。

## PR 门槛合规核对（repos.yaml default_pr_gate）

| 门槛 | 落实 |
|---|---|
| require_integration_point | 接入点=两份 README 顶部切换行（新读者第一眼） |
| no_missing_channel | 纯测试，零新外部渠道 |
| no_duplicate_module | 不重复 T1 的互链改动，只钉验收 |
| impl_requires_devlog | 本文件即开发记录 |
