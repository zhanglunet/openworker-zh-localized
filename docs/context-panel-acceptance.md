# 中文上下文面板 T5 验收记录（PRD-155/T5，trend #779）

> 验收日期：2026-10-25（T5 分支 `trend/prd-155-t5-dsh-context-zh-panel`）
> 验收对象：T2/T3 面板（PR #43/#44）+ T4 开箱文档（PR #46）
> 验收标准（PRD-155 T5 行）：**中文用户按文档 10 分钟内看懂面板；无密钥**
> 验收形态：人工浏览器走查（逐步计时）+ 自动化验收测试 `tests/test_panel_acceptance_t5.py`（HTTP + 页面字符串检查）

## 结论

**通过。** 按指南 5 步开箱全链路（打开面板 → 明暗主题 → 页签①能力组成 → 页签②调用演进 → 节点详情 → 数据契约）走通，交互操作合计约 2.2 秒，中文用户含阅读理解预计 5 分钟内看懂面板；面板数据与面板文档密钥扫描零命中。T4 遗留的 3 处文档问题（见「勘误与收尾」）已在本 PR 修复。

## 步骤 × 耗时表（人工走查实测）

走查环境：`ui-mocks/` 起在本机回环地址的临时静态服务（与双击 `file://` 打开等价，两种形态数据同源——页内回退副本与 fixtures 契约文件深度一致，测试钉住）。

| 指南步骤 | 操作 | 实测耗时 | 结果 |
|---|---|---|---|
| ① 打开面板 | 打开 `dsh-context-panel.html`，默认落页签① | 约 2.1 s（加载到内容上屏） | 通过：标题/角色/会话、「演示数据」徽标、装配清单、五段占比条（合计 10,300 tok）全部上屏 |
| ② 切换主题 | 右上角主题按钮往返切换 | 单次 <10 ms | 通过：`data-theme` light→dark→light 往返生效 |
| ③ 看组成 | 阅读页签①（占比条 + 合计 token） | 0 额外操作，阅读约 1–2 分钟 | 通过：五段占比（31/27/18/12/12%）与合计口径「（token 占比，合计 10,300）」可读 |
| ④ 看演进 | 点页签② → 点节点（失败样例 `file_read`）看详情卡 | 约 0.09 s（切页签+点节点到详情上屏） | 通过：7 节点按发生顺序，●/◆ 形态、✓/✕/↻ 三态齐全；详情卡显示「工具调用 file_read 失败，输入 token 520、输出 token —、耗时 400 毫秒」（缺失字段显示「—」不造假数） |
| ⑤ 换数据 | 核对面板只认 `panel-data v1` 契约 | 约 0.01 s（取回比对） | 通过：页面数据与 `fixtures/panel-demo-data.json` 逐字一致；页内实测 `schema_version: 2` 被契约闸拒绝（「数据源版本不支持」，不渲染任何区） |

**合计口径**：交互操作约 2.2 秒 + 中文阅读理解预留 3–5 分钟（五段占比、7 个节点、详情卡三指标），**合计 < 10 分钟** ✅

> 页签数说明：T1 §3.1 定稿为**双页签**（① 能力组成、② 调用演进）+ 节点详情卡，共三块核心视图；本次按该口径验证全链路（面板→双页签→节点详情）。

## 无密钥（验收标准第二条）

- 演示数据（JSON 键名+字符串值）、面板 HTML（含页内回退副本）、使用指南、本验收记录、README §9 逐行扫描 T1 §4.3-1 敏感模式（密钥类词 + IPv4 形态）：**零命中**（`tests/test_panel_acceptance_t5.py::test_t5_keyscan_*` 三例钉住）。
- 连接器账号一律 `<占位符-账号>` 形态；模型/服务商为 `<示例模型名>`/`<示例服务商>`；时间线标签全虚构。

## 勘误与收尾（T4 遗留 → 本 PR 修复）

1. **指南步骤④原文与实现不符**：原文写「用 ◀ ▶ 步进关键节点或点『自动回放』」，T3 实际落地形态（T1 §2）是**点击任一节点**看详情卡（默认已选中首节点）+ 键盘 ←/→ 切换页签，无步进器/自动回放。已将 `docs/context-panel-guide.md` 步骤④改为实际交互。
2. **README 出现两个 §9**：T4 插入「§9 开箱加餐」未重排后续编号。已重排为 §9 开箱加餐 / §10 仓库结构 / §11 已知问题与后续计划 / §12 贡献与许可，并同步目录。
3. **截图占位补真**：`docs/assets/context-panel-composition.png`（页签①）、`context-panel-timeline.png`（页签②+失败节点详情卡）、`context-panel-zh.png`（README 概览，同页签①）均为真实渲染截图。

## 截图方法与偏差披露

- 截图由无头 Chromium 渲染 `ui-mocks/dsh-context-panel.html` 的**字节一致副本**生成（副本仅存于临时目录，不入库）；时间线截图的副本额外附加 3 行脚本（加载后自动切页签②并点选失败节点），面板本体零改动。
- 走查所用嵌入式浏览器的指针级点击与截屏面在本环境不稳定（点击超时）：走查改用页内 DOM `click()` 派发（与真实点击同一事件路径，处理函数真实执行），截图改用无头浏览器。自动化验收不受影响（HTTP + 页面字符串检查）。

## 测试

- 自动化验收：`tests/test_panel_acceptance_t5.py`（12 例，按指南①~⑤逐步断言 + 密钥扫描 3 例；支持 `python3` 直跑或 pytest）——**12/12 通过**
- 面板文档门禁：`tests/test_panel_docs.py`（T4 自查随 T5 从「占位不伪造」翻转为「真实截图已入库且被引用」，3 例）——**通过**
- 回归：`tests/test_panel_fixture_selfcheck.py`（T2/T3 自查 13 例，继续全绿）
- 全量：`.venv` 下 `pytest tests -q` → **1476 passed, 4 skipped, 2 failed**；2 例失败（`test_cli_bridge.py::test_environment_is_not_inherited_wholesale`、`test_shell_i18n_hazards.py::test_no_bare_variable_immediately_before_a_wide_character[.github/workflows/upstream-weekly.yml]`）经在 main 分支复跑确认**与本 PR 无关**（main 上同样失败，环境相关预存问题）。
- 运行方式：`.venv` 下 `pytest tests/test_panel_acceptance_t5.py tests/test_panel_docs.py tests/test_panel_fixture_selfcheck.py -q` → 28 passed
