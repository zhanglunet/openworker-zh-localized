# spec.json 全字段说明

`spec.json` 是**你对这张 Excel 业务逻辑的形式化理解**，也是 `verify` / `output` / `analyze`
三个子命令共用的唯一输入。写它之前先读完 Step 1 的 MD，写完 Step 2/3 的本体与公式链。

用 `write_file` 把它写成文件，**不要用 heredoc 内联进 shell 命令**。
JSON 不支持注释——本文里的 `//` 只是讲解，抄进去要删掉。

---

## 0. 顶层结构一览

| 字段 | 必填 | 用于 | 说明 |
|---|---|---|---|
| `workbook` | ✅ | verify | Excel 路径。绝对路径最稳；相对路径按 **spec.json 所在目录**解析 |
| `sheet` | ✅ | verify | Sheet 名（精确名，取自 Step 1 的索引） |
| `header_rows` | ✅ | verify | 表头占几行（0-based 数据体起始行号）。**数错一行全废** |
| `keys` | 建议 | verify/analyze | 标识列：工号、单号、物料编码。值是字符串 |
| `dimensions` | 建议 | verify/analyze | 分析维度：部门、岗位、产品线。值是字符串 |
| `fields` | ✅ | verify/analyze | 参与计算的数值列 + **所有 `target` 结果列**。值是 float |
| `derived` | 可选 | verify/analyze | 中间量，按**声明顺序**求值，可引用前面的 derived |
| `checks` | ✅ | verify | 校验项：`target`（Excel 现值）对撞 `expr`（你的理解） |
| `skip_when` | 建议 | verify | 排除空行、汇总/小计行 |
| `fill_merged` | 可选 | verify | 数据区需要向下铺开合并单元格的变量名列表 |
| `cross_checks` | 可选 | verify | 跨表一致性（源表的值有没有正确传过来） |
| `lineage` | 可选 | output | 写进结果表「数据血缘」Sheet 的内容 |
| `ontology` | 可选 | output | 写进结果表「字段本体」Sheet 的内容 |
| `analysis` | 可选 | analyze | 分组/分布/TopN/离群/规则/What-If 的配置 |

---

## 1. 定位：`workbook` / `sheet` / `header_rows`

```jsonc
{
  "workbook": "/Users/you/OpenWorker/s-42/2025年10月工资表.xlsx",
  "sheet": "工资明细表",
  "header_rows": 4
}
```

- `header_rows` 就是"数据体从第几行开始"（0-based）。Step 1 的 MD 里给了推断值，
  但**必须自己数一眼**：多了一行会把第一条真实数据当表头，少了一行会把表头当数据。
- `header_rows` ≥ 总行数会直接报错。

## 2. 列引用：`keys` / `dimensions` / `fields`

三段的写法一样：`{"变量名": 列引用}`。变量名是你在 `expr` 里用的名字（建议用公式链里的
A/B1/G 或简短英文），列引用可以是：

- **列名（字符串）**：先按归一化后**精确**匹配（去掉所有空白/全角空格再比），
  没有唯一命中再按**包含**匹配。多行表头的拼接列名形如 `工资项 / 基本工资A`，
  写 `"基本工资A"` 就能包含命中。
- **列号（整数，0-based）**：`36` 表示第 37 列。也可以写字符串 `"36"`。

> **命中多列 = 直接报错**，并把候选列号列出来。这时**改用列号**，不要靠调整字眼去碰运气。

三段的区别：

| 段 | 求值类型 | 典型用途 |
|---|---|---|
| `keys` | 字符串 | 工号、姓名、单号——出现在明细/不匹配清单里，方便人去核 |
| `dimensions` | 字符串 | 部门、岗位——`analysis.group_by` / `distributions` 用 |
| `fields` | float（非数值按 0.0） | 所有参与算术的列 **以及每个 `checks.target`** |

**`checks` 的 `target` 必须放在 `fields` 里**（放进 `keys`/`dimensions` 会因为拿到字符串而报错）。

每个变量还自动附带一个 `<变量名>__raw`，值是**该单元格的原始字符串**：

```jsonc
"rules": [{"name": "不参加考核（/）却发了绩效", "when": "COEF__raw == \"/\" and B1 > 0"}]
```

这是区分「真正的 0」和「`/` 表示不参加」的唯一办法（见 `pitfalls.md` 第 5 条）。

## 3. `derived`：中间量

```jsonc
"derived": {
  "B": "B1+B2+B3+B4+B5+B6+B7+B8",
  "C": "C1+C2+C3+C4+C5",
  "G": "round(A+B-C+D+E-F, 2)"        // 可以引用前面已声明的 derived
}
```

- 按**声明顺序**求值，所以被引用者必须写在前面（JSON 对象顺序脚本会保留）。
- 变量名不能和 `keys`/`dimensions`/`fields` 里的重名（会报错）。
- `derived` 变量会出现在明细 CSV 里，`analysis` 可以直接用；
  但 `cross_checks.compare.left` **不支持 derived**，要比对就把它写进 `fields`。

## 4. `checks`：验证项（本方法论的核心）

```jsonc
"checks": [
  {"name": "应发工资G", "target": "G_x",
   "expr": "round(A+B-C+D+E-F, 2)", "tolerance": 0.01},
  {"name": "税前工资L", "target": "L_x",
   "expr": "round(A+B-C+D+E-F-H-I-J-K, 2)", "tolerance": 0.01}   // 展开到输入层，不引用 G
]
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | ✅ | 校验项名，不能重复；会成为明细 CSV 的三列前缀 `名·AI` / `名·Excel` / `名·差异` |
| `target` | ✅ | **Excel 里已有的结果列**对应的 `fields` 变量 |
| `expr` | ✅ | 你理解的算法 |
| `tolerance` | 否 | 默认 `0.01`。金额 0.01、比率 0.0001 |

纪律：

- `checks` 为空脚本直接报错——**没有校验项就不叫验证**。
- 每一项尽量**展开到输入层**，不要引用上一层的结果列：某一层错了才不会连锁污染下面所有项，
  能一眼看出问题出在哪一层。
- **不要为了让报告好看去放大 `tolerance`**。容差放大掩盖的正是最值钱的发现。

### 表达式语法（`expr` / `derived` / `rules.when` / `what_if` 共用一个安全求值器）

- 算术：`+ - * / ** %`，一元 `-`
- 比较：`== != < <= > >=`；布尔：`and or not`；三元：`x if cond else y`
- 函数白名单：`abs round min max int float sum floor ceil`
- 字符串字面量可用（配合 `__raw` 做文本判断）
- **禁止**：属性访问（`x.y`）、下标（`x[0]`）、导入、其他任何函数调用、赋值
- 非数值单元格（`/`、`-`、空、备注文字）在 `fields` 里一律按 `0.0` 参与运算

## 5. `skip_when` / `fill_merged`

```jsonc
"skip_when": {
  "empty": ["ID"],                                  // 这些变量为空的行跳过（离职空行、格式行）
  "label_in": ["汇总", "合计", "总计", "小计"]        // 整行任一单元格含这些词 → 判为汇总行跳过
},
"fill_merged": ["DEPT"]                             // 仅这些列在数据区向下铺开合并单元格
```

- 全空行自动跳过，不用配。
- `label_in` 是**整行任一单元格包含**即命中，词别取太泛（比如 `"总"` 会误伤"总监"）。
- 数据区的合并单元格**默认不铺开**（铺开会让金额随合并区行数翻倍）。只有"部门列合并了 5 行、
  下面 4 行是空"这种维度列才用 `fill_merged` 显式铺。
- 如果报「没有任何数据行参与比对」，就是 `header_rows` 或 `skip_when` 过严了。

## 6. `cross_checks`：跨表一致性

回答"源表的值有没有正确传到主表"——Step 3 血缘的可执行版本。

```jsonc
"cross_checks": [
  {"name": "绩效系数传递",
   "workbook": "/abs/绩效表.xlsx",      // 相对路径按 spec.json 所在目录解析
   "sheet": "月考月发",
   "header_rows": 4,                    // 右表的表头行数，默认 1
   "key": "工号",                        // 右表的连接列（列名或列号）
   "left_key": "ID",                     // 主表里的连接变量（keys/dimensions/fields 之一）
   "compare": [
     {"left": "COEF", "right": "绩效系数", "tolerance": 0.001}   // tolerance 默认 0.001
   ]}
]
```

- 右表 key 重复时会在报告里列出重复键（只保留首行），这本身往往就是数据质量问题。
- 主表有、右表找不到的键会进「未匹配」清单——离职/新入职人员的高发区。
- `compare.left` 只能是主表的 `keys`/`dimensions`/`fields` 变量，**不能是 `derived`**。

## 7. `lineage` / `ontology`：写进结果表

`output` 会把这两段渲染成「数据血缘」「字段本体」两个 Sheet。**不写就是空表**——
Step 2/3 辛苦写的结论要在这里落进交付物。

接受 字符串 / 字符串数组 / 对象 / **对象数组（渲染成表格，key 作表头）**：

```jsonc
"lineage": [
  {"源": "绩效表.月考月发.绩效系数", "目标": "工资表.B1 绩效工资", "连接键": "工号",
   "说明": "系数 × 绩效基数，系数为 / 表示不参加考核"},
  {"源": "考勤表.出勤天数", "目标": "工资表.C2 缺勤扣款", "连接键": "工号",
   "说明": "按 21.75 天折算"}
],
"ontology": {
  "主数据": [{"字段": "ID", "含义": "工号，全公司唯一", "角色": "人工输入"}],
  "薪酬":   [{"字段": "A", "含义": "基本工资，来自调薪表", "角色": "系统带出"},
             {"字段": "G_x", "含义": "应发工资，公式勿动", "角色": "最终输出"}]
}
```

## 8. `analysis`：Step 5 报告配置

`analyze` 读的是 `verify` 产出的明细 CSV，所以**能用的变量 = `keys` + `dimensions` +
`fields` + `derived`**，另外每个 `checks.name` 若是合法标识符也会以其 **AI 值**暴露。

```jsonc
"analysis": {
  "group_by":      [{"dim": "DEPT", "metrics": ["G", "L"], "count_as": "人数"}],
  "distributions": [{"dim": "GRADE"},
                    {"field": "G", "bins": [5000, 10000, 20000, 50000]}],
  "top_n":         [{"field": "G", "n": 5, "label": "NAME"}],
  "outliers":      [{"field": "G", "method": "iqr", "k": 1.5, "label": "NAME"},
                    {"field": "B1", "method": "zscore", "z": 3.0, "label": "NAME"}],
  "rules": [{"name": "不参加考核却有绩效工资", "when": "COEF__raw == \"/\" and B1 > 0",
             "label": "NAME", "show": ["COEF", "B1"]}],
  "what_if": [{"name": "基本工资上调10%", "set": {"A": "A*1.1"},
               "recompute": ["B", "C", "D"],
               "targets": [{"name": "应发G", "expr": "A+B-C+D+E-F"}],
               "label": "NAME"}]
}
```

| 小节 | 必填 | 可选 |
|---|---|---|
| `group_by` | `dim` | `metrics`（数值变量数组）、`count_as`（计数列名，默认"数量"） |
| `distributions` | `dim` 或 `field` | `bins`（数值边界数组 → 分箱；不给则按取值枚举，最多列 40 种） |
| `top_n` | `field` | `n`（默认 5）、`label`（默认第一个 key）。同时出 Top 和 Bottom |
| `outliers` | `field` | `method`（`iqr` 默认 / 其他值走 zscore）、`k`（默认 1.5）、`z`（默认 3.0）、`label` |
| `rules` | `when` | `name`、`label`、`show`（额外展示的变量数组） |
| `what_if` | `set`、`targets` | `recompute`（必须是 `derived` 里的变量）、`name`、`label` |

What-If 的执行顺序：`set` 里的表达式在**原始环境**上求值 → 覆盖进情景环境 →
按 `spec.derived` 的声明顺序重算 `recompute` 列出的中间量 → 对每个 `target` 出
「现状 / 情景 / 变化」三列，外加合计行与变化率。所以：
**改了输入就要把依赖它的中间量写进 `recompute`**，否则情景值等于没变。

---

## 9. 一份可以直接改的完整示例

```json
{
  "workbook": "/Users/you/OpenWorker/s-42/2025年10月工资表.xlsx",
  "sheet": "工资明细表",
  "header_rows": 4,
  "keys":       {"ID": "工号", "NAME": "姓名"},
  "dimensions": {"DEPT": "一级部门", "GRADE": "职级"},
  "fields": {
    "A": "基本工资A",
    "B1": 36, "B2": 37, "B3": 38,
    "C1": "养老保险", "C2": "医疗保险",
    "D": "补发补扣D", "E": "补贴E", "F": "扣款F",
    "H": "个人社保H", "I": "个人公积金I", "J": "工会费J", "K": "其他扣款K",
    "COEF": "绩效系数",
    "G_x": "应发工资G", "L_x": "税前工资L"
  },
  "derived": {
    "B": "B1+B2+B3",
    "C": "C1+C2",
    "G": "round(A+B-C+D+E-F, 2)"
  },
  "checks": [
    {"name": "应发工资G", "target": "G_x",
     "expr": "round(A+B-C+D+E-F, 2)", "tolerance": 0.01},
    {"name": "税前工资L", "target": "L_x",
     "expr": "round(A+B-C+D+E-F-H-I-J-K, 2)", "tolerance": 0.01}
  ],
  "skip_when": {
    "empty": ["ID"],
    "label_in": ["汇总", "合计", "总计", "小计"]
  },
  "cross_checks": [
    {"name": "绩效系数传递",
     "workbook": "/Users/you/OpenWorker/s-42/2025年10月绩效表.xlsx",
     "sheet": "月考月发", "header_rows": 4,
     "key": "工号", "left_key": "ID",
     "compare": [{"left": "COEF", "right": "绩效系数", "tolerance": 0.001}]}
  ],
  "lineage": [
    {"源": "绩效表.月考月发.绩效系数", "目标": "工资表.B1 绩效工资", "连接键": "工号",
     "说明": "绩效工资 = 绩效系数 × 绩效基数；系数 / 表示不参加考核"}
  ],
  "ontology": {
    "主数据": [{"字段": "ID", "含义": "工号，全公司唯一", "角色": "人工输入"},
               {"字段": "DEPT", "含义": "一级部门", "角色": "系统带出"}],
    "薪酬":   [{"字段": "A", "含义": "基本工资，来自调薪表", "角色": "系统带出"},
               {"字段": "G_x", "含义": "应发工资（列名标注公式勿动）", "角色": "最终输出"}]
  },
  "analysis": {
    "group_by":      [{"dim": "DEPT", "metrics": ["G"], "count_as": "人数"}],
    "distributions": [{"dim": "GRADE"}, {"field": "G", "bins": [8000, 15000, 30000]}],
    "top_n":         [{"field": "G", "n": 10, "label": "NAME"}],
    "outliers":      [{"field": "G", "method": "iqr", "k": 1.5, "label": "NAME"}],
    "rules": [
      {"name": "不参加考核却有绩效工资", "when": "COEF__raw == \"/\" and B1 > 0",
       "label": "NAME", "show": ["B1"]},
      {"name": "应发为负", "when": "G < 0", "label": "NAME", "show": ["A", "F"]}
    ],
    "what_if": [
      {"name": "基本工资普调 5%", "set": {"A": "A*1.05"}, "recompute": ["B", "C", "G"],
       "targets": [{"name": "应发G", "expr": "A+B-C+D+E-F"}], "label": "NAME"}
    ]
  }
}
```

---

## 10. 常见报错 → 该改哪里

| 报错关键字 | 原因 | 处置 |
|---|---|---|
| `缺少必填字段 workbook / sheet / header_rows` | 顶层三件套没写全 | 补上；`header_rows` 从 Step 1 的 MD 抄并自己确认 |
| `列名「X」精确/包含命中 N 列` | 列名重复 | **改用列号**（0-based，MD 的列字段表里有），别改字眼碰运气 |
| `列号越界` | 列号写成 1-based 了 | 列号 0-based，合法范围 `0..列数-1` |
| `变量名重复定义` | 同名出现在 keys/dimensions/fields 多段 | 改名 |
| `derived 变量 X 与 ... 重名` | derived 和列变量撞名 | 给 derived 换名（如 `G` vs `G_x`） |
| `checks 为空` | 只写了 fields 没写校验 | 没有校验项就不叫验证，补 `checks` |
| `checks[i] 的 target=X 未在 ... 中定义` | target 没进 `fields` | 把结果列加进 `fields` |
| `没有任何数据行参与比对` | `header_rows` 或 `skip_when` 过严 | 核对表头行数；放宽 `skip_when.empty` |
| `明细 CSV 与 spec 不匹配，缺少列` | 改了 spec 但没重跑 verify | 重跑 `verify` 再跑 `output`/`analyze` |
| `analysis.xxx 的 dim/field 不在明细列中` | 用了没在 spec 里定义的变量 | 只能用 keys/dimensions/fields/derived（+ 合法标识符的 check 名） |
| `what_if.recompute 中的 X 不是 spec.derived 里的变量` | recompute 只接受 derived | 把中间量写进 `derived` |

---

## 附录：脚本四个子命令的必要行为（scripts/ 缺失时照此现写）

单文件 `excel_ai.py`，依赖 `pandas` + `openpyxl`，**纯本地、零网络调用**。
下面每一条都是踩过的坑，别漏：

**`tomd`** — pandas `header=None` 读全表；openpyxl `data_only=False` 抽真实公式；
用 `range_boundaries` 把合并单元格的值铺满其覆盖区**再拼多行列名**（数据区不铺）；
跳过"整行只有一个取值且横跨大半张表"的大标题行；列类型按 `pd.to_numeric` 成功率判定
（≥95% 判数值，≥50% 标"含非数值"告警）；启发式定位数据体起始行（首个出现真实公式的行，
或首个"非空单元格中数值占比 ≥25%"的行）；识别汇总/小计行并从画像中排除；
对"有公式但取值全空"的列出严重告警；输出 `00-索引.md`。

**`verify`** — 读 spec.json；列引用支持列号（0-based）或列名（先精确后包含匹配，
**命中多列必须报错并列出候选**）；表达式用 `ast` 白名单求值（只放行算术/比较/布尔/三元 +
`abs round min max int float sum floor ceil`，**禁止属性访问、下标、导入、其他调用**）；
非数值单元格一律按 `0.0`，另以 `<变量名>__raw` 暴露原始字符串；按声明顺序先算 `derived`
再算 `checks`；逐行比对，超 `tolerance` 记为不匹配；产出 `验证报告.md`
（概况 / 列绑定 / 校验项定义与结果 / 不匹配明细 / 差异模式速查 / 汇总额对比 / 跨表一致性）
+ `verification_detail.csv`（每个校验项三列 `名·AI`、`名·Excel`、`名·差异`）+ `mismatches.csv`，
全部 `utf-8-sig`。

**`output`** — 读 detail CSV 写 `AI处理结果.xlsx`：蓝 `DAEEF3`=原始输入、绿 `E2EFDA`=AI 计算、
橙 `FCE4D6`=差异超容差；另附「校验汇总」「数据血缘」「字段本体」三个 Sheet
（后两者取自 spec 的 `lineage` / `ontology`）以及公式说明区 + 图例。

**`analyze`** — 读 detail CSV + `spec.analysis`：数值字段概览、分组汇总（数量/总额/人均/占比）、
取值分布（枚举或 `bins` 分箱）、Top/Bottom、离群（IQR `k` / Z-score `z`）、
规则异常（表达式，复用同一个安全求值器）、What-If（`set` 在原始环境求值 → 覆盖进情景环境 →
按 `derived` 声明顺序重算 `recompute` → 对 `targets` 出「现状/情景/变化」三组列 + 合计行）；
产出 `分析报告.md`。
