# 中文技能包同步漂移修复指引

> PRD-212/T4（trend #1063）：每类漂移的「可照做」修复步骤。诊断用同步检查脚本
> （`scripts/cn_skill_sync_check.py`，见 `docs/plans/2026-10-26-cn-skill-sync-checklist-design.md`
> 的 CN-SYNC 编号），本指引按编号逐条给出修复动作。

## 修复总步骤

1. 先跑检查脚本拿状态表（只读，不改任何工具目录）：
   `python3 scripts/cn_skill_sync_check.py check --manifest manifests/<批次>.json`
2. 按下表逐条修复（修复只动工具目录里的 skill 文件，不碰脚本本身）。
3. 修完重跑检查，直到结论 PASS。

## 按编号的修复步骤

### 安装类（装了没）

- **CN-SYNC-01 目录不存在（MISSING）**：从仓库 `role-packs/<角色>/skills/<skill-id>/`
  复制整个 skill 目录到对应工具的技能根目录（对照 T1 §2 的路径表），然后回到总步骤第 1 步重跑。
- **CN-SYNC-02 元数据缺失或不一致（SKILL.md 缺 name/description/version）**：
  以仓库内该 skill 的 SKILL.md 为准整份覆盖工具目录里的 SKILL.md（不手改单字段，
  防止再次漂移）；`name` 必须与目录名一致。
- **CN-SYNC-03 附属资源缺失**：对照 manifest 的 `files[]`，把缺失文件从仓库复制过去；
  0 字节文件视为缺失，同样整份覆盖。

### 版本类（对不对）

- **CN-SYNC-04 版本不可读（UNREADABLE，检查项记 UNKNOWN）**：确认 SKILL.md frontmatter
  有 `version: X.Y.Z` 或目录下有 VERSION 文件；没有就从仓库同步一份带版本标识的
  SKILL.md。版本比对项随行记 SKIP（不参与该轮判定）。
- **CN-SYNC-05 版本漂移（VERSION_DRIFT）**：把工具目录里的 skill 整目录替换为
  manifest 对应版本（先删旧目录再复制，防新旧混装）；重跑确认一致。
- **CN-SYNC-06 内容漂移（CONTENT_DRIFT）**：版本号相同但文件指纹不符（多为手改痕迹）——
  先确认手改内容是否要保留：要保留就回仓库改源头发新版本；不要保留就整目录重装。

### 残留类（旧版清没清）

- **CN-SYNC-07 旧版本目录（OLD_DIR，如 `<skill-id>@1.0.0`）**：确认新版可用后删除
  整个旧版目录（多版本并存会造成误触发）。
- **CN-SYNC-08 孤儿文件（ORPHAN_FILES）**：对照 manifest `files[]`，差集里既不在
  仓库也不在清单里的文件逐个确认后删除；判不清的先移出工具目录观察一周。

- **CN-SYNC-09 索引/缓存残留（SKIP，名单待实测冻结）**：按各工具的重载入口刷新
  skill 索引/缓存（重载后仍残留才升级复核）；此项检查恒记 SKIP，不产生 WARN。
- **CN-SYNC-10 标准触发词不命中**：先重装最新版（多数是版本漂移的连带症状）；
  仍不命中则按 manifest 的 `triggers.standard[]` 修订 SKILL.md 的 description
  关键词，修完按 §4.3 全量重测（11+3 条），不接受只测失败条。
- **CN-SYNC-11 口语变体不达标（低于 6/8 或某类全灭）**：按 §4.1 的四类样本逐类
  排查——某类全灭优先补 description 的口语同义表述；修完整量重测。
- **CN-SYNC-12 误触发**：收窄 description 里的触发词（去掉过泛的口语词），
  修完重跑反向样本确认 0 误触发。

## 修复后

- 全部条目回 PASS 后，把本轮状态表存档（文件名占位
  `sync-status-<批次>-<日期>.md`），作为下一轮对照基线。
- 反复漂移同一 skill 时，优先排查是否有别的工具在同步覆盖它（写入方竞争）。
