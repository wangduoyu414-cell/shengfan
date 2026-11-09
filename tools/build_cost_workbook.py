#!/usr/bin/env python3
"""生成成本测算表模板 X01（templates/X01-cost-calculator.xlsx）。

用法：python3 tools/build_cost_workbook.py [输出路径]
依赖：openpyxl（只在生成模板时需要；日常使用模板不需要本脚本）。
规则依据：skill-source/shared/D09-pricing-and-cost.md
"""
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "templates" / "X01-cost-calculator.xlsx"

INPUT = PatternFill("solid", fgColor="FFF7D6")   # 需要填写
FORMULA = PatternFill("solid", fgColor="EEEEEE")  # 公式，勿改
HEAD = Font(bold=True)
ROWS = 100  # 成本明细预置行数
FIRST = 4   # 成本明细第一行数据所在行

MODULES = [
    ("M01", "需求诊断与方案策划"), ("M02", "培训课程与讲师"), ("M03", "会议场地与住宿"),
    ("M04", "餐饮与茶歇"), ("M05", "交通与票务"), ("M06", "活动创意与流程"),
    ("M07", "设计、印刷与物料"), ("M08", "舞台、灯光、音响、LED 与直播"), ("M09", "摄影摄像与视频制作"),
    ("M10", "教务、班务与学习运营"), ("M11", "客户接待与现场服务"), ("M12", "安全、保险、应急与保密"),
    ("M13", "供应商协调与第三方管理"), ("M14", "结算、发票、验收与项目报告"),
    ("M15", "目的地服务（地接、导游讲解、景区门票、体验项目）"), ("M16", "签证与出入境（预留）"),
]
STATUSES = "参考价,正式报价,已核可用,已锁定,已结算,已失效,待查估算"


def build():
    wb = Workbook()

    # 说明
    ws = wb.active
    ws.title = "说明"
    lines = [
        "成本测算表模板 X01 · v1.0（依据 D09 报价与成本口径）",
        "",
        "使用方法",
        "1. 每个项目复制一份，命名：{项目编号}_成本测算_V{n}_{YYYYMMDD}.xlsx，放在项目 03_资源与报价/。",
        "2. 只填黄色格子；灰色格子是公式，不要改。",
        "3. 参数页：填项目编号、版本、计划人数、报价口径、毛利底线、风险预备比例、各档拟报价。",
        "4. 成本明细页：每行一项费用，按服务模块填写；单价必须引用报价编号（报价记录 A04）。",
        "   计量方式：按人数＝数量随人数变化（填每人系数，如每人 0.5 间）；固定数量＝填数量。",
        "   次数：天数、晚数或场次。向上取整：房间、车辆等需要整数时填“是”。",
        "   价格状态：参考价只能估算；未知费用写“待查估算”并填估算单价，不填零。",
        "5. 汇总页：查看三档成本、最低安全报价、毛利率和提醒。",
        "6. 没有 Excel 时，用 tools/cost_recalc.py 复算并输出摘要（结果与本表公式一致）。",
        "",
        "注意",
        "- 用脚本生成或修改后，需要用 Excel 或 WPS 打开并保存一次，文件里才有计算结果。",
        "- 对外报价引用本表版本号；不在其他文件里另算金额（D09 §1）。",
        "- 毛利底线、风险预备比例、税费口径由财务确定（DQ18）；未定时汇总页会提示。",
    ]
    for i, text in enumerate(lines, start=1):
        ws.cell(row=i, column=1, value=text)
    ws["A1"].font = Font(bold=True, size=13)
    ws.column_dimensions["A"].width = 110

    # 参数
    p = wb.create_sheet("参数")
    p["A1"] = "参数（黄色格子填写）"
    p["A1"].font = HEAD
    params = [
        (2, "项目编号", None, True),
        (3, "测算版本", "V1", True),
        (4, "测算日期", None, True),
        (5, "计划人数", None, True),
        (6, "低档系数", 0.8, True),
        (7, "高档系数", 1.2, True),
        (8, "低档人数", "=IF(B5=\"\",\"\",ROUNDUP(B5*B6,0))", False),
        (9, "中档人数", "=IF(B5=\"\",\"\",B5)", False),
        (10, "高档人数", "=IF(B5=\"\",\"\",ROUNDUP(B5*B7,0))", False),
        (11, "对外报价口径（含税/不含税）", None, True),
        (12, "毛利底线（如 0.15）", None, True),
        (13, "风险预备比例（如 0.03）", None, True),
        (14, "拟报价-低档", None, True),
        (15, "拟报价-中档", None, True),
        (16, "拟报价-高档", None, True),
    ]
    for row, label, value, is_input in params:
        p.cell(row=row, column=1, value=label)
        c = p.cell(row=row, column=2, value=value)
        c.fill = INPUT if is_input else FORMULA
    p.column_dimensions["A"].width = 30
    p.column_dimensions["B"].width = 18
    dv_tax = DataValidation(type="list", formula1='"含税,不含税"', allow_blank=True)
    p.add_data_validation(dv_tax)
    dv_tax.add("B11")

    # 成本明细
    d = wb.create_sheet("成本明细")
    d["A1"] = "成本明细（每行一项费用；单价引用报价编号；数量与小计为公式）"
    d["A1"].font = HEAD
    heads = ["模块编号", "费用项", "报价编号", "价格状态", "单价", "计量方式", "系数或数量",
             "次数（天/晚/场）", "向上取整", "数量-低", "数量-中", "数量-高",
             "小计-低", "小计-中", "小计-高", "含税", "备注"]
    for col, h in enumerate(heads, start=1):
        c = d.cell(row=3, column=col, value=h)
        c.font = HEAD
        c.alignment = Alignment(wrap_text=True)
    widths = [9, 28, 14, 11, 10, 10, 11, 10, 9, 9, 9, 9, 12, 12, 12, 8, 24]
    for col, w in enumerate(widths, start=1):
        d.column_dimensions[d.cell(row=3, column=col).column_letter].width = w

    people = {"J": "参数!$B$8", "K": "参数!$B$9", "L": "参数!$B$10"}
    for r in range(FIRST, FIRST + ROWS):
        for col in "ABCDEFGHIPQ":
            d[f"{col}{r}"].fill = INPUT
        for qcol, ref in people.items():
            d[f"{qcol}{r}"] = (
                f'=IF(OR(G{r}="",H{r}=""),"",IF(F{r}="按人数",'
                f'IF(I{r}="是",ROUNDUP({ref}*G{r},0),{ref}*G{r}),G{r})*H{r})'
            )
            d[f"{qcol}{r}"].fill = FORMULA
        for scol, qcol in (("M", "J"), ("N", "K"), ("O", "L")):
            d[f"{scol}{r}"] = f'=IF(OR(E{r}="",{qcol}{r}=""),"",E{r}*{qcol}{r})'
            d[f"{scol}{r}"].fill = FORMULA
    last = FIRST + ROWS - 1
    for formula, cells in (
        (f'"{STATUSES}"', f"D{FIRST}:D{last}"),
        ('"按人数,固定数量"', f"F{FIRST}:F{last}"),
        ('"是,否"', f"I{FIRST}:I{last}"),
        ('"是,否,未知"', f"P{FIRST}:P{last}"),
    ):
        dv = DataValidation(type="list", formula1=formula, allow_blank=True)
        d.add_data_validation(dv)
        dv.add(cells)
    d.freeze_panes = "C4"

    # 汇总
    s = wb.create_sheet("汇总")
    s["A1"] = "汇总（全部为公式）"
    s["A1"].font = HEAD
    for col, h in enumerate(["项目", "低档", "中档", "高档"], start=1):
        s.cell(row=2, column=col, value=h).font = HEAD
    rng = lambda c: f"成本明细!{c}{FIRST}:{c}{last}"
    rows = [
        ("人数", "=参数!B8", "=参数!B9", "=参数!B10"),
        ("成本合计", f"=SUM({rng('M')})", f"=SUM({rng('N')})", f"=SUM({rng('O')})"),
        ("其中：参考价金额", f'=SUMIF({rng("D")},"参考价",{rng("M")})',
         f'=SUMIF({rng("D")},"参考价",{rng("N")})', f'=SUMIF({rng("D")},"参考价",{rng("O")})'),
        ("其中：待查估算金额", f'=SUMIF({rng("D")},"待查估算",{rng("M")})',
         f'=SUMIF({rng("D")},"待查估算",{rng("N")})', f'=SUMIF({rng("D")},"待查估算",{rng("O")})'),
        ("风险预备", '=IF(参数!$B$13="",0,B4*参数!$B$13)', '=IF(参数!$B$13="",0,C4*参数!$B$13)',
         '=IF(参数!$B$13="",0,D4*参数!$B$13)'),
        ("最低安全报价", '=IF(参数!$B$12="","毛利底线待定",(B4+B7)/(1-参数!$B$12))',
         '=IF(参数!$B$12="","毛利底线待定",(C4+C7)/(1-参数!$B$12))',
         '=IF(参数!$B$12="","毛利底线待定",(D4+D7)/(1-参数!$B$12))'),
        ("拟报价", "=参数!B14", "=参数!B15", "=参数!B16"),
        ("毛利", '=IF(B9="","",B9-B4)', '=IF(C9="","",C9-C4)', '=IF(D9="","",D9-D4)'),
        ("毛利率", '=IF(OR(B9="",B9=0),"",B10/B9)', '=IF(OR(C9="",C9=0),"",C10/C9)',
         '=IF(OR(D9="",D9=0),"",D10/D9)'),
        ("人均报价", '=IF(OR(B9="",B3="",B3=0),"",B9/B3)', '=IF(OR(C9="",C3="",C3=0),"",C9/C3)',
         '=IF(OR(D9="",D3="",D3=0),"",D9/D3)'),
        ("提醒：低于最低安全报价",
         '=IF(OR(B9="",ISTEXT(B8)),"",IF(B9<B8,"低于最低安全报价，需负责人批准",""))',
         '=IF(OR(C9="",ISTEXT(C8)),"",IF(C9<C8,"低于最低安全报价，需负责人批准",""))',
         '=IF(OR(D9="",ISTEXT(D8)),"",IF(D9<D8,"低于最低安全报价，需负责人批准",""))'),
        ("提醒：含参考价", '=IF(B5>0,"含参考价，对外报价前换成正式报价","")',
         '=IF(C5>0,"含参考价，对外报价前换成正式报价","")', '=IF(D5>0,"含参考价，对外报价前换成正式报价","")'),
        ("提醒：已失效报价行数", f'=COUNTIF({rng("D")},"已失效")', "", ""),
        ("提醒：未填报价编号的行数", f'=COUNTIFS({rng("E")},"<>",{rng("C")},"")', "", ""),
    ]
    for i, (label, *vals) in enumerate(rows, start=3):
        s.cell(row=i, column=1, value=label)
        for j, v in enumerate(vals, start=2):
            c = s.cell(row=i, column=j, value=v if v != "" else None)
            c.fill = FORMULA
    s.column_dimensions["A"].width = 26
    for col in "BCD":
        s.column_dimensions[col].width = 30

    # 模块
    m = wb.create_sheet("模块")
    m["A1"], m["B1"] = "编号", "服务模块（D05 §7）"
    m["A1"].font = m["B1"].font = HEAD
    for i, (code, name) in enumerate(MODULES, start=2):
        m.cell(row=i, column=1, value=code)
        m.cell(row=i, column=2, value=name)
    m.column_dimensions["B"].width = 50

    # 公式里的中文工作表名统一加引号，兼容 Excel 与 WPS
    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                v = cell.value
                if isinstance(v, str) and v.startswith("="):
                    cell.value = v.replace("参数!", "'参数'!").replace("成本明细!", "'成本明细'!")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(f"已生成 {OUT}")


if __name__ == "__main__":
    build()
