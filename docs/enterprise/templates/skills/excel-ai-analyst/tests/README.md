# excel_ai.py 的测试与对抗套件

这些文件**不参与技能运行**（OpenWorker 的 `SkillLoader` 只读 `SKILL.md`），它们是给维护者的：
每次跟进上游同步、或改动 `scripts/excel_ai.py` 之后跑一遍，确认没有回归。

## 依赖

```bash
pip3 install pandas openpyxl pytest    # 需要时加 --break-system-packages
```

## 跑法

```bash
cd <技能目录>          # 即 enterprise/skills/excel-ai-analyst

# 1) 基础用例（68 项，约 23 秒）
python3 -m pytest tests/test_excel_ai.py -q

# 2) 三套对抗套件（任一有攻破即非零退出）
python3 tests/attacks/dirty-data/run_attacks.py        # 93 项：脏数据与边界
python3 tests/attacks/security/run_all.py              # 表达式逃逸 / 注入 / 性能
python3 tests/attacks/spec-robustness/run_attacks.py   # 138 项：spec.json 鲁棒性
```

夹具是**按需生成**的（各套件自带 `make_*fixtures.py`，首次运行自动建 `fx/`），
仓库里只存源码，不存 xlsx 二进制与运行产物。

## 各套件守的是什么

| 套件 | 覆盖 |
|------|------|
| `test_excel_ai.py` | 四个子命令的规格符合性：多行表头拼接、合并单元格铺开、大标题行跳过、真实公式抽取、类型告警、验证通过率、重名列报错、汇总行排除、容差边界、三色标注、三个附加 Sheet、What-If 数值、不修改原表、CSV 为 utf-8-sig |
| `dirty-data` | 空表/单行表/全空列/超长列名/中文数字混排/日期列/科学计数法/负数/1 万行性能/无缓存值/Sheet 名冲突/全角减号 |
| `security` | 表达式求值器白名单逃逸（`__import__`、`open`、`__class__` 链、lambda、推导式、f-string、海象、`getattr` 变体）、资源上限（嵌套幂 DoS、`sum` 列表拼接、深度嵌套解析）、路径穿越、CSV/xlsx 公式注入 |
| `spec-robustness` | spec.json 字段缺失/拼错/类型错、`header_rows` 数错、列号越界、`tolerance` 异常值、`derived` 循环依赖、`checks` 引用不存在的变量、`cross_checks` 表不存在、`analysis` 段缺失、变量命名空间冲突、What-If 依赖链 |

## 一条重要的历史教训

`spec.json` 是 AI 手写的，**写错类型是常态而非例外**。对抗套件里被攻破最多的一类
就是「spec 类型污染」——`header_rows: "四"`、`fields` 写成数组、`checks[].target`
指向文本列等，早期版本一律直接 traceback。现在全部转成中文 `UserError` 并给出诊断。

第二类最危险的是**静默通过**：`header_rows` 少数一行会让字段名行被当数据行、
文本按 0.0 参与运算、`0 == 0` 判为通过，于是报告写着「100% ✅ 可以进入 Step 5」——
比崩溃危险得多。改动求值或列绑定逻辑时，务必重跑 `spec-robustness` 套件。
