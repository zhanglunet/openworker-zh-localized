#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spec.json 鲁棒性攻击套件。

攻击面（本轮职责）：
  spec.json 字段缺失 / 多余 / 类型错、header_rows 数错一行、列号越界、
  tolerance 为 0 或负、derived 循环依赖、checks 引用不存在的 derived、
  cross_checks 的表不存在、analysis 段缺失时 analyze 是否优雅退出、
  以及 1 万行的验证性能。

判定标准（任意一条命中即算"被攻破"）：
  * 出现未捕获的 traceback（应当是清晰的中文错误 + 非零退出码）
  * 错误的静默通过（期望报错却 rc=0；或期望至少要有告警却报告里只字未提）
  * 明显不合理的结果（数值错误、报告为空、产物缺失）
  * 性能不可接受（1 万行 verify 超过 60 秒）

用法：
  python3 run_attacks.py            # 跑全部
  python3 run_attacks.py 关键字      # 只跑 id/描述 命中关键字的用例
"""

import json
import os
from collections import OrderedDict
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
FX = os.path.join(HERE, "fx")
OUT = os.path.join(HERE, "out")
SCRIPT = os.path.abspath(os.path.join(HERE, "..", "..", "scripts", "excel_ai.py"))

B01 = os.path.join(FX, "B01_单行表头.xlsx")
B02 = os.path.join(FX, "B02_两行表头.xlsx")
B03 = os.path.join(FX, "B03_右表.xlsx")
B04 = os.path.join(FX, "B04_万行.xlsx")
B05 = os.path.join(FX, "B05_含汇总行.xlsx")

CASES = []


def case(cid, desc, cmd="verify", expect="error", must=None, forbid=None,
         spec=None, detail_from=None, timeout=180, extra=None):
    """
    expect: error = 必须非零退出且是中文 [错误]
            ok    = 必须 rc=0
            warn  = 必须 rc=0，且 must 里的关键字要出现在 stdout/stderr/产物里
    must   : 关键字列表（出现在 stdout+stderr+产物文本 里才算过）
    forbid : 关键字列表（不允许出现）
    """
    CASES.append(dict(id=cid, desc=desc, cmd=cmd, expect=expect, spec=spec,
                      must=must or [], forbid=forbid or [], detail_from=detail_from,
                      timeout=timeout, extra=extra or []))


# ---------------------------------------------------------------------------
# 基线 spec：B01 单行表头，G = A + B - C
# ---------------------------------------------------------------------------
def base(**over):
    s = {
        "workbook": B01,
        "sheet": "工资明细表",
        "header_rows": 1,
        "keys": {"ID": "工号", "NAME": "姓名"},
        "dimensions": {"DEPT": "一级部门"},
        "fields": {"A": "基本工资A", "B": "绩效B", "C": "扣款C", "G_x": "应发工资G"},
        "checks": [{"name": "应发G", "target": "G_x", "expr": "round(A + B - C, 2)",
                    "tolerance": 0.01}],
        "skip_when": {"empty": ["ID"]},
    }
    for k, v in over.items():
        if v is _DEL:
            s.pop(k, None)
        else:
            s[k] = v
    return s


class _Del(object):
    def __repr__(self):
        return "<删除>"


_DEL = _Del()


# ===========================================================================
# 一、spec 字段缺失
# ===========================================================================
case("S01", "缺 workbook", spec=base(workbook=_DEL))
case("S02", "缺 sheet", spec=base(sheet=_DEL))
case("S03", "缺 header_rows", spec=base(header_rows=_DEL))
case("S04", "缺 checks", spec=base(checks=_DEL))
case("S05", "checks 是空数组", spec=base(checks=[]))
case("S06", "checks[0] 缺 target", spec=base(checks=[{"name": "x", "expr": "A+B"}]))
case("S07", "checks[0] 缺 expr", spec=base(checks=[{"name": "x", "target": "G_x"}]))
case("S08", "缺 fields（target 无处可寻）", spec=base(fields=_DEL))

# ===========================================================================
# 二、spec 多余 / 拼错字段（最危险的一类：静默生效成默认值）
# ===========================================================================
case("S10", "顶层多写一个无害的说明字段 note", expect="ok",
     spec=base(note="这是给人看的备注"))
case("S11", "checks 拼成 checkss（顶层键名错）", spec=base(checks=_DEL, checkss=[
    {"name": "应发G", "target": "G_x", "expr": "A+B-C"}]))
case("S12", "tolerance 拼成 tolerence（会静默退回默认 0.01）", expect="error",
     spec=base(checks=[{"name": "应发G", "target": "G_x", "expr": "round(A+B-C,2)",
                        "tolerence": 5.0}]))
case("S13", "skip_when 拼成 skipwhen（汇总行会混进来）", expect="error",
     must=["skip_when"],
     spec=base(workbook=B05, skipwhen={"label_in": ["小计", "合计"]}, skip_when=_DEL))
case("S13b", "根本没写 skip_when（汇总行必须被高声点名，但不该报错）", expect="warn",
     must=["疑似未排除的汇总行", "翻倍"],
     spec=base(workbook=B05, skip_when=_DEL))
case("S14", "keys 拼成 key（明细里会没有工号列）", expect="error",
     spec=base(keys=_DEL, key={"ID": "工号"}, skip_when=_DEL))
case("S15", "dimensions 拼成 dimension", expect="error",
     spec=base(dimensions=_DEL, dimension={"DEPT": "一级部门"}))
case("S16", "checks[0] 多写一个 targets（复数）", expect="error",
     spec=base(checks=[{"name": "应发G", "target": "G_x", "expr": "round(A+B-C,2)",
                        "targets": "G_x"}]))

# ===========================================================================
# 三、类型错
# ===========================================================================
case("T01", "header_rows 写成中文'四'", spec=base(header_rows="四"))
case("T02", "header_rows 写成小数 2.5", spec=base(header_rows=2.5))
case("T03", "header_rows 写成布尔 true", spec=base(header_rows=True))
case("T04", "header_rows 写成 null", spec=base(header_rows=None))
case("T05", "keys 写成数组", spec=base(keys=["ID"]))
case("T06", "fields 的值写成 null", spec=base(fields={"A": None, "G_x": "应发工资G"}))
case("T07", "fields 的值写成对象", spec=base(fields={"A": {"col": 3}, "G_x": "应发工资G"}))
case("T08", "fields 的值写成布尔", spec=base(fields={"A": True, "G_x": "应发工资G"}))
case("T09", "checks 写成对象而不是数组",
     spec=base(checks={"name": "x", "target": "G_x", "expr": "A"}))
case("T10", "checks[0] 写成字符串", spec=base(checks=["应发G = A+B-C"]))
case("T11", "checks[0].expr 写成数组", spec=base(
    checks=[{"name": "x", "target": "G_x", "expr": ["A", "+", "B"]}]))
case("T12", "skip_when 写成字符串", spec=base(skip_when="汇总"))
case("T13", "skip_when.label_in 写成单个字符串（应当容忍）", expect="ok",
     spec=base(skip_when={"empty": ["ID"], "label_in": "合计"}))
case("T14", "derived 写成数组", spec=base(derived=["A+B"]))
case("T15", "derived 的值写成数字", spec=base(derived={"S": 3}))
case("T16", "workbook 写成数字", spec=base(workbook=123))
case("T17", "sheet 写成数字", spec=base(sheet=0))
case("T18", "tolerance 写成文本 'abc'", spec=base(
    checks=[{"name": "x", "target": "G_x", "expr": "A+B-C", "tolerance": "abc"}]))
case("T19", "tolerance 写成布尔", spec=base(
    checks=[{"name": "x", "target": "G_x", "expr": "A+B-C", "tolerance": True}]))
case("T20", "fill_merged 写成对象", spec=base(fill_merged={"DEPT": True}))
case("T21", "spec 顶层是数组", spec=[1, 2, 3])
case("T22", "spec 顶层是字符串", spec="工资表")
case("T23", "cross_checks 写成对象", spec=base(cross_checks={"name": "x"}))
case("T24", "keys 的值写成数字数组", spec=base(keys={"ID": [0]}))

# ===========================================================================
# 四、header_rows 数错一行
# ===========================================================================
case("H01", "两行表头却写 header_rows=1（字段名行会被当成数据行）", expect="warn",
     must=["疑似表头行", "0==0"], forbid=["**结论：** ✅ 全部通过"],
     spec={"workbook": B02, "sheet": "工资明细表", "header_rows": 1,
           "keys": {"ID": 0, "NAME": 1}, "dimensions": {"DEPT": 2},
           "fields": {"A": 3, "B": 4, "C": 5, "G_x": 6},
           "checks": [{"name": "应发G", "target": "G_x", "expr": "round(A+B-C,2)",
                       "tolerance": 0.01}]})
case("H02", "两行表头写对 header_rows=2（基线，必须 5 行数据）", expect="ok",
     must=["参与比对的数据行 | 5", "**结论：** ✅ 全部通过"],
     forbid=["疑似表头行", "与脚本推断不一致", "有水分"],
     spec={"workbook": B02, "sheet": "工资明细表", "header_rows": 2,
           "keys": {"ID": 0, "NAME": 1}, "dimensions": {"DEPT": 2},
           "fields": {"A": 3, "B": 4, "C": 5, "G_x": 6},
           "checks": [{"name": "应发G", "target": "G_x", "expr": "round(A+B-C,2)",
                       "tolerance": 0.01}]})
case("H03", "两行表头写成 3（第一行数据被当表头吃掉）", expect="warn",
     must=["与脚本推断不一致"],
     spec={"workbook": B02, "sheet": "工资明细表", "header_rows": 3,
           "keys": {"ID": 0, "NAME": 1}, "dimensions": {"DEPT": 2},
           "fields": {"A": 3, "B": 4, "C": 5, "G_x": 6},
           "checks": [{"name": "应发G", "target": "G_x", "expr": "round(A+B-C,2)",
                       "tolerance": 0.01}]})
case("H04", "header_rows 等于总行数", spec=base(header_rows=9))
case("H05", "header_rows 超大", spec=base(header_rows=10 ** 6))
case("H06", "header_rows 负数", spec=base(header_rows=-1))
case("H07", "header_rows=0（列名全部失效，却用列名引用）",
     spec=base(header_rows=0))

# ===========================================================================
# 五、列号越界 / 列引用
# ===========================================================================
case("C01", "fields 列号 999 越界", spec=base(fields={"A": 999, "G_x": 6}))
case("C02", "fields 列号 -1", spec=base(fields={"A": -1, "G_x": 6}))
case("C03", "fields 列号写成字符串 '999'", spec=base(fields={"A": "999", "G_x": 6}))
case("C04", "keys 列号越界", spec=base(keys={"ID": 42}))
case("C05", "列号刚好等于列数（差一）", spec=base(fields={"A": 7, "G_x": 6}))
case("C06", "列名根本不存在", spec=base(fields={"A": "不存在的列", "G_x": "应发工资G"}))
case("C07", "列号 0 合法（工号列当数值字段用）", expect="ok",
     spec=base(fields={"A": "基本工资A", "B": "绩效B", "C": "扣款C", "G_x": 6}))

# ===========================================================================
# 六、tolerance 为 0 / 负 / 荒谬地大
# ===========================================================================
case("V01", "tolerance = 0（合法，且必须仍然全通过）", expect="ok",
     forbid=["不匹配次数 | 1"],
     spec=base(checks=[{"name": "应发G", "target": "G_x", "expr": "round(A+B-C,2)",
                        "tolerance": 0}]))
case("V02", "tolerance = -1", spec=base(
    checks=[{"name": "x", "target": "G_x", "expr": "A+B-C", "tolerance": -1}]))
case("V03", "tolerance = 1e9（把真实差异掩盖成通过）", expect="warn",
     must=["仅因为容差被放大才判为「通过」", "远大于建议值"],
     forbid=["**结论：** ✅ 全部通过"],
     spec=base(checks=[{"name": "应发G", "target": "G_x", "expr": "round(A+B-C+1000,2)",
                        "tolerance": 1e9}]))
case("V04", "tolerance = 'NaN'", spec=base(
    checks=[{"name": "x", "target": "G_x", "expr": "A+B-C", "tolerance": "NaN"}]))
case("V05", "tolerance = 1e400（JSON 解析成 Infinity）", spec=base(
    checks=[{"name": "x", "target": "G_x", "expr": "A+B-C", "tolerance": 1e400}]))
case("V06", "tolerance = 'Infinity' 字符串", spec=base(
    checks=[{"name": "x", "target": "G_x", "expr": "A+B-C", "tolerance": "Infinity"}]))

# ===========================================================================
# 七、derived 循环依赖 / 顺序
# ===========================================================================
case("D01", "derived 自引用 {'S': 'S+1'}", must=["derived"],
     spec=base(derived={"S": "S + 1"},
               checks=[{"name": "x", "target": "G_x", "expr": "S", "tolerance": 0.01}]))
case("D02", "derived 两两循环 {'P':'Q+1','Q':'P+1'}", must=["derived"],
     spec=base(derived={"P": "Q + 1", "Q": "P + 1"},
               checks=[{"name": "x", "target": "G_x", "expr": "P", "tolerance": 0.01}]))
case("D03", "derived 三角循环 P→Q→R→P", must=["derived"],
     spec=base(derived={"P": "R + 1", "Q": "P + 1", "R": "Q + 1"},
               checks=[{"name": "x", "target": "G_x", "expr": "P", "tolerance": 0.01}]))
case("D04", "derived 声明顺序颠倒（TOT 用了后面才声明的 SUB）", must=["声明"],
     spec=base(derived={"TOT": "SUB + 1", "SUB": "A + B"},
               checks=[{"name": "x", "target": "G_x", "expr": "TOT", "tolerance": 0.01}]))
case("D05", "derived 与 field 重名", spec=base(derived={"A": "A + 1"}))
case("D06", "derived 引用不存在的变量", spec=base(derived={"S": "A + 不存在"}))
case("D07", "derived 正常链式（基线，必须通过）", expect="ok",
     spec=base(derived={"S1": "A + B", "S2": "S1 - C"},
               checks=[{"name": "应发G", "target": "G_x", "expr": "round(S2,2)",
                        "tolerance": 0.01}]))

# ===========================================================================
# 八、checks 引用不存在的 derived
# ===========================================================================
case("K01", "checks.expr 引用不存在的 derived", must=["B_ALL"],
     spec=base(checks=[{"name": "x", "target": "G_x", "expr": "A + B_ALL - C",
                        "tolerance": 0.01}]))
case("K02", "checks.target 未在 fields 中定义",
     spec=base(checks=[{"name": "x", "target": "没这个", "expr": "A", "tolerance": 0.01}]))
case("K03", "checks.target 指向 keys（文本列）",
     spec=base(checks=[{"name": "x", "target": "ID", "expr": "A", "tolerance": 0.01}]))
case("K04", "checks 同名", spec=base(checks=[
    {"name": "同名", "target": "G_x", "expr": "A", "tolerance": 0.01},
    {"name": "同名", "target": "G_x", "expr": "B", "tolerance": 0.01}]))
case("K05", "check 名与变量名撞车", spec=base(checks=[
    {"name": "A", "target": "G_x", "expr": "A", "tolerance": 0.01}]))
case("K06", "check 名 + 字段名拼出同名 CSV 列（X·AI）",
     spec=base(fields={"A": "基本工资A", "B": "绩效B", "C": "扣款C", "G_x": "应发工资G",
                       "X·AI": "应发工资G"},
               checks=[{"name": "X", "target": "G_x", "expr": "round(A+B-C,2)",
                        "tolerance": 0.01}]))
case("K07", "checks.expr 引用 check 自己的名字",
     spec=base(checks=[{"name": "应发G", "target": "G_x", "expr": "应发G + 1",
                        "tolerance": 0.01}]))

# ===========================================================================
# 九、cross_checks
# ===========================================================================
def xc(**over):
    c = {"name": "绩效系数传递", "workbook": B03, "sheet": "绩效表", "header_rows": 1,
         "key": "工号", "left_key": "ID",
         "compare": [{"left": "A", "right": "绩效系数", "tolerance": 0.001}]}
    for k, v in over.items():
        if v is _DEL:
            c.pop(k, None)
        else:
            c[k] = v
    return [c]


case("X01", "cross_checks 的工作簿不存在",
     spec=base(cross_checks=xc(workbook=os.path.join(FX, "根本没有这个表.xlsx"))))
case("X02", "cross_checks 的 Sheet 不存在", spec=base(cross_checks=xc(sheet="没这个Sheet")))
case("X03", "cross_checks 的 sheet 写成 null", spec=base(cross_checks=xc(sheet=None)))
case("X04", "cross_checks 的 sheet 写成数字 0", spec=base(cross_checks=xc(sheet=0)))
case("X05", "cross_checks 的 sheet 写成数组", spec=base(cross_checks=xc(sheet=["绩效表"])))
case("X06", "cross_checks 的 left_key 写成数组", spec=base(cross_checks=xc(left_key=["ID"])))
case("X07", "cross_checks.compare[0].left 写成数组",
     spec=base(cross_checks=xc(compare=[{"left": ["A"], "right": "绩效系数"}])))
case("X08", "cross_checks 缺 compare", spec=base(cross_checks=xc(compare=_DEL)))
case("X09", "cross_checks.compare 写成对象",
     spec=base(cross_checks=xc(compare={"left": "A", "right": "绩效系数"})))
case("X10", "cross_checks 的 left_key 在主表未定义", spec=base(cross_checks=xc(left_key="没有")))
case("X11", "cross_checks 的 key 列在右表不存在", spec=base(cross_checks=xc(key="没这列")))
case("X12", "cross_checks.header_rows 超过右表行数", spec=base(cross_checks=xc(header_rows=99)))
case("X13", "cross_checks.header_rows 写成负数", spec=base(cross_checks=xc(header_rows=-1)))
case("X14", "cross_checks.compare[0].right 列号越界",
     spec=base(cross_checks=xc(compare=[{"left": "A", "right": 99}])))
case("X15", "cross_checks 正常（基线，必须跑通）", expect="ok", must=["跨表一致性"],
     spec=base(cross_checks=xc()))
case("X16", "cross_checks.workbook 写成数字", spec=base(cross_checks=xc(workbook=1)))
case("X17", "cross_checks 少了 name（应当自动兜底）", expect="ok",
     spec=base(cross_checks=xc(name=_DEL)))

# ===========================================================================
# 十、analyze：analysis 段缺失 / 出错
# ===========================================================================
case("A01", "analysis 段完全缺失时 analyze 应优雅退出", cmd="analyze", expect="ok",
     must=["未提供"], spec=base())
case("A02", "analysis 是空对象", cmd="analyze", expect="ok", must=["未提供"],
     spec=base(analysis={}))
case("A03", "analysis 写成数组", cmd="analyze", spec=base(analysis=[]))
case("A04", "analysis 写成字符串", cmd="analyze", spec=base(analysis="分组"))
case("A05", "group_by.dim 写成数组", cmd="analyze",
     spec=base(analysis={"group_by": [{"dim": ["DEPT"], "metrics": ["A"]}]}))
case("A06", "group_by.dim 不存在", cmd="analyze",
     spec=base(analysis={"group_by": [{"dim": "没这个维度", "metrics": ["A"]}]}))
case("A07", "group_by.metrics 指向文本列", cmd="analyze",
     spec=base(analysis={"group_by": [{"dim": "DEPT", "metrics": ["NAME"]}]}))
case("A08", "group_by 写成对象", cmd="analyze",
     spec=base(analysis={"group_by": {"dim": "DEPT"}}))
case("A09", "group_by[0] 写成字符串", cmd="analyze",
     spec=base(analysis={"group_by": ["DEPT"]}))
case("A10", "top_n.field 不存在", cmd="analyze",
     spec=base(analysis={"top_n": [{"field": "没这个"}]}))
case("A11", "top_n.field 写成数组", cmd="analyze",
     spec=base(analysis={"top_n": [{"field": ["A"]}]}))
case("A12", "top_n.n = 0", cmd="analyze", spec=base(analysis={"top_n": [{"field": "A", "n": 0}]}))
case("A13", "outliers.method 非法", cmd="analyze",
     spec=base(analysis={"outliers": [{"field": "A", "method": "森林"}]}))
case("A14", "outliers.field 写成数组", cmd="analyze",
     spec=base(analysis={"outliers": [{"field": ["A"]}]}))
case("A15", "rules.when 写成数组", cmd="analyze",
     spec=base(analysis={"rules": [{"name": "r", "when": ["A > 0"]}]}))
case("A16", "rules 缺 when", cmd="analyze", spec=base(analysis={"rules": [{"name": "r"}]}))
case("A17", "distributions.dim 写成数组", cmd="analyze",
     spec=base(analysis={"distributions": [{"dim": ["DEPT"]}]}))
case("A18", "distributions.bins 乱序", cmd="analyze",
     spec=base(analysis={"distributions": [{"field": "A", "bins": [3, 1, 2]}]}))
case("A19", "distributions.bins 混入文本", cmd="analyze",
     spec=base(analysis={"distributions": [{"field": "A", "bins": [1, "二", 3]}]}))
case("A20", "what_if.recompute 不是 derived", cmd="analyze",
     spec=base(analysis={"what_if": [{"name": "w", "set": {"A": "A*1.1"},
                                      "recompute": ["没这个"],
                                      "targets": [{"name": "t", "expr": "A"}]}]}))
case("A21", "what_if.set 扰动文本列", cmd="analyze",
     spec=base(analysis={"what_if": [{"name": "w", "set": {"NAME": "NAME"},
                                      "targets": [{"name": "t", "expr": "A"}]}]}))
case("A22", "what_if 缺 targets", cmd="analyze",
     spec=base(analysis={"what_if": [{"name": "w", "set": {"A": "A*1.1"}}]}))
case("A23", "what_if.targets 同名", cmd="analyze",
     spec=base(analysis={"what_if": [{"name": "w", "set": {"A": "A*1.1"}, "targets": [
         {"name": "t", "expr": "A"}, {"name": "t", "expr": "B"}]}]}))
case("A24", "analysis 全套正常（基线）", cmd="analyze", expect="ok",
     must=["分组汇总", "离群", "What-If"],
     spec=base(derived={"S1": "A + B"},
               checks=[{"name": "应发G", "target": "G_x", "expr": "round(S1-C,2)",
                        "tolerance": 0.01}],
               analysis={"group_by": [{"dim": "DEPT", "metrics": ["G_x"], "count_as": "人数"}],
                         "distributions": [{"dim": "DEPT"}],
                         "top_n": [{"field": "G_x", "n": 3, "label": "NAME"}],
                         "outliers": [{"field": "G_x", "method": "iqr", "k": 1.5}],
                         "rules": [{"name": "高薪", "when": "G_x > 12000", "label": "NAME"}],
                         "what_if": [{"name": "涨10%", "set": {"A": "A*1.1"},
                                      "recompute": ["S1"],
                                      "targets": [{"name": "应发", "expr": "round(S1-C,2)"}]}]}))
case("A25", "改了 check 名却没重跑 verify（明细 CSV 对不上）", cmd="analyze",
     detail_from="A24",
     spec=base(derived={"S1": "A + B"},
               checks=[{"name": "改了名字的校验项", "target": "G_x",
                        "expr": "round(S1-C,2)", "tolerance": 0.01}],
               analysis={"top_n": [{"field": "改了名字的校验项", "n": 3}]}))
case("A26", "output：改了 check 名却没重跑 verify", cmd="output", detail_from="A24",
     spec=base(derived={"S1": "A + B"},
               checks=[{"name": "改了名字的校验项", "target": "G_x",
                        "expr": "round(S1-C,2)", "tolerance": 0.01}]))

# ===========================================================================
# 十之二、命名空间（第二轮攻击：变量名/校验项名怎么起才不会静默算错）
# ===========================================================================
def _chain(n, reverse=False):
    """n 个链式 derived：S0=A+B，S1=S0+1 …… reverse=True 时倒着声明。"""
    rng = range(n - 1, 0, -1) if reverse else range(1, n)
    dv = OrderedDict()
    if not reverse:
        dv["S0"] = "A + B"
    for i in rng:
        dv["S%d" % i] = "S%d + 1" % (i - 1)
    if reverse:
        dv["S0"] = "A + B"
    return dv


case("N01", "变量名带减号（expr 里会被当成减法静默算错）",
     spec=base(fields={"A-B": "基本工资A", "B": "绩效B", "C": "扣款C", "G_x": "应发工资G"},
               checks=[{"name": "x", "target": "G_x", "expr": "B", "tolerance": 1e9}]))
case("N02", "变量名带空格（永远引用不到，却白占一列明细）",
     spec=base(fields={"A B": "基本工资A", "B": "绩效B", "C": "扣款C", "G_x": "应发工资G"},
               checks=[{"name": "x", "target": "G_x", "expr": "B", "tolerance": 1e9}]))
case("N03", "变量名以 __raw 结尾（和自动生成的原始文本变量撞车）",
     spec=base(fields={"A": "基本工资A", "A__raw": "绩效B", "C": "扣款C", "G_x": "应发工资G"},
               checks=[{"name": "x", "target": "G_x", "expr": "A__raw", "tolerance": 1e9}]))
case("N04", "变量名与白名单函数 sum 同名",
     spec=base(fields={"sum": "基本工资A", "B": "绩效B", "C": "扣款C", "G_x": "应发工资G"},
               checks=[{"name": "x", "target": "G_x", "expr": "sum + B - C", "tolerance": 1e9}]))
case("N05", "变量名是 Python 关键字 if",
     spec=base(fields={"if": "基本工资A", "B": "绩效B", "C": "扣款C", "G_x": "应发工资G"},
               checks=[{"name": "x", "target": "G_x", "expr": "B", "tolerance": 1e9}]))
case("N06", "变量名以数字开头",
     spec=base(fields={"1A": "基本工资A", "B": "绩效B", "C": "扣款C", "G_x": "应发工资G"},
               checks=[{"name": "x", "target": "G_x", "expr": "B", "tolerance": 1e9}]))
case("N07", "中文变量名（合法标识符，必须放行）", expect="ok",
     spec=base(fields={"基本工资": "基本工资A", "绩效": "绩效B", "扣款": "扣款C",
                       "应发_x": "应发工资G"},
               checks=[{"name": "应发", "target": "应发_x",
                        "expr": "round(基本工资 + 绩效 - 扣款, 2)", "tolerance": 0.01}]))
case("N08", "校验项名以 __raw 结尾",
     spec=base(checks=[{"name": "G__raw", "target": "G_x", "expr": "A+B-C", "tolerance": 0.01}]))
case("N09", "校验项名不是标识符，却被 group_by.metrics 引用（analyze 会 KeyError）",
     cmd="analyze", expect="ok", must=["应发工资G=A+B-C"],
     spec=base(checks=[{"name": "应发工资G=A+B-C", "target": "G_x",
                        "expr": "round(A+B-C,2)", "tolerance": 0.01}],
               analysis={"group_by": [{"dim": "DEPT", "metrics": ["应发工资G=A+B-C"]}]}))
case("N10", "同上，被 top_n.field 引用", cmd="analyze", expect="ok",
     spec=base(checks=[{"name": "应发工资G=A+B-C", "target": "G_x",
                        "expr": "round(A+B-C,2)", "tolerance": 0.01}],
               analysis={"top_n": [{"field": "应发工资G=A+B-C", "n": 3}]}))
case("N11", "同上，被 outliers.field 引用", cmd="analyze", expect="ok",
     spec=base(checks=[{"name": "应发工资G=A+B-C", "target": "G_x",
                        "expr": "round(A+B-C,2)", "tolerance": 0.01}],
               analysis={"outliers": [{"field": "应发工资G=A+B-C", "method": "iqr"}]}))
case("N12", "3000 个链式 derived（正序，必须跑通且不爆栈）", expect="ok",
     spec=base(derived=_chain(3000),
               checks=[{"name": "x", "target": "G_x", "expr": "S2999", "tolerance": 1e9}]))
case("N13", "3000 个链式 derived（倒序声明 → 应报「声明顺序」而不是 RecursionError）",
     must=["声明"],
     spec=base(derived=_chain(3000, reverse=True),
               checks=[{"name": "x", "target": "G_x", "expr": "S1", "tolerance": 1e9}]))
case("N14", "3000 个 derived 首尾相接成环（必须报循环依赖，不许爆栈）", must=["循环依赖"],
     spec=base(derived=_chain(3000, reverse=True, ) if False else
               OrderedDict([("S0", "S2999 + 1")] +
                           [("S%d" % i, "S%d + 1" % (i - 1)) for i in range(1, 3000)]),
               checks=[{"name": "x", "target": "G_x", "expr": "S1", "tolerance": 1e9}]))

# ===========================================================================
# 十之三、What-If 的依赖链（第三轮：数字全是 0 的"假推演"）
# ===========================================================================
def wf_base(**over):
    """带两级中间量的基线：S1 = A+B，S2 = S1-C。"""
    s = base(derived={"S1": "A + B", "S2": "S1 - C"},
             checks=[{"name": "应发G", "target": "G_x", "expr": "round(S2,2)",
                      "tolerance": 0.01}])
    s.update(over)
    return s


case("W01", "set 扰动 S1 又把 S1 写进 recompute（扰动被算回去，变化全 0）",
     cmd="analyze", must=["既出现在"],
     spec=wf_base(analysis={"what_if": [{"name": "S1涨10%", "set": {"S1": "S1*1.1"},
                                         "recompute": ["S1", "S2"],
                                         "targets": [{"name": "应发", "expr": "round(S2,2)"}]}]}))
case("W02", "扰动 A 只重算 S1，target 却用下游的 S2（拿陈旧值，变化全 0）",
     cmd="analyze", must=["陈旧值"],
     spec=wf_base(analysis={"what_if": [{"name": "A涨10%", "set": {"A": "A*1.1"},
                                         "recompute": ["S1"],
                                         "targets": [{"name": "应发", "expr": "round(S2,2)"}]}]}))
case("W03", "整条链都重算（基线，合计变化必须真的是 7,450）", cmd="analyze", expect="ok",
     must=["7,450.00"],
     spec=wf_base(analysis={"what_if": [{"name": "A涨10%", "set": {"A": "A*1.1"},
                                         "recompute": ["S1", "S2"],
                                         "targets": [{"name": "应发", "expr": "round(S2,2)"}]}]}))
case("W04", "target 只用输入层，不需要 recompute（基线）", cmd="analyze", expect="ok",
     must=["7,450.00"],
     spec=wf_base(analysis={"what_if": [{"name": "A涨10%", "set": {"A": "A*1.1"},
                                         "targets": [{"name": "应发",
                                                      "expr": "round(A+B-C,2)"}]}]}))

# ===========================================================================
# 十一、性能
# ===========================================================================
case("P01", "1 万行 × 3 校验项 × 3 中间量 的 verify 必须在 60 秒内跑完",
     expect="ok", timeout=180,
     spec={"workbook": B04, "sheet": "大表", "header_rows": 1,
           "keys": {"ID": "工号", "NAME": "姓名"}, "dimensions": {"DEPT": "一级部门"},
           "fields": {"A1": "A1", "A2": "A2", "A3": "A3", "B1": "B1", "B2": "B2",
                      "C1": "C1", "C2": "C2", "D": "D", "G_x": "应发G"},
           "derived": {"A_ALL": "round(A1+A2+A3,2)", "B_ALL": "round(B1+B2,2)",
                       "C_ALL": "round(C1+C2,2)"},
           "checks": [
               {"name": "应发_输入层", "target": "G_x",
                "expr": "round(A1+A2+A3+B1+B2-C1-C2+D,2)", "tolerance": 0.01},
               {"name": "应发_分层", "target": "G_x",
                "expr": "round(A_ALL+B_ALL-C_ALL+D,2)", "tolerance": 0.01},
               {"name": "应发_三元", "target": "G_x",
                "expr": "round(A_ALL+B_ALL-C_ALL+D,2) if A1 > 0 else 0", "tolerance": 0.01}]})


def _perf_spec(n_check):
    sp = {"workbook": B04, "sheet": "大表", "header_rows": 1,
          "keys": {"ID": "工号", "NAME": "姓名"}, "dimensions": {"DEPT": "一级部门"},
          "fields": {"A1": "A1", "A2": "A2", "A3": "A3", "B1": "B1", "B2": "B2",
                     "C1": "C1", "C2": "C2", "D": "D", "G_x": "应发G"},
          "derived": OrderedDict([("A_ALL", "round(A1+A2+A3,2)"), ("B_ALL", "round(B1+B2,2)"),
                                  ("C_ALL", "round(C1+C2,2)"), ("NET", "A_ALL+B_ALL-C_ALL+D")]),
          "checks": []}
    for i in range(n_check):
        sp["checks"].append({"name": "应发_%02d" % i, "target": "G_x",
                             "expr": "round(A_ALL+B_ALL-C_ALL+D,2) if A1 > %d else round(NET,2)" % i,
                             "tolerance": 0.01})
    return sp


case("P02", "1 万行 × 12 校验项 × 4 中间量（更重的一轮，同样卡 60 秒）",
     expect="ok", timeout=300, spec=_perf_spec(12))
case("P03", "1 万行 + 跨表校验（右表 4 行，左表全量扫两遍）", expect="ok", timeout=300,
     spec=dict(_perf_spec(3), cross_checks=[
         {"name": "跨表", "workbook": B03, "sheet": "绩效表", "header_rows": 1,
          "key": "工号", "left_key": "ID",
          "compare": [{"left": "A1", "right": "绩效系数", "tolerance": 1e9}]}]))

# ---------------------------------------------------------------------------
# 执行
# ---------------------------------------------------------------------------
def run(cmd_args, timeout):
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, SCRIPT] + cmd_args, capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr, time.time() - t0
    except subprocess.TimeoutExpired as e:
        return -99, e.stdout or "", (e.stderr or "") + "\n[超时]", time.time() - t0


def read_all(d):
    txt = []
    for root, _dirs, files in os.walk(d):
        for f in files:
            if f.endswith((".md", ".csv")):
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8-sig") as fh:
                        txt.append(fh.read())
                except OSError:
                    pass
    return "\n".join(txt)


def main():
    kw = sys.argv[1] if len(sys.argv) > 1 else ""
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    results = []
    detail_cache = {}
    for c in CASES:
        if kw and kw not in c["id"] and kw not in c["desc"]:
            continue
        cdir = os.path.join(OUT, c["id"])
        os.makedirs(cdir, exist_ok=True)
        sp = os.path.join(cdir, "spec.json")
        with open(sp, "w", encoding="utf-8") as f:
            json.dump(c["spec"], f, ensure_ascii=False, indent=2)

        if c["cmd"] == "verify":
            args = ["verify", sp, "-o", cdir]
        else:
            src = detail_cache.get(c["detail_from"])
            if src is None:
                # 先用自己的 spec 跑一遍 verify 生成明细
                rc0, _o0, _e0, _t0 = run(["verify", sp, "-o", cdir], c["timeout"])
                src = os.path.join(cdir, "verification_detail.csv")
                if rc0 != 0 or not os.path.isfile(src):
                    results.append((c, -1, "", "[前置 verify 失败，无法产出明细]\n" + _e0, 0.0, ""))
                    continue
                detail_cache[c["id"]] = src   # 供后续用例复用（模拟"改了 spec 却没重跑 verify"）
            args = [c["cmd"], sp, "-d", src, "-o", cdir]

        rc, out, err, dt = run(args, c["timeout"])
        if c["cmd"] == "verify" and rc == 0:
            dpath = os.path.join(cdir, "verification_detail.csv")
            if os.path.isfile(dpath):
                detail_cache[c["id"]] = dpath
        results.append((c, rc, out, err, dt, read_all(cdir)))

    # ---- 判定 ----
    bad = []
    print("\n%-5s %-4s %-7s %s" % ("ID", "rc", "耗时", "结论"))
    print("-" * 100)
    for (c, rc, out, err, dt, prod) in results:
        blob = out + "\n" + err
        problems = []
        if "Traceback (most recent call last)" in err:
            problems.append("未捕获 traceback")
        if rc == -99:
            problems.append("超时（>%ds）" % c["timeout"])
        if rc not in (0, 1, -99) and rc != -1:
            problems.append("异常退出码 %d" % rc)
        if c["expect"] == "error":
            if rc == 0:
                problems.append("期望报错却静默通过（rc=0）")
            elif rc == 1 and "[错误]" not in err:
                problems.append("非零退出但没有中文 [错误] 提示")
        elif c["expect"] in ("ok", "warn"):
            if rc != 0:
                problems.append("期望正常跑通却失败（rc=%d）" % rc)
        for m in c["must"]:
            if m not in blob and m not in prod:
                problems.append("缺关键信息：%s" % m)
        for fb in c["forbid"]:
            if fb in blob or fb in prod:
                problems.append("出现了不该有的内容：%s" % fb)
        if c["id"].startswith("P") and rc == 0 and dt > 60:
            problems.append("性能不可接受：%.1fs > 60s" % dt)
        status = "✅ 挡住" if not problems else "❌ " + "；".join(problems)
        print("%-5s %-4s %6.1fs  %s  — %s" % (c["id"], rc, dt, status, c["desc"]))
        if problems:
            bad.append((c, rc, out, err, problems))

    print("\n共 %d 个用例，%d 个被攻破。" % (len(results), len(bad)))
    if bad:
        print("\n" + "=" * 100)
        for (c, rc, out, err, problems) in bad:
            print("\n### %s %s\n    问题：%s\n    rc=%s\n    stderr:\n%s"
                  % (c["id"], c["desc"], "；".join(problems), rc,
                     re.sub(r"^", "        ", (err or "(空)")[-2500:], flags=re.M)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
