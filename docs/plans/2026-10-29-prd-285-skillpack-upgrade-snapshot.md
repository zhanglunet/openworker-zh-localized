# PRD-285/T1：中文技能包升级快照设计（skillpack-snapshot-v1）

- 日期：2026-10-29
- 来源：2026-10-28 趋势日报 openworker-zh-localized 第 1 条（⭐），用户当日拍板采纳
- trend issue：[zhanglunet/trend#1426](https://github.com/zhanglunet/trend/issues/1426)
- 中央 PRD：`trend/adopted/PRD-285-owzh-skillpack-upgrade-snapshot.md`
- 状态：T1 设计稿，待评审；实现类任务（T2–T4）只开 PR 不合并
- 同批主题：本批「可逆改动包」14 仓同构——先快照、再改动、一键回上一版

## 1. 目标与非目标

**目标**：升级中文技能包（覆盖已安装技能目录或安装新版角色包）前，自动留一张**升级前快照**（包目录整体副本 + 清单指纹）；升级后跑**抽查（spot_check）**，抽样校验并落档；抽查失败时**一键回滚旧包**，抽查记录与回滚记录**一并存档**（append-only、机读）。

**非目标**：
- **不做多版本历史**——一键回滚只回"上一版"；被顶替的快照转入 archive 只读留档（审计追溯用，不经 restore 通道恢复），不提供"回到任意历史版本"的时间旅行；
- **不自动生成技能**——录制、提炼、review 入库是 PRD-267 领域；本条只管升级应用前后的可逆；
- **不联网**——快照、升级应用、抽查、回滚、存档全链零网络（T4 AST 断言钉住）；
- 不替代 git 历史——git 记录"变更怎么发生"（PR 合并），快照记录"运行时回滚点"，两者指纹互相对账（§3.5）；
- 不碰用户偏好——`skills-settings.json`（个人启用/禁用等）不在快照与还原范围，回滚不动用户设置。

## 2. 与既有能力的划界

| 既有能力 | 关系 |
|---|---|
| PRD-267 中文实操转中文技能 | **267 管技能来源**（录制 → 人 review 入库门 → 带口语化触发词的中文技能）；**285 管升级可逆**（升级前快照 / 升级后抽查 / 回滚存档）。组合点：267 入库的技能作为一次升级应用时，可触发 285 快照——但通道独立、互不依赖；267 不做快照回滚，285 不生成技能 |
| PRD-183 中文角色包规范 | 183 定包形态与安装动线（`role-packs/<包>/`、persona.md 唯一 .md 约束、本地目录安装）；本条把**安装后的运行态实例**作为快照对象，不改变 183 任何规范。183 明确 manifest 无版本字段 → 快照以**指纹**为身份，不自造版本体系（§3.2） |
| 技能目录机制（folder-is-truth） | 全局技能在 `state_dir()/skills`、项目技能在 `<workspace>/.coworker/skills`，无数据库；快照按**整个技能文件夹**为最小还原单元（§3.1），还原即目录级覆盖，加载器零改动 |
| 上传暂存通道 | 技能上传走 `state_dir()/skills-staged/<token>` 暂存（解析 → 预览 → 确认）；285 的快照挂在**确认动作前**强制触发——暂存面与快照面互不混用 |
| personas 托管区 | 第三方角色安装已"快照进托管区 `personas-installed/<id>/`"（`coworker/personas/registry.py::install_from_dir`）；涉及 persona.md 的升级沿用该托管区形态，本条不重复建设（§3.1 范围表） |
| PRD-268 零网络纪律 | 268 验收已立 AST 断言先例（封禁 `socket`/`urllib`/`http`/`requests`/`httpx`/`ssl`/`subprocess` 等 import）；285/T4 沿用同一断言形态扫快照/回滚/抽查实现模块 |
| git 历史 | git 记录"变更怎么发生"；快照记录"运行时回滚点"（含清单指纹），一键执行、不依赖 git 操作权限 |

## 3. 方案设计

### 3.1 快照对象与时机（封闭清单）

| 对象 | 位置（运行态） | 说明 |
|---|---|---|
| 技能文件夹 | `state_dir()/skills/<技能名>/` 或 `<workspace>/.coworker/skills/<技能名>/` | folder-is-truth：整个文件夹为最小快照/还原单元（SKILL.md + 附带文件） |
| persona（可选） | `personas-installed/<id>/manifest.md` 及其 skills/ | 升级触及中文角色包时一并快照；沿用 personas 托管区形态 |

- **快照时机：挂在升级确认动作前强制触发**——新包覆盖已安装技能目录（或角色包重装/更新）前先出快照；快照失败则升级中止（fail-close，宁可不能升，不可不可回）；
- **回滚动作前再出一张"问题态"快照**（event kind = `snapshot_taken`, `trigger.kind = pre_rollback`），保证"回滚可再回滚"（§3.3 规则 5）；
- **范围限定**：只快照本次升级触及的包（`packages[].name` 显式列出）——不做全目录扫描式快照，避免把无关技能卷进存档。

### 3.2 快照 schema：`skillpack-snapshot-v1`

```json
{
  "schema": "skillpack-snapshot-v1",
  "snapshot_id": "sps-20261029-a1b2c3d4",
  "taken_at": "2026-10-29T09:00:00+08:00",
  "target_scope": "global",
  "skillpack_root": "<占位：state_dir()/skills 或 <workspace>/.coworker/skills>",
  "trigger": {
    "kind": "skillpack_upgrade",
    "ref": "<升级动作标识占位，如安装会话 token>"
  },
  "base_commit": "<git 短哈希占位，可空：运行目录未必是 git 检出>",
  "packages": [
    {
      "name": "zh-sales-lead-brief",
      "kind": "skill",
      "manifest_fingerprint": "sha256:<占位>",
      "dir_fingerprint": "sha256:<占位>",
      "bytes": 12345
    }
  ],
  "snapshot_dir": "<占位：state_dir()>/skillpack-snapshots/sps-20261029-a1b2c3d4/",
  "notes": []
}
```

字段纪律：

- **两枚指纹**：
  - `manifest_fingerprint`：SKILL.md 解析出的 manifest 取 `{name, description}` 的 canonical JSON 做 sha256——183 机制硬约束：manifest 校验器**无版本字段**，包身份以指纹承载，不自造 frontmatter 版本字段（会过不了解析器还会误导安装者）；
  - `dir_fingerprint`：技能文件夹内全部文件按相对路径排序，取 `{path, sha256, bytes}` 清单的 canonical JSON sha256——目录整体一致性，还原后重算对账。
- **`target_scope`** ∈ `global | project`：与技能目录 scope 同源（`state_dir()/skills` = global，`<workspace>/.coworker/skills` = project）；project 快照落 `<workspace>/.coworker/skillpack-snapshots/`，global 快照落 `<state_dir()>/skillpack-snapshots/`，互不混放；
- **`kind`** ∈ `skill | persona`：persona 条目的 `name` 为角色 id（`zh-sales` 等），指纹取 manifest.md 同法；
- **示例全中文虚构**：`zh-sales-lead-brief` 等均为本仓 PRD-183 规划的虚构示例名；`skillpack_root`/`snapshot_dir` 一律 `<占位>` 形态，不出现真实主机名/IP/账号/密钥。

### 3.3 回滚接口与语义（全部为硬规则）

**接口（T2 实现）**：

```
snapshot_skillpack(packages, trigger) -> skillpack-snapshot-v1   # 升级确认动作前强制调用
spot_check(snapshot_id | upgrade_id, sample_items) -> spot-check-v1   # 升级后抽样校验（§3.4）
restore_skillpack(snapshot_id?, reason) -> rollback-record-v1    # 一键回旧包
```

1. **只回上一版**：无参调用回滚最近一张快照；带 `snapshot_id` 仅限 archive 中存在的快照（事件显式记 `non_default: true`）；
2. **逐字节还原**：从快照目录把整个技能文件夹复制回原位（目录级覆盖，folder-is-truth，加载器零改动）；还原后**重算两枚指纹必须与快照记录一致**，任一不符即回滚失败、只落 `restore_failed`（绝不静默半还原）；
3. **单槽位"上一版"**：不做多版本历史（PRD 非目标）——每个 scope 只有一张可回滚快照；被新快照顶替的转入同目录 `archive/` 只读留档，不经 restore 通道恢复；
4. **抽查失败才推荐回滚，v1 不自动回滚**：`verdict=fail` 时升级标记 degraded 并提示一键回滚——抽查本身可能误判（触发例命中是启发式），自动回滚会把好升级回掉；是否改为自动回滚留评审决定；
5. **回滚可再回滚**：回滚前强制"问题态"快照（§3.1 时机 2），回滚后快照槽保留；若要把"回滚前的新版"装回来，走正常升级流程（新包 + 新快照），全程留档；
6. **fail-close**：该快照时快不了 ⇒ 升级中止。

**`rollback-record-v1`**（追加进 `<快照根>/audit.jsonl`）：

```json
{
  "schema": "rollback-record-v1",
  "rollback_id": "spr-20261029-e5f6a7b8",
  "at": "2026-10-29T14:30:00+08:00",
  "snapshot_id": "sps-20261029-a1b2c3d4",
  "spot_check_id": "spc-20261029-c3d4e5f6",
  "from_fingerprint": "sha256:<占位>",
  "to_fingerprint": "sha256:<占位>",
  "verify": "passed",
  "non_default": false,
  "reason": "<必填一句话，如：升级后触发例命中失败，回旧包>"
}
```

### 3.4 升级后抽查：spot_check 抽样校验并落档（T3 核心）

**`spot-check-v1` schema**：

```json
{
  "schema": "spot-check-v1",
  "check_id": "spc-20261029-c3d4e5f6",
  "checked_at": "2026-10-29T09:05:00+08:00",
  "upgrade_id": "<升级动作标识占位>",
  "snapshot_id": "sps-20261029-a1b2c3d4",
  "sample_policy": { "strategy": "touched-all-under-5-else-3", "size": 3 },
  "sample_items": [
    {
      "pkg": "zh-sales-lead-brief",
      "checks": [
        { "name": "manifest-valid", "result": "pass", "detail": "" },
        { "name": "name-dir-consistent", "result": "pass", "detail": "" },
        { "name": "trigger-zh-present", "result": "pass", "detail": "" },
        { "name": "references-exist", "result": "pass", "detail": "" },
        { "name": "dir-fingerprint-declared", "result": "pass", "detail": "" }
      ]
    }
  ],
  "verdict": "pass",
  "notes": []
}
```

- **抽样策略（v1 拍板项，评审可调）**：本次升级触及的包 ≤5 个时全查；>5 时按包名字典序取前 3（确定性抽样，可复现、可对账）——不引入随机性；
- **单包五项校验**（全部本地文件操作）：
  1. `manifest-valid`：SKILL.md 可解析、必需字段齐全；
  2. `name-dir-consistent`：manifest name 与目录名一致、满足既有技能名校验（`^[A-Za-z0-9][A-Za-z0-9._-]*$` ≤64 字符）；
  3. `trigger-zh-present`：description 含中文触发短语（口语化触发词的轻量存在性检查；完整命中验证不进 v1）；
  4. `references-exist`：SKILL.md 引用的包内文件存在；
  5. `dir-fingerprint-declared`：升级后重算 `dir_fingerprint` == 升级声明值（升级前后清单对账，防"装的不是说的那版"）；
- **落档**：spot-check-v1 整条 JSON 追加进 `audit.jsonl`（append-only），与快照、回滚记录同一存档——抽查记录与回滚记录一并存档（PRD 目标原文），按 `snapshot_id`/`upgrade_id` 可机读串联；
- `verdict=fail` ⇒ 升级标记 degraded，一键回滚入口激活（§3.3 规则 4）。

### 3.5 存档形态与零网络

- **存档布局**（全部本地）：

```
<state_dir()>/skillpack-snapshots/          # global scope；project scope 在 <workspace>/.coworker/skillpack-snapshots/
├── audit.jsonl                             # append-only 事件流（机读）
├── sps-20261029-a1b2c3d4/
│   ├── snapshot.json                       # skillpack-snapshot-v1
│   └── packages/zh-sales-lead-brief/       # 包目录完整副本（逐字节还原源）
└── archive/                                # 被顶替的旧快照只读留档
```

- **事件流**（`audit.jsonl`，一行一 JSON，机读）：`kind` ∈ `snapshot_taken` / `upgrade_applied` / `spot_check_recorded` / `restore_applied` / `restore_failed`；每行含 `at`、`scope`、`snapshot_id`、`packages_fingerprint`、`verify`、`gap`（写失败占位，不伪造）——回滚记录存档即此流中的 `restore_applied`/`restore_failed` 行 + `rollback-record-v1` 条目；
- **全链零网络**：快照/还原/抽查/存档均为本地文件操作，模块无任何网络调用面；T4 沿 PRD-268 验收先例做 AST 扫描（封禁 `socket`/`urllib`/`http`/`requests`/`httpx`/`ssl`/`subprocess` 等 import），并对文档示例做无 URL 外联扫描；
- **与 git 对账**：快照可带 `base_commit`（可空——运行目录未必是 git 检出）；非空时校验包面指纹 == 该 commit 下同名包重算指纹，不一致说明快照脱离所声称基线，T4 断言钉住。

## 4. 安全红线

1. **本地处理零网络（本 PRD 第一红线）**：全链（快照/升级应用/抽查/回滚/存档）零网络调用；T4 AST 断言 + 文档外联扫描双钉；升级源（新包从哪来）不在本条范围，285 不发起任何下载；
2. **fail-close**：快照失败升级中止；还原后指纹不符回滚失败告警，只落 `restore_failed`；存档写失败落 gap 占位不伪造；
3. **回滚留档可再回滚**：回滚前强制"问题态"快照；`restore_failed` 也如实入档；
4. **不碰界**：用户偏好（`skills-settings.json`）、personas 托管区既有快照、skills-staged 暂存面，均不在本条写路径上；写路径封闭在 `<快照根>/` 与被触及的技能文件夹；
5. 本文档与示例**无真实主机名、IP、账号、密钥**，占位符一律 `<占位>` 形态；示例包名、快照号、指纹全虚构，示例文本全中文。

## 5. 演练样本（T2 夹具、T5 回放，全虚构中文示例）

| 样本 | 内容（全虚构） | 预期 |
|---|---|---|
| P-1 常规升级 | 虚构技能 `zh-sales-lead-brief` 升级（改中文触发短语） | 确认前自动出快照；升级后抽查 pass；audit.jsonl 三行（snapshot_taken/upgrade_applied/spot_check_recorded） |
| P-2 抽查失败回滚 | 升级后 `trigger-zh-present` 抽查 fail | 升级标记 degraded；一键回滚旧包；两枚指纹一致；spot-check 与 rollback 记录一并落档 |
| N-1 快照被跳过 | 模拟跳过 snapshot 直接应用升级 | 升级中止（fail-close），运行目录无变化 |
| N-2 还原后指纹不符 | 人为篡改快照副本一个字节 | restore 报错退出，只落 `restore_failed`（verify: failed），无成功记录 |
| N-3 越界夹带 | 回滚同时试图改动 `skills-settings.json` 与未触及包 | 拒绝：写路径封闭（§4 红线 4），未触及包不在快照/还原范围 |
| N-4 零网络断言 | 实现模块引入 `urllib` | T4 AST 扫描失败，断言不过 |

## 6. T2–T5 任务拆分（按 PRD）

| 任务 | 内容 | 验收标准（PRD 原文口径） |
|---|---|---|
| T2 | 快照存储与回滚最小实现（snapshot/restore/审计记录） | 样例可快照可回滚，审计可查，有测试 |
| T3 | 升级后抽查记录：spot_check(sample_items) 抽样校验并落档 | 抽查记录字段齐全，有测试 |
| T4 | 本地处理断言：快照/回滚/抽查全链零网络（AST/源码扫描） | 断言通过 |
| T5 | 验收试运行：样例全流程回放 + 回滚演练 + 文档无密钥 | 快照回滚全链通过；红线断言全过；文档无密钥 |

依赖关系：T1 → T2 → T3 → T4 → T5。

## 7. T5 验收标准

1. P-1/P-2 全链：升级前快照自动发生 → 应用 → 抽查 → （失败时）一键回滚 → 指纹一致、包目录逐字节还原；N-1 fail-close 生效（跳过快照的升级被中止）；
2. N-2 篡改快照被检出，`restore_failed` 如实入档且无成功回滚记录；P-2 的抽查记录与回滚记录在 `audit.jsonl` 可按 `snapshot_id` 串联回放；N-3 写路径越界被拒绝；
3. 每次升级/回滚在 `audit.jsonl` 有机读行（字段齐全、append-only、gap 纪律）；抽查记录五项校验字段齐全（§3.4）；
4. N-4 零网络 AST 断言通过（快照/回滚/抽查实现模块封禁 import 集零命中）；文档外联扫描零命中；
5. 全部 schema/记录/文档密钥扫描 0 命中、真实主机名/IP/账号 0 命中；示例全中文虚构。

## 8. 借鉴划界

- [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv)：GitHub License API 实测 **NOASSERTION（无协议）**。**仅借鉴「先快照再改动、一键还原」的形态思路，不复用其任何代码与文案**；`skillpack-snapshot-v1` schema、目录清单指纹算法、抽查五项校验与抽样策略、回滚语义（fail-close/单槽位上一版/可再回滚）、零网络断言形态均为本仓原创设计。
- 与日报原文的差异修正：日报未核实许可证，实测无协议——借鉴口径据此收紧为"仅形态思路零复用"（同批 14 仓统一口径）。
