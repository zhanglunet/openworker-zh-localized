# PRD-084/T1：翻译流水线设计（opencode 式多语言 README 自动化）

> trend #373。PRD：`trend/adopted/PRD-084-owzh-i18n-pipeline.md`。
> 本稿是 T1（设计稿）：只定"怎么做"，不写实现代码；T2 按本稿实现。
> 相关仓库：zhanglunet/openworker-zh-localized（OpenWorker 全量汉化版）。
> 前置：PRD-029（同步策略）、PRD-067（质量门）、PRD-068（哨兵）已全部落地。

## 0. 一句话

068 的哨兵是"新剧集通知单"，067 的质量门是"审片环节"，
本流水线是中间的"配音流水线"——通知单一到，自动出带术语锁定的初稿配音，
审片通过才播出。

**诚实口径**：PRD 标题写"多语言"，本仓库的实际需求是**英→中**单向。
第一期只做英→中；"多语言"体现在架构上——目标语言、术语表做成参数，
以后加语言只加配置，不改流水线。不一次做 25 种。

## 1. 流水线输入输出格式

### 1.1 输入

```json
{
  "source": "weekly-report | manual",
  "source_ref": "《上游周报 2026-10-19》#12",
  "items": [
    {"path": "README.md", "status": "modified", "upstream_sha": "a79f7c47"},
    {"path": "docs/enterprise/DEPLOYMENT.md", "status": "modified", "upstream_sha": "a79f7c47"},
    {"path": "docs/new-guide.md", "status": "added", "upstream_sha": "a79f7c47"}
  ]
}
```

- `source=weekly-report`：从 PRD-068 哨兵周报 JSON 的 `needs_translation: [path...]`
  转换而来（见 §4 字段映射）。`status` 取哨兵 `classify_impact` 的 per-file 记录。
- `source=manual`：`workflow_dispatch` 手动输入文件清单（T4 做）。
- **排除项**：`status=removed` 的文件不进流水线——上游删了文件，
  按 PRD-029/T4 三级冲突流程处理，不是"翻译"问题。
- 上游英文 diff 由 T2 实现时按 `upstream_sha` 经 compare API 拉取，
  本稿不定拉取细节（T2 按 068/T1 §2 的 API 约定做）。

### 1.2 输出

- 新分支 `i18n/YYYYMMDD-<slug>`（如 `i18n/20261019-readme-update`），
  从 owzh 的 `main` 拉出。
- PR 标题前缀 `[i18n]`，如 `[i18n] README.md 跟进上游 a79f7c47`。
- PR body 必须含：① 来源（周报 issue 链接 / 手动触发说明）；
  ② "机器初稿，需人工审校"醒目声明；③ 审校 checklist（见 §7）；
  ④ 术语表版本（25 条，拍板日期 2026-10-18）。

### 1.3 上游官方中文包的特殊处理（对照 diff）

上游 v0.3.1 起自带 `surfaces/gui/src/locales/zh.json` 官方中文包
（068/T5 试运行已验证：`zh.json` 更新会被哨兵标红）。
若 `needs_translation` 命中该文件，流水线**不做"翻译"**，改做"对照 diff"：
输出官方中文译法的前后对照表，供人工决定是否同步措辞。
理由：官方译法是现成的，再翻一遍是浪费，且可能与官方打架。

## 2. 翻译引擎选型（T1 待定项①）

| 方案 | 做法 | 优点 | 缺点 |
|---|---|---|---|
| A. LLM API | 整段喂 LLM 翻译 | 质量最高，上下文连贯 | 有成本；需凭据进 CI；输出不稳定 |
| B. 术语替换+规则 | 只替换术语表词汇，其余保留英文 | 零成本、确定性 | 根本不是翻译，整段英文仍在 |
| C. 混合（推荐） | LLM 出初稿 + 确定性术语后处理 | 质量与术语锁定兼得 | 比纯 A 多一步后处理 |

**推荐：C（混合）**。

- LLM 选型：走用户已有的 SiliconForge 网关（OpenAI 兼容，
  默认模型 `AI/Qwen3.8-Flash-Next`，不用 `auto`——沿用企业助手 PRD 的既定结论），
  不引入新凭据体系。网关挂掉时流水线失败退出（不输出半成品），
  下次重跑即可——文档翻译是周级低频，不要求高可用。
- 成本：哨兵是周级触发，单次翻译量通常几段到几页文档，token 成本可忽略；
  T5 试运行时记录实际 token 量，超预期再议。
- B 不可选：它产出的是"术语替换后的英文"，不是中文初稿，违背流水线目标。

## 3. 术语表注入方式：双保险

**推荐：prompt 注入 + 后处理确定性替换，双保险。**

1. **prompt 注入**：system prompt 里附 25 条术语表全文，
   指令"以下术语必须严格使用指定译法，不得意译"。
   作用：让初稿尽量一次写对，减少审校负担。但模型自觉不可靠，
   不能作为唯一手段。
2. **后处理确定性替换**：翻译完成后，用正则把术语英文原形
   （及 `wrongs` 已知错误译法，如"供应商"/"总结"）强制替换为拍板译法。
   术语表源头复用 `scripts/quality-gate.py` 的 `TERMS` 常量结构
   （`en` 正则片段 + `zh` + `wrongs`），T2 实现时从同一份表读，
   不另立第二份表。
   作用：确定性保证，CI 术语锁定对流水线产出必过。

**分工声明**（防误解）：后处理保证"机器初稿"术语必过；
CI 术语锁定（T3）保证"人工改动"也被管住。两者互补，不重复。

**边界**：只锁定 25 条已拍板术语；术语表之外的译法争议，
流水线不替用户做主，留给人工审校（PRD 非目标已有）。

## 4. 与哨兵的接口：`needs_translation` → 流水线输入

哨兵 `classify_impact` 返回（068/T2 已实现）：

```json
{"categories": {"新增文件": [], "修改已汉化文件": [], "修改未汉化文件": [], "非敏感区变更": []},
 "needs_translation": ["docs/enterprise/DEPLOYMENT.md"],
 "removed_sensitive": [], "impacts_zh": true}
```

字段映射（T2/T4 实现约定）：

| 哨兵字段 | 流水线输入字段 | 说明 |
|---|---|---|
| `needs_translation[]` 的 path | `items[].path` | 逐一映射 |
| per-file 记录的 `status` | `items[].status` | added/modified；removed 排除（§1.1） |
| commit 的 `sha` | `items[].upstream_sha` | 取该文件变更所在 commit |
| 周报 issue 号/标题 | `source_ref` | 写进 PR body 溯源 |

**口径对齐声明**：哨兵的"命中敏感区"口径以 `scripts/upstream_common.py`
为准（068/T1 §1 硬要求）；流水线不自立口径，
`needs_translation` 给什么就翻什么。

## 5. CI 校验设计（T3 实现，本稿定口径）

独立 workflow `.github/workflows/i18n-check.yml`，
触发条件：PR 改动 `README.md` 或 `docs/**`（`docs/plans/` 除外，沿用 067/T3 口径）。

### 5.1 术语锁定：失败阻断

- 规则：复用 PRD-067 质量门的 `check_terms`（25 条术语表同一份源头）。
  翻译文本出现术语英文词但中文译法与拍板值不一致 → **失败，阻断合并**。
- 与 067/T3 的关系：067 的 quality-gate.yml 已在检查术语；
  T3 做的时候二选一：① 复用现有 workflow（推荐，不另起文件）；
  ② 独立文件。T3 实现时定，本稿不定。

### 5.2 链接有效性：内链阻断，外链警告（T1 待定项②）

**推荐口径**：

| 链接类型 | 检查 | 失败时 |
|---|---|---|
| 内链（仓库内相对路径、`#` 锚点） | 文件存在性 | **失败阻断**——内链是自己能控制的，断了就是 bug |
| 外链（http/https） | HEAD/GET 可达性，超时 10s，重试 1 次 | **警告，不阻断** |

理由：外链抖动多（目标站挂了、限流了），且翻译者控制不了目标站；
失败阻断会让 CI 噪音淹没真实问题。PRD 验收标准第 3 条"故意断链 CI 能报出"——
警告也算"报出"，T5 用 warning 断言即可。

### 5.3 占位符完整性

翻译后的文档若含代码块占位符（如 `{input}`），沿用 067 的
`check_placeholders` 规则：中英文占位符集合必须一致。
（文档里少见，但加上不花钱，防翻车。）

## 6. 第一期文档范围（T1 待定项③）

**推荐：范围 = 哨兵 `needs_translation` 的全部输出，不另设 allowlist。**

- 哨兵的敏感区（`upstream_common.py`）本来就覆盖 README、`docs/`、`website/`；
  流水线另设范围 = 重复造口径，迟早打架。
- T5 试运行聚焦 **README.md** 做端到端验证（控制验证成本），
  不代表流水线只支持 README。
- `docs/plans/`（过程稿）、`*test*` 沿用 067 的排除口径，不进流水线。

## 7. 人工审校闸门：位置、确认人、防跳过

```
哨兵周报 → [触发] → 流水线跑 → 开 [i18n] PR → CI 检查 → 人工审校 → 合并
                                              ↑               ↑
                                           技术闸门          人工闸门
```

- **人工闸门位置**：`[i18n]` PR 合并前。确认人：仓库维护者（zhanglunet）。
  PR 模板自带审校 checklist（三项必须勾选）：
  - [ ] 术语：25 条拍板术语译法无误（CI 已过，人工抽查流畅度）
  - [ ] 链接：内链有效（CI 已过）；外链警告已人工看过
  - [ ] 流畅度：通读一遍，无机器翻译腔、无漏段
- **防跳过三件套**：
  1. PR body 醒目声明"机器初稿，需人工审校"（模板强制，删了也看得出）；
  2. CI 术语锁定失败阻断合并（技术硬门）；
  3. 分支保护建议：`[i18n]` PR 要求 1 个 approve（仓库设置里配，T4 落地时提醒用户手动开——
     参考 067/T3 的教训：workflow 里的检查不会自己变成 required）。
- **抽查机制**（呼应 PRD 验收标准第 4 条）：T5 试运行报告里如实记录
  "人工审校是否被执行"，留作流程审计证据。

## 8. 给 T2–T5 的接口约定

- T2（流水线实现）：按 §1 输入输出格式实现 `scripts/i18n-pipeline.py`
  （纯标准库 + 网关 HTTP 调用层）；术语后处理复用 `TERMS` 结构；
  `--dry-run` 模式（只出 diff 不开 PR）供 T5 验证。
- T3（CI 校验）：按 §5 口径实现；先定复用 067 workflow 还是独立文件。
- T4（哨兵联动）：按 §4 字段映射做 `workflow_dispatch` 手动触发版；
  自动触发（哨兵 issue → 自动开翻译 PR）明确放二期，本稿不设计。
- T5（试运行）：拿一次真实上游 README 更新走完全流程；
  记录 token 消耗；故意写错术语验证 CI 拦截；故意断外链验证警告；
  报告里如实写人工审校执行情况。

## 9. 不越界

- 不写实现代码（T2，trend #374）。
- 不动 `scripts/upstream-weekly.py` / `quality-gate.py` / `upstream_common.py`，
  只读它们的常量和输出格式。
- 不引入新凭据体系（翻译走现有 SiliconForge 网关）。
- 自动触发放二期，本稿只设计手动触发。
- 代码内 UI 字符串不在本 PRD 范围（PRD 非目标）。
