# 待提交上游：定时任务在 skip-on-overlap 下仍可能重复执行

- 发现时间：2026-08-05
- 影响文件：`coworker/automation/scheduler.py`（与上游 `01b6f83` 逐字一致，本仓库未曾改动过它）
- 本仓库已修复：`7347760`（修复）+ `d6c3bcd`（回归测试）
- **上游尚未提交**——本会话的 GitHub 权限只覆盖 `zhanglunet/openworker-zh-localized`，
  无法在 `andrewyng/openworker` 或其 fork 上 push / 开 PR。本目录是可直接使用的提交材料，
  照「怎么提交给上游」一节逐条执行即可（fork 已就绪：`zhanglunet/openworker`）。

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
| 补丁应用到上游 `01b6f83` | `git apply --check` 干净通过（2026-08-06 复验一次） |
| 新回归测试（上游代码基 + 补丁） | 通过 |
| 新回归测试（上游代码基，无补丁） | **失败**（`run_count == 2`），确认能逮出缺陷 |
| 上游代码基 + 补丁跑 `test_automation.py` + `test_automation_create.py` + `test_standing_approvals.py` | 37 项全过 |
| 独立复现脚本 `repro_standalone.py` | 修复前 15/15 重复执行，修复后 0/15 |

回归测试不靠时序碰运气：它从 `due()` 调用**内部**开闸，也就是在「某次 tick 刚把任务读成到期、
正要为它 spawn」的那一刻，把窗口钉死。

> 复验的基点说明：`01b6f83` 是本环境缓存到的**最新**上游提交（2026-08-01）。
> 2026-08-06 复验时上游 remote 已不可达，因此**没能对照当天的 upstream/main**。
> 上游若已往前走，`git am` 可能冲突——第 3 步给了退回原始基点再 rebase 的做法。

## 怎么提交给上游（逐条命令）

补丁 `0001-fix-scheduler-skip-on-overlap-race.patch` 是标准 `git format-patch` 产物
（英文提交信息，符合上游语言习惯），基于上游 `01b6f83`。

> ⚠️ **三个仓库名字很像，别搞混——这正是上次卡住的地方：**
>
> | 仓库 | 是什么 | 在这件事里的角色 |
> |---|---|---|
> | `andrewyng/openworker` | 上游 | PR 的**目标**，只读 |
> | `zhanglunet/openworker` | 你的 fork | PR 的**来源**，本次唯一要 push 的地方 |
> | `zhanglunet/openworker-zh-localized` | 汉化仓（本仓库） | **与本次无关**，补丁材料放在这里而已 |
>
> 不要在任何一个 `openworker-zh*` 本地克隆里做这件事：它们的 `origin` 都指向汉化仓，
> 在里面 `git push -u origin <分支>` 会把上游补丁推到汉化仓去。
> 全程在一个**全新目录**里操作，从头到尾只碰 fork 的那个克隆。

### 第 0 步：fork（已完成）

<https://github.com/zhanglunet/openworker> 已经是 `andrewyng/openworker` 的 fork。
（若换账号操作：打开上游仓库 → 右上角 **Fork**。）

### 第 1 步：全新目录克隆 fork，并同步到上游最新

```bash
cd ~          # 放哪儿都行，只要不在某个已有克隆的内部
git clone https://github.com/zhanglunet/openworker.git openworker-upstream-pr
cd openworker-upstream-pr
git remote -v
```

**目录路径本身不重要**（`~/openworker-upstream-pr`、`~/OpenWorker/openworker-upstream-pr`
都可以，只要父目录不是另一个 git 仓库）。真正决定对错的只有 `git remote -v` 这一条：

```
origin    https://github.com/zhanglunet/openworker.git (fetch)
origin    https://github.com/zhanglunet/openworker.git (push)
```

输出里带 `openworker-zh-localized` 就是进错目录了，停下重来。

fork 可能落后于上游（GitHub 不会自动跟进），先补齐——这一步同时保证第 3 步退路要用的
`01b6f83` 在本地存在：

```bash
git remote add upstream https://github.com/andrewyng/openworker.git
git fetch upstream
git checkout main
git merge --ff-only upstream/main      # 若报 non-fast-forward，说明 fork 的 main 有自己的提交，
                                        # 用 git reset --hard upstream/main（会丢弃它们）
git push origin main
```

### 第 2 步：下载补丁

补丁在本仓库里，本地克隆不一定有（新克隆或浅克隆都可能缺）。直接拉：

```bash
curl -fsSL -o /tmp/scheduler-fix.patch \
  https://raw.githubusercontent.com/zhanglunet/openworker-zh-localized/main/docs/upstream/scheduler-overlap-race/0001-fix-scheduler-skip-on-overlap-race.patch

head -4 /tmp/scheduler-fix.patch
```

应看到 `From 1b71089f…` 与
`Subject: [PATCH] fix(automation): scheduled task can run twice despite skip-on-overlap`。

### 第 3 步：建分支并应用

```bash
git checkout -b fix/scheduler-skip-on-overlap-race
git am -3 /tmp/scheduler-fix.patch
git log -1 --stat        # 必须显示：HEAD -> fix/scheduler-…，两个文件，106 insertions
```

> ⚠️ **这一组必须一条一条跑，看着 `checkout` 那条成功了再跑 `am`。**
> 如果分支已存在（上次尝试留下的），`git checkout -b` 会失败：
>
> ```
> fatal: a branch named 'fix/scheduler-skip-on-overlap-race' already exists
> ```
>
> 而 `git am` 不管这个，会照样把补丁提交到**你当前所在的分支**——通常就是 `main`。
> 这就是为什么最后要用 `git log -1 --stat` 确认 HEAD 指向的是特性分支。
> 已经打错到 `main` 上了也不用重来，把提交挪过去即可：
>
> ```bash
> git branch -m fix/scheduler-skip-on-overlap-race fix/scheduler-old-attempt   # 旧分支改名留存
> git checkout -b fix/scheduler-skip-on-overlap-race                            # 当前提交钉到正确分支
> git branch -f main upstream/main                                              # main 放回上游状态
> ```
>
> 另外：zsh 交互模式默认不把 `#` 当注释，整段带注释粘贴会刷出一串
> `zsh: command not found: #`，**真正的错误会被这些噪音盖住**。
> 粘贴前删掉注释行，或先执行一次 `setopt interactivecomments`。

`-3` 是三方合并兜底。补丁对 `01b6f83` 是干净的（见上面「验证」表），但**上游从那以后可能已往前走**，
所以万一 `git am` 报冲突，退回到补丁的原始基点再 rebase：

```bash
git am --abort
git checkout -B fix/scheduler-skip-on-overlap-race 01b6f83   # 第 1 步已 fetch upstream，这个 commit 在
git am /tmp/scheduler-fix.patch
git rebase upstream/main
```

### 第 4 步：跑测试确认

```bash
pip install -e '.[dev]'
python3 -m pytest tests/test_scheduler_overlap.py tests/test_standing_approvals.py -q
```

装不动全套依赖不影响提 PR——这两个文件只要 `pytest`、`pytest-asyncio`、`croniter`。

想亲眼确认新测试确实逮得住缺陷（而不是一个恒绿的摆设），**只回退 `scheduler.py`、留下测试文件**：

```bash
git checkout HEAD~1 -- coworker/automation/scheduler.py
python3 -m pytest tests/test_scheduler_overlap.py -q     # 必须红：run_count == 2
git checkout HEAD  -- coworker/automation/scheduler.py
python3 -m pytest tests/test_scheduler_overlap.py -q     # 恢复后：绿
```

> 别用 `git stash` 做这件事。`git am` 之后补丁已经是一个**提交**，工作区是干净的，
> `git stash` 只会回你一句 `No local changes to save`，测试照常变绿，
> 于是你会以为「没有补丁也能过」——什么都没验证到。
> （写这份文档时就先踩了一次，上面这组命令是在 `01b6f83 + 补丁` 的临时 worktree 里
> 实跑验证过的：回退后 1 failed，恢复后 1 passed。）

### 第 5 步：推送并开 PR

```bash
git push -u origin fix/scheduler-skip-on-overlap-race
```

> 若报 `non-fast-forward`：说明这个分支之前推过（`git log --oneline -1 origin/fix/scheduler-skip-on-overlap-race`
> 能看到）。**先比内容再决定**，不要上来就 `--force`：
>
> ```bash
> git diff origin/fix/scheduler-skip-on-overlap-race HEAD    # 无输出 = 内容相同，只是 SHA 不同
> ```
>
> 无输出就直接对齐到远端那个，省掉一次 force push（远端已经是对的）：
>
> ```bash
> git reset --hard origin/fix/scheduler-skip-on-overlap-race
> ```
>
> 有输出才说明本地这版确实不一样，再决定要不要 `git push --force-with-lease`。

然后直接打开这个链接——base 与 head 都写死在 URL 里，绕开「GitHub 把 base 默认成你自己
fork、PR 开到自己仓库里」那个坑：

<https://github.com/andrewyng/openworker/compare/main...zhanglunet:openworker:fix/scheduler-skip-on-overlap-race>

格式是 `…/<上游>/compare/<base 分支>...<fork 属主>:<fork 仓库名>:<你的分支>`。
页面上仍应核对一遍：

- base repository = `andrewyng/openworker`，base = `main`
- head repository = `zhanglunet/openworker`，compare = `fix/scheduler-skip-on-overlap-race`

（注意 head 是 `zhanglunet/openworker`，**不是** `zhanglunet/openworker-zh-localized`。）

**PR 标题**：

```
fix(automation): scheduled task can run twice despite skip-on-overlap
```

**PR 正文**用 `git log -1 --format=%b` 的输出——就是补丁里那段英文说明，已经讲清了
TOCTOU 窗口、生产后果、CI 上的间歇失败表现和修复思路。

### 署名

`git am` 会把 author 设成 `Claude <noreply@anthropic.com>`。想换成自己：

```bash
git commit --amend --reset-author --no-edit
```

保留原样也没问题，这是你自己的选择。

## 独立复现脚本

`repro_standalone.py` 不依赖 pytest 与 aisuite（用 importlib 直接加载 `coworker/automation`
的三个子模块，绕开会 import aisuite 的包 `__init__`），可在任何装了 croniter 的环境里跑：

```bash
python3 repro_standalone.py
# 修复前： run_count 分布 {2: 15} → 重复运行 15/15
# 修复后： run_count 分布 {1: 15} → 重复运行 0/15
```

脚本里的路径指向本仓库的 `coworker/automation`，换成上游 checkout 的路径即可对照验证。
