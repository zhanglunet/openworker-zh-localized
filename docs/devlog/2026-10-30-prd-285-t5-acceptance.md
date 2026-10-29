# PRD-285/T5 验收试运行记录：中文技能包升级快照全流程演练 + 抽查 + 本地断言 + 文档无密钥

- 日期：2026-10-30
- trend issue：[zhanglunet/trend#1430](https://github.com/zhanglunet/trend/issues/1430)
- 中央 PRD：`trend/adopted/PRD-285-owzh-skillpack-upgrade-snapshot.md`
- 全链：T1 #1426（设计 `docs/plans/2026-10-29-prd-285-skillpack-upgrade-snapshot.md`）→ T2 #1427（`skillpack_snapshot.py` 快照/还原/抽查）→ T3 #1428（`spotcheck_archive.py` 抽查落档+升级流程）→ T4 #1429（本地断言）→ 本任务 T5
- 验收测试：`tests/test_prd285_acceptance.py`（8 例，.venv/bin/python -m pytest）
- 状态：验收通过；实现类 PR 只开不合并，等用户 review

## 验收标准逐条核验（issue #1430）

### 1. 升级可回滚（全链通过）— 通过

虚构中文技能包全流程演练：take_snapshot（逐文件 sha256）→ 模拟升级后包面损坏
（content 改而指纹仍旧）→ spot_check 检出 failed>0 → upgrade_flow_with_check
自动回滚 → restore 回到旧包（内容逐文件与快照一致）。

### 2. 红线断言全过 — 通过

- 升级通过路径：包面与快照一致 → 抽查全过 → 不回滚
- 抽查记录：spotcheck-record-v1 六字段 JSONL 落档可读
- 指纹校验：篡改指纹 restore 抛错（fail-close）
- 本地处理：两模块零网络原语（AST/源码双断言）
- 确定性：同输入快照逐字节一致

### 3. 文档无密钥 — 通过

交付面（skillpack_snapshot.py/spotcheck_archive.py/验收测试）密钥形态扫描零命中。

## 运行记录

`.venv/bin/python -m pytest tests/test_prd285_acceptance.py -q` → 8 passed。

## 结论

PRD-285 全链（T1–T5）验收通过；只开不合并，等用户 review。
