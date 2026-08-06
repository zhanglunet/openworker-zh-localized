# 待提交上游：定时任务在 skip-on-overlap 下仍可能重复执行

- 发现时间：2026-08-05
- 影响文件：`coworker/automation/scheduler.py`（与上游 `01b6f83` 逐字一致，本仓库未曾改动过它）
- 本仓库已修复：`7347760`（修复）+ `d6c3bcd`（回归测试）
- **上游尚未提交**——本会话的 GitHub 权限只覆盖 `zhanglunet/openworker-zh-localized`，
  无法 fork `andrewyng/openworker` 或在其上开 PR/Issue。本目录是可直接使用的提交材料。

## 缺陷

调度器文档写明策略是 skip-on-overlap（上一次还在跑就不叠加新的运行），但守卫是在
**被 spawn 的 `run_task` 协程首次执行时**才占位，于是 tick 的 `due()` 扫描与前一次运行
结束之间存在 TOCTOU 窗口：

1. 某次运行挂起（例如停在审批上）。它不会推进 `next_run`，所以此后**每次** tick 的
   `due()` 扫描都会再次返回这个任务，并各自 spawn 一个 `run_task`。
2. 这些多余的 spawn 通常在守卫仍被持有时启动，于是直接 bail。
3. 但只要其中某个的**首次执行**发生在前一次运行结束之后——守卫已释放**且**
   `next_run` 已推进——它就会越过守卫，把任务又跑一遍。

**生产后果**：一个挂在审批上的定时任务可能被执行两次。

**CI 表现**：`tests/test_standing_approvals.py::test_blocked_run_does_not_stall_other_tasks`
间歇失败（`assert 2 == 1`）。同一份代码在 GitHub runner 上时通时不通（近期 10 次里中 3 次），
在空闲机器上 30/30 通过——负载越高越容易命中。

## 修复

把占位移到 `_tick` 里，与「决定 spawn」同步完成，重复的 spawn 从一开始就不会产生。
`run_task` 新增 `claimed` 参数：直接调用者（UI 的「立即运行」、自行调用 `run_task` 的测试）
仍在 `run_task` 内取守卫，行为不变。

## 验证

| 检查 | 结果 |
|------|------|
| 补丁应用到上游 `01b6f83` | `git apply --check` 干净通过 |
| 新回归测试（上游代码基 + 补丁） | 通过 |
| 新回归测试（上游代码基，无补丁） | **失败**（`run_count == 2`），确认能逮出缺陷 |
| 上游代码基 + 补丁跑 `test_automation.py` + `test_automation_create.py` + `test_standing_approvals.py` | 37 项全过 |
| 独立复现脚本 `repro_standalone.py` | 修复前 15/15 重复执行，修复后 0/15 |

回归测试不靠时序碰运气：它从 `due()` 调用**内部**开闸，也就是在「某次 tick 刚把任务读成到期、
正要为它 spawn」的那一刻，把窗口钉死。

## 怎么提交给上游

补丁 `0001-fix-scheduler-skip-on-overlap-race.patch` 是标准 `git format-patch` 产物
（英文提交信息，符合上游语言习惯），基于上游 `01b6f83`：

```bash
# 1) fork andrewyng/openworker 到自己账号，然后
git clone https://github.com/<你的账号>/openworker.git
cd openworker
git checkout -b fix/scheduler-skip-on-overlap-race
git am < 0001-fix-scheduler-skip-on-overlap-race.patch

# 2) 跑一遍确认
python3 -m pytest tests/test_scheduler_overlap.py tests/test_standing_approvals.py -q

# 3) 推送并开 PR 到 andrewyng/openworker
git push -u origin fix/scheduler-skip-on-overlap-race
```

PR 标题与正文可直接用补丁里的提交信息（`git log -1` 即可看到完整英文说明）。

## 独立复现脚本

`repro_standalone.py` 不依赖 pytest 与 aisuite（用 importlib 直接加载 `coworker/automation`
的三个子模块，绕开会 import aisuite 的包 `__init__`），可在任何装了 croniter 的环境里跑：

```bash
python3 repro_standalone.py
# 修复前： run_count 分布 {2: 15} → 重复运行 15/15
# 修复后： run_count 分布 {1: 15} → 重复运行 0/15
```

脚本里的路径指向本仓库的 `coworker/automation`，换成上游 checkout 的路径即可对照验证。
