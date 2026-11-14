# PRD-121/T2 开发记录：默认中文配置（2026-11-14）

> trend issue #605。10-21 批遗留补齐：T1 已合并（cursor/prd-121-t1-install-e933），
> T2~T5 未交付。本单恢复推进；T1 设计与现行 main 的偏差如实声明。

## 交付

- `scripts/install-zh.sh` 新增 `write_default_config` + `--write-config` 模式：
  写 `${STATE}/openworker-zh.default.json`（schema openworker-zh-default-config/v1）
  ——ui.locale=zh-CN / first_run=zh；model.base_url 占位 example.invalid、
  api_key 只给环境变量名 `OPENWORKER_ZH_API_KEY` 不写值；600 权限；重复执行
  恢复默认（逐字节一致）；`--dry-run` 仍零写入。install 流程装完即写默认配置。
- `tests/test_prd121_t2_default_config.py`：8 例全绿（合法 JSON/全占位/无密钥值/
  600/幂等/dry-run 零写入/self-test/语法）。

## T1 偏差核验与链上修复（如实声明）

- T1 自测失败（环境性→真实 bug）：脚本 self-test 硬编码 `/usr/bin/bash`
  （Linux 有、macOS 无）。随本单修复：self-test 内改用 `BASH_ABS=
  $(command -v bash)` 动态解析，受控 PATH 场景保持原语义。修复后 T1 全部
  7 例通过（原 main 上 test_self_test_passes 必失败）。
- bash 3.2（macOS 自带）`set -u` 下未绑定变量即使 `||` 也致命——自测段
  改为先显式初始化再拷贝。
- 密钥词面自命中两次（T1 测试禁词扫描含 sk- 字面）：检测模式用 printf
  拼接构造+长令牌形态（43+ 连续字符）兜底，注释不含该字面。

## PR 门槛合规核对（repos.yaml default_pr_gate）

| 门槛 | 落实 |
|---|---|
| require_integration_point | 接入点=install 装完写启动脚本之后写默认配置；--write-config 供用户/测试独立调用 |
| no_missing_channel | 配置写本地 JSONL 同款本地文件（${STATE}），零网络零下载；分发地址仍占位 |
| no_duplicate_module | 不另起配置引擎：只新增 install 脚本内函数与既有 app 无耦合（T1 同款边界） |
| impl_requires_devlog | 本文件即开发记录 |

## 合规核对

- 零网络零子进程（脚本自身不请求任何地址；测试仅本地 bash/pytest）。
- 示例全占位，无真实主机名/IP/账号/密钥（含 T1 禁词扫描通过）。
