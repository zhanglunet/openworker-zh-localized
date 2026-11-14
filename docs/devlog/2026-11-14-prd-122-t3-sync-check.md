# PRD-122/T3 开发记录：章节同步检查（2026-11-14）

> trend issue #611。10-21 批遗留补齐。

## 交付

- scripts/check_readme_sync.py：比对两份 README 的 H2 结构（数量一致+顺序一一对应+CANON 中英同节登记表 15 对全覆盖）；不一致 exit 1 报具体节位。零依赖标准库。
- .github/workflows/i18n-check.yml：既有翻译校验 job 内新增「中英 README 章节同步检查」步（复用同一 checkout，不另起 workflow——与 PRD-084/T3 术语锁定划界：本步管结构同步，不管术语/链接）。
- tests/test_prd122_t3_sync_check.py：4 例全绿（当前通过/漂移检出（monkeypatch 注入）/self-test exit 0/workflow 步存在）。

## PR 门槛合规核对（repos.yaml default_pr_gate）

| 门槛 | 落实 |
|---|---|
| require_integration_point | 接入点=i18n-check CI job（README*.md 改动即触发） |
| no_missing_channel | 纯本地标准库检查，零网络零新渠道 |
| no_duplicate_module | 复用 i18n-check workflow 容器不另起 workflow；与术语锁定/链接检查划界明确 |
| impl_requires_devlog | 本文件即开发记录 |

## 合规核对

- 零网络；示例全占位。
