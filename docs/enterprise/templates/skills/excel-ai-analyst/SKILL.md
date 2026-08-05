---
name: excel-ai-analyst
description: 把含公式的业务 Excel 当作没有文档的遗留代码来逆向工程——结构化转 MD、抽字段本体、还原公式链与跨表数据血缘、用全量真实数据逐行验证理解是否正确，再输出带标注的结果表与业务分析报告。当用户说"分析一下这个 Excel/表格""搞懂这张表是怎么算的""帮我核对/验证表里算得对不对""这套手工 Excel 流程能不能 AI 化、表进表出""做成本分析、异常检测、What-If 测算"，或提到 Excel 转 MD、字段本体、公式解析、数据血缘、跨表核对、工资表/成本表/台账/报价表分析，或直接点名"大表哥"时使用。不适用于简单的表格读写与数据清洗（用 xlsx 技能），也不适用于最终产物是 Word/PPT 的场景。
allowed-tools: run_shell, read_file, read_file_lines, write_file, list_files, grep, todo_write
---

# Excel 智能分析（把表格当代码读）

## 核心主张

一张成熟的业务 Excel 就是一套**没有文档的遗留代码**：列名是变量名，公式是函数，
跨 Sheet 引用是模块依赖，check 列是单元测试。所以分析它的正确姿势不是"看数据"，
而是**逆向工程**：先还原变量定义（本体）→ 再还原函数与调用图（公式链 + 血缘）→
然后用全量真实数据跑一遍回归测试（验证）→ 通过了才有资格谈分析和推演。

**跳过验证直接分析 = 在没读懂代码的情况下改代码。** 这是本技能最重要的一条纪律。
用户催"直接给结论"时也不能跳——没验证过的结论，错了没人知道。

## 五步法

| 步 | 产出 | 谁来做 |
|---|---|---|
| 1 结构化转换 | 每个 Sheet 一份 MD：多行表头、合并单元格、真实公式、列画像 | `excel_ai.py tomd` |
| 2 字段本体 | 跨表统一的字段定义表（含义/类型/计算关系/来源） | **AI 手写** |
| 3 公式链与血缘 | 分层公式链 + 跨 Sheet 数据流向 | **AI 手写** |
| 4 数据验证 | 逐行比对「AI 理解」vs「Excel 实际值」，出通过率与不匹配清单 | `excel_ai.py verify` |
| 5 交付 | 带配色标注的结果表 + 分析报告（分布/异常/What-If） | `excel_ai.py output` / `analyze` |

Step 2/3 是**认知工作，必须由你读着 Step 1 的 MD 亲自写**，不要试图用脚本自动生成——
业务含义不在文件里，在列名的言外之意里。Step 1/4/5 是机械工作，交给脚本。

开工第一件事是 `todo_write` 把这五步列出来（用户的进度面板就是它渲染的），
每完成一步更新状态，同时只保持一项 in_progress。

---

## 开工前：三件事

### 1. 找到脚本

脚本随技能分发，就在 `load_skill` 返回的 `resources_path` 下：

```
<resources_path>/scripts/excel_ai.py
```

**用 `load_skill` 返回的那个 `resources_path`，不要假设当前目录下有 `scripts/`。**
（技能装在全局技能目录或项目技能目录里，与用户的工作区不是同一个地方；
一般是 `~/.config/coworker/skills/excel-ai-analyst`，Windows 在 `%APPDATA%\coworker\skills\` 下，
项目级则在 `<工作区>/.coworker/skills/` 下——路径会变，`resources_path` 不会错。）

先确认它在：`run_shell` 跑 `ls <resources_path>/scripts`，或 `python3 <resources_path>/scripts/excel_ai.py --help`。
万一确实缺文件（技能被裁剪过），按 `references/spec-schema.md` 的「附录」现写一份，别硬着头皮手算。

### 2. 让 `python3` 能跑

OpenWorker 的命令执行走审批：`run_shell` 默认每次弹审批卡，除非命令命中用户全局配置里的
`allowed_commands` 白名单。第一次调用时告诉用户：

> 想免掉后面每一步的审批，可以在全局配置 `~/.config/coworker/config.toml`
> （Windows：`%APPDATA%\coworker\config.toml`）里加一行：
> ```toml
> allowed_commands = ["python3"]
> ```
> 更保守的企业写法是只放行这一个脚本（白名单按**命令词前缀**匹配）：
> ```toml
> allowed_commands = ["python3 /Users/你/.config/coworker/skills/excel-ai-analyst/scripts/excel_ai.py"]
> ```
> 白名单只在**用户全局配置**里生效；工作区 `.coworker/config.toml` 里的同名配置要等这个工作区被信任后才追加。

两条会让白名单失效、必然弹审批的写法，能避就避：

- 命令里带 `&&`、`;`、`|`、`>`、`<`、`` ` ``、`$(`、`(` 或换行——一律强制审批。所以
  **一条命令只做一件事**，不要串联、不要重定向。
- 文件名带括号（`工资表(1).xlsx`）也会命中上面这条。必要时先把表复制成不带括号的名字。

还有一条 OpenWorker 的硬约定：**绝不要在 shell 命令里内联多行脚本（不要 heredoc）**。
`spec.json` 用 `write_file` 写成文件，再让 `excel_ai.py` 读它——审批卡才短、内容才可复核。

### 3. 定输入与输出

- **输入**：用户的表通常在会话工作区，或本次会话的草稿目录（默认 `~/OpenWorker/<会话 id>`）。
  不确定就 `list_files` 看一眼，别猜文件名。
- **输出**：所有产物写到工作区下一个**独立输出目录**（见下方「目录约定」）。
  **绝不修改用户原表**——`tomd`/`verify` 只读打开原文件，你也不要用别的手段回写。
- 交付时按 OpenWorker 的习惯，最后用 `[结果表](artifact:04_output/AI处理结果.xlsx)` 这样的
  markdown 链接把产物指出来，用户点一下就能打开。

> **数据不出内网**：`excel_ai.py` 只用 Python 标准库 + pandas + openpyxl，
> 零网络调用、不上传任何单元格、不写临时文件到系统目录，全部计算在本机完成。
> 涉及工资、成本、客户价格这类敏感表时，把这一条明确讲给用户——这是企业敢用的前提。

---

## Step 1：Excel → 结构化 MD

```
python3 <resources_path>/scripts/excel_ai.py tomd 表A.xlsx 表B.xlsx -o ./01_raw_md
```

可选参数：`--sheets 明细表 汇总表`、`--header-rows 4`（不给则自动推断）、
`--header-scan 8`、`--preview-rows 10`、`--summary-words 汇总 合计 小计`。

产出 `01_raw_md/<文件名>/<Sheet>.md` 与 `00-索引.md`。每份 MD 含：表头区逐行解析、
列字段定义表（拼接列名 / 样例值 / 填充率 / 类型 / 真实公式）、真实公式清单、数据预览、告警。

读 MD 时重点看四件事：

1. **数据体从第几行开始**——脚本已给出推断值，但要自己确认一眼（`header_rows` 数错一行全废）
2. **哪些列是输入，哪些是结果**——结果列往往列名里就写着公式，或标了"公式勿动"
3. **哪些列是校验列**——check / Countif / 核对，它们是原作者留下的断言，白送的测试用例
4. **类型告警**——`数值为主(75%)⚠️含非数值` 意味着这列混了 `/`、`-`、备注文字，是后续踩坑高发区

## Step 2：字段定义本体（Ontology）

对每个 Sheet 每一列产出：字段名、业务含义、数据类型、计算关系、所属表。写到 `02_ontology/`。

- **跨表同名概念必须合并**：工号 / 员工编号 / 人员编码 是同一个实体，本体里只有一条
- **按业务域组织**，不要按 Sheet 顺序平铺（如：主数据 / 考勤 / 绩效 / 薪酬 / 成本）
- **标注依赖方向**：`绩效工资 ← 绩效表.绩效系数 × 绩效基数`
- 另起一节做**字段角色标注**：人工输入 / 系统带出 / 中间计算 / 最终输出 / 校验列 / "公式勿动"
- 再起一节记**取值陷阱**：`/` 表示不参加、空表示在职、负数合法但需确认……
- 不确定的地方写进「待确认问题」清单，别猜着填
- 目标读者是"下一个接手的 AI"，写成它读一遍就能问答的形式

## Step 3：公式链与数据血缘

**分层公式链**——一定要分层，扁平罗列没有信息量：

```
第一层 输入      A=基本工资 ← 调薪表   B1..B8=浮动项 ← 提成/绩效表
第二层 中间量    B=ΣB1..B8   C=ΣC1..C5   D=ΣD1..D5
第三层 应发      G = A + B - C + D + E - F
第四层 税前      L = G - H - I - J - K
第五层 实发      R = L - Q（个税，累计预扣法）
```

**跨表血缘**——每条写清 `源 Sheet.字段 → 目标 Sheet.字段 / 连接键 / 说明`；链路复杂时补一张 ASCII 流向图。

- 公式经常**不在单元格里，而在列名里**（`应发工资G=A+B-C+D+E-F`）。中文列名、字母编号（A/B1/C3）混排是常态，照单全收
- 区分输入层 / 中间计算层 / 输出层，What-If 推演的能力完全建立在这个分层上
- 把所有校验逻辑（check 列、Countif、汇总行）单独列一节——它们是免费的验证锚点
- 单元格里真有公式的（Step 1 已抽出），拿来和你从列名推断的逻辑对照，不一致时以真实公式为准
- 最后列一张「可扰动的输入点 → 影响层级」表，Step 5 的 What-If 直接照着做

## Step 4：验证——本方法论的核心

把 Step 2/3 的理解写成 `spec.json`（用 `write_file`），让脚本用**全量真实数据**逐行回算，与 Excel 现有值比对。

```
python3 <resources_path>/scripts/excel_ai.py verify spec.json -o ./03_verify
```

最小可用骨架（全字段说明与完整示例见 `references/spec-schema.md`）：

```jsonc
{
  "workbook": "/abs/path/表.xlsx",
  "sheet": "工资明细表",
  "header_rows": 4,                                  // 表头占几行，数错一行全废
  "keys":       {"ID": "工号", "NAME": "姓名"},        // 值可写列名(模糊匹配)或列号
  "dimensions": {"DEPT": "一级部门"},                  // 分析维度
  "fields":     {"A": "基本工资A", "B1": 36, "E": 54, "F": 55, "G_x": "应发工资G"},
  "derived":    {"B": "B1+B2+B3", "C": "C1+C2"},      // 中间量，按声明顺序求值
  "checks": [
    {"name": "应发工资G", "target": "G_x",             // target = Excel 里已有的结果列
     "expr": "round(A+B-C+D+E-F, 2)", "tolerance": 0.01}
  ],
  "skip_when": {"empty": ["ID"], "label_in": ["汇总", "合计", "总计"]}
}
```

产出 `03_verify/验证报告.md` + `verification_detail.csv` + `mismatches.csv`（均 utf-8-sig）。

规则要点：

- 列名匹配到多列会**直接报错**并列出候选，这时改用列号，别去猜
- `target` 是 Excel 现有结果列，`expr` 是你理解的算法——**两者对撞才叫验证**；
  `checks` 里没有 `target` 的项不成立，`checks` 为空脚本会直接报错
- `checks` 里每一项尽量**展开到输入层**，而不是引用上一层的结果列：这样某层错了不会
  连锁污染下面所有校验项，能一眼看出问题出在哪一层
- 金额容差 0.01，比率容差 0.0001；**不要为了让报告好看去放大容差**
- 表达式白名单：`+ - * / ** %`、比较与 `and/or/not`、三元 `x if c else y`、
  函数 `abs round min max int float sum floor ceil`；非数值单元格按 0.0 参与运算；
  每个变量还有一个 `<变量名>__raw` 拿到原始字符串（用来区分 `/` 和真正的 0）

**读结果的纪律：**

- 通过率 100% 才算"AI 学会了这套业务逻辑"，可以进 Step 5
- 有不匹配时，**先别假设是自己错**。两种可能：你理解错了，**或这张 Excel 本身算错了**。
  看差异模式：差一个固定值 → 几乎总是漏了某一项；差一个比例 → 系数/口径不同；
  只有零星几行差 → 多半是 Excel 里的人为覆盖或错误，**这恰恰是最有价值的发现**，
  要单独列出来交给用户核（附工号/姓名/行号/差额），不要悄悄改 `expr` 把它"抹平"
- 结论要明确写给用户：多少条 × 多少项公式、通过率多少、不匹配的那几条到底是谁的错

## Step 5：交付

```
python3 <resources_path>/scripts/excel_ai.py output  spec.json -d ./03_verify/verification_detail.csv -o ./04_output
python3 <resources_path>/scripts/excel_ai.py analyze spec.json -d ./03_verify/verification_detail.csv -o ./04_output
```

- `output` → `AI处理结果.xlsx`：蓝 `DAEEF3`=原始输入、绿 `E2EFDA`=AI 计算、橙 `FCE4D6`=存在差异，
  另附「校验汇总」「数据血缘」「字段本体」三个 Sheet（内容取自 spec 的 `lineage` / `ontology` 段——
  这两段不写就是空表，记得把 Step 2/3 的结论填进去）以及公式说明区与图例
- `analyze` → `分析报告.md`：分组汇总（数量/总额/人均/占比）、取值分布、Top/Bottom、
  异常检测（IQR / Z-score 离群 + 自定义规则）、What-If 推演

```jsonc
"analysis": {
  "group_by":      [{"dim": "DEPT", "metrics": ["G"], "count_as": "人数"}],
  "distributions": [{"dim": "GRADE"}, {"field": "G", "bins": [8000, 15000, 30000]}],
  "top_n":         [{"field": "G", "n": 5, "label": "NAME"}],
  "outliers":      [{"field": "G", "method": "iqr", "k": 1.5, "label": "NAME"}],
  "rules":         [{"name": "不参加考核却有绩效", "when": "COEF__raw == \"/\" and B1 > 0", "label": "NAME"}],
  "what_if":       [{"name": "基本工资上调10%", "set": {"A": "A*1.1"}, "recompute": ["B", "C"],
                     "targets": [{"name": "应发G", "expr": "A+B-C+D+E-F"}], "label": "NAME"}]
}
```

各小节的必填/可选项见 `references/spec-schema.md` 第 8 节。
**改了输入就要把依赖它的中间量写进 `recompute`**，否则 What-If 情景值等于没变。

脚本给的是骨架。**真正的洞察要你在报告基础上再写一段结论**：钱花在哪、
哪些异常需要人去核、哪个情景对总成本的杠杆最大。最后把 `spec.json` 和产物路径一并交给用户。

---

## 通用踩坑速查

细节与处置办法见 `references/pitfalls.md`，这里只留一行提醒：

1. **多行表头**：常见 2~4 行（大标题 + 分组表头 + 字段名 + 单位），`header_rows` 要数准
2. **合并单元格**：表头要铺开再拼列名；数据区默认**不铺**（铺了金额会翻倍），确需铺开用 `fill_merged`
3. **"公式勿动/勿删"**：系统自动算的列，是结果不是输入，别当输入喂进 `expr`
4. **check 列**：原作者的断言，优先拿来做验证锚点
5. **`/`、`-`、"不适用"**：中文表里表示"不参加/无此项"，按 0 处理但业务上要和真正的 0 区分——
   `COEF == 0` 会同时命中两者，用 `COEF__raw` 区分
6. **汇总行/小计行**：混在数据体里，用 `skip_when.label_in` 排掉，否则金额翻倍
7. **离职/中途入职人员**：验证不匹配的高发人群，单独看一眼
8. **浮点误差**：每层各自 `round(x, 2)`（不是最后统一舍入），比较用容差不用 `==`
9. **CSV 编码**：一律 `utf-8-sig`，否则用户用 Excel 打开是乱码
10. **不要改用户的原表**：所有产物写到独立输出目录
11. **公式列显示"全空"**：这个 xlsx 没有缓存值（多半是程序生成的）。用 Excel/LibreOffice
    另存一次，或 `soffice --headless --convert-to xlsx` 重算
12. **`.xls` 老格式**：脚本只吃 `.xlsx`/`.xlsm`，先让用户另存为 `.xlsx`

## 目录约定

在工作区（或会话草稿目录）下建一个分析目录，内部结构固定：

```
01_raw_md/     Step 1 结构化 MD + 索引
02_ontology/   Step 2/3 本体、公式链、血缘（AI 手写）
03_verify/     Step 4 验证报告 + 逐行明细 CSV + 不匹配清单
04_output/     Step 5 结果 Excel + 分析报告
spec.json      AI 对业务逻辑的形式化理解
```

`spec.json` 是最值钱的产物：它是这张 Excel 的业务逻辑被机器可执行地记录下来的唯一形式。
下个月表格再来一份，改个 `workbook` 路径就能重跑全流程。所以**每次都要把 spec.json 交给用户**，
并告诉他这份文件的意义（可以存进仓库、可以复用、可以交给同事）。

## 随取随读的参考文档

都在 `<resources_path>/references/` 下。优先用 `read_file` 读；
如果因为超出会话根目录被拒，就用 `run_shell` 的 `cat` 读。**按需读，不要一次全读进上下文。**

| 文件 | 什么时候读 |
|---|---|
| `references/spec-schema.md` | 写 `spec.json` 之前（Step 4/5）。全字段说明、取值规则、一份可直接改的完整示例、常见报错对照 |
| `references/pitfalls.md` | Step 1 读完 MD 觉得表结构不对劲时；Step 4 出现不匹配时。踩坑清单的完整解释与处置动作 |
| `references/walkthrough.md` | 第一次做、或拿不准每一步该产出什么时。一张工资表从 0 到 5 的完整演练，含真实命令与产物样貌 |

## 依赖与兜底

缺依赖时：`pip3 install pandas openpyxl`（必要时加 `--break-system-packages`）。
万一 `scripts/excel_ai.py` 被裁掉了，四个子命令的必要行为写在
`references/spec-schema.md` 的「附录」里，照着现写一份，别手算。
