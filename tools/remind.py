#!/usr/bin/env python3
"""提醒（X05）：报价有效期、超期的待确认事项、降级结果待审。

用法：python3 remind.py <业务库路径> [--days 7] [--out 提醒.md]
可以由各平台的定时任务调用（例如 WorkBuddy 定时任务），输出 Markdown 提醒。
读取 XLSX 需要 openpyxl；没有时读取同名 CSV。规则依据：D05 §3.2、D09 §5。
"""
import argparse
import csv
import datetime as dt
import re
from pathlib import Path

try:
    from openpyxl import load_workbook
except ImportError:
    load_workbook = None

CLOSED = {"已失效", "已结算", "已锁定"}


def read_rows(base: Path, rel: str):
    xlsx, csvp = base / f"{rel}.xlsx", base / f"{rel}.csv"
    if xlsx.exists() and load_workbook:
        ws = load_workbook(xlsx, read_only=True, data_only=True).active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        head = [str(h) for h in rows[0]]
        return [dict(zip(head, r)) for r in rows[1:] if any(r)]
    if csvp.exists():
        with csvp.open(encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    return []


def to_date(v):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v).strip()[:10])
    except (ValueError, TypeError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("library")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--out")
    a = ap.parse_args()
    base, today = Path(a.library), dt.date.today()
    out = [f"# 提醒 {today.isoformat()}", ""]

    quotes = read_rows(base, "共享资产/资源与报价/报价记录")
    expired, soon = [], []
    for q in quotes:
        d = to_date(q.get("有效期至"))
        status = (q.get("价格状态") or "").strip()
        if not d or status in CLOSED:
            continue
        if d < today:
            expired.append(q)
        elif (d - today).days <= a.days:
            soon.append(q)
    out += ["## 报价", ""]
    if not (expired or soon):
        out.append("- 无")
    for q in expired:
        out.append(f"- 已过期但未标失效：{q.get('报价编号')}（{q.get('关联项目')}，有效期至 {q.get('有效期至')}）→ 改为“已失效”或续期")
    for q in soon:
        out.append(f"- {a.days} 天内到期：{q.get('报价编号')}（{q.get('关联项目')}，有效期至 {q.get('有效期至')}）→ 联系供应商续期")

    out += ["", "## 待确认事项与降级结果", ""]
    found = False
    for card in sorted((base / "项目").glob("*/00_项目主卡.md")):
        text = card.read_text(encoding="utf-8")
        sec = re.search(r"## 5 待确认事项(.*?)\n## ", text, re.S)
        if not sec:
            continue
        for line in sec.group(1).splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 7 or cells[0] in ("编号", "") or set(cells[0]) <= {"-"}:
                continue
            due, status = to_date(cells[4]), cells[6]
            if "降级" in cells[1] and status not in ("已确认", "已关闭"):
                out.append(f"- {card.parent.name}：降级结果待审——{cells[1]}")
                found = True
            elif due and due < today and status not in ("已确认", "已关闭"):
                out.append(f"- {card.parent.name}：待确认已超期——{cells[1]}（截止 {cells[4]}，负责人 {cells[5]}）")
                found = True
    if not found:
        out.append("- 无")
    text = "\n".join(out) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"已写入 {a.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
