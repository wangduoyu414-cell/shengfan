#!/usr/bin/env python3
"""成本测算表复算（X01 的 T3 替代）：不用 Excel，按与模板相同的公式复算并输出 Markdown 摘要。

用法：python3 tools/cost_recalc.py <成本测算表.xlsx> [--out 摘要.md]
依赖：openpyxl。没有 openpyxl 时，请用 Excel 或 WPS 打开测算表查看汇总页。
规则依据：skill-source/shared/D09-pricing-and-cost.md
"""
import argparse
import math
import sys
from pathlib import Path

try:
    from openpyxl import load_workbook
except ImportError:  # pragma: no cover
    sys.exit("缺少 openpyxl：请用 Excel 或 WPS 打开测算表，查看“汇总”页（D06 §11）。")

FIRST, ROWS = 4, 100


def num(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def roundup(x):
    return math.ceil(x - 1e-9)


def recalc(path):
    wb = load_workbook(path, data_only=False)
    p, d = wb["参数"], wb["成本明细"]
    planned = num(p["B5"].value)
    low_f = num(p["B6"].value) or 0.8
    high_f = num(p["B7"].value) or 1.2
    people = {
        "低": roundup(planned * low_f) if planned else None,
        "中": planned,
        "高": roundup(planned * high_f) if planned else None,
    }
    margin_floor = num(p["B12"].value)
    risk = num(p["B13"].value)
    offers = {"低": num(p["B14"].value), "中": num(p["B15"].value), "高": num(p["B16"].value)}

    totals = {k: 0.0 for k in people}
    ref_amt = {k: 0.0 for k in people}
    tbd_amt = {k: 0.0 for k in people}
    expired = no_quote = 0
    lines = []
    for r in range(FIRST, FIRST + ROWS):
        module, item, quote, status = (d[f"{c}{r}"].value for c in "ABCD")
        price, basis, coef, times, ceil_ = (d[f"{c}{r}"].value for c in "EFGHI")
        price, coef, times = num(price), num(coef), num(times)
        if price is None and not item:
            continue
        if status == "已失效":
            expired += 1
        if price is not None and not quote:
            no_quote += 1
        row = {"模块": module, "费用项": item, "报价编号": quote, "状态": status, "小计": {}}
        for k, n in people.items():
            if coef is None or times is None:
                qty = None
            elif basis == "按人数":
                if n is None:
                    qty = None
                else:
                    q = n * coef
                    qty = (roundup(q) if ceil_ == "是" else q) * times
            else:
                qty = coef * times
            sub = price * qty if (price is not None and qty is not None) else None
            row["小计"][k] = sub
            if sub is not None:
                totals[k] += sub
                if status == "参考价":
                    ref_amt[k] += sub
                if status == "待查估算":
                    tbd_amt[k] += sub
        lines.append(row)

    summary = {}
    for k in people:
        reserve = totals[k] * risk if risk else 0.0
        floor_price = (totals[k] + reserve) / (1 - margin_floor) if margin_floor is not None else None
        offer = offers[k]
        margin = offer - totals[k] if offer is not None else None
        rate = margin / offer if (offer and margin is not None) else None
        per_head = offer / people[k] if (offer and people[k]) else None
        flags = []
        if floor_price is None:
            flags.append("毛利底线待定")
        elif offer is not None and offer < floor_price:
            flags.append("低于最低安全报价，需负责人批准")
        if ref_amt[k] > 0:
            flags.append("含参考价，对外报价前换成正式报价")
        summary[k] = dict(people=people[k], cost=totals[k], ref=ref_amt[k], tbd=tbd_amt[k],
                          reserve=reserve, floor=floor_price, offer=offer, margin=margin,
                          rate=rate, per_head=per_head, flags=flags)
    return dict(project=p["B2"].value, version=p["B3"].value, tax=p["B11"].value,
                lines=lines, summary=summary, expired=expired, no_quote=no_quote)


def fmt(v, pct=False):
    if v is None:
        return "—"
    if pct:
        return f"{v * 100:.1f}%"
    return f"{v:,.2f}"


def to_markdown(res, src):
    out = [f"# 成本测算摘要（脚本复算）", "",
           f"来源：{src} ｜ 项目：{res['project'] or '未填'} ｜ 版本：{res['version'] or '未填'} ｜ 报价口径：{res['tax'] or '未填'}",
           "", "> 由 tools/cost_recalc.py 按模板公式复算（T3）。引用时写“成本测算 {版本}（脚本复算）”。", "",
           "| 项目 | 低档 | 中档 | 高档 |", "|---|---|---|---|"]
    keys = ["低", "中", "高"]
    rows = [("人数", "people", False), ("成本合计", "cost", False), ("其中参考价", "ref", False),
            ("其中待查估算", "tbd", False), ("风险预备", "reserve", False), ("最低安全报价", "floor", False),
            ("拟报价", "offer", False), ("毛利", "margin", False), ("毛利率", "rate", True), ("人均报价", "per_head", False)]
    for label, key, pct in rows:
        out.append(f"| {label} | " + " | ".join(fmt(res["summary"][k][key], pct) for k in keys) + " |")
    out += ["", "## 提醒", ""]
    flags = []
    for k in keys:
        for f in res["summary"][k]["flags"]:
            flags.append(f"- {k}档：{f}")
    if res["expired"]:
        flags.append(f"- 有 {res['expired']} 行使用了已失效的报价")
    if res["no_quote"]:
        flags.append(f"- 有 {res['no_quote']} 行填了单价但没有报价编号")
    out += flags or ["- 无"]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("xlsx")
    ap.add_argument("--out")
    a = ap.parse_args()
    md = to_markdown(recalc(a.xlsx), Path(a.xlsx).name)
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
        print(f"已写入 {a.out}")
    else:
        print(md)


if __name__ == "__main__":
    main()
