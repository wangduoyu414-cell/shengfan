#!/usr/bin/env python3
"""一致性检查（X02）：核对项目主卡与各成果内容稿的"关键数据"是否一致，并检查版本指针和文件命名。

用法：python3 check_consistency.py <项目工作区路径> [--all]
  默认只检查主卡版本指针中登记的当前有效文件；--all 检查工作区内所有带"关键数据"块的 .md 文件。
只用 Python 标准库。规则依据：D05 §6、D06 §10、change-review M3。
"""
import argparse
import re
import sys
from pathlib import Path

KEYS = ["项目编号", "人数", "开始日期", "结束日期", "天数", "每人间夜", "地点",
        "报价总额", "含税", "成本测算版本", "服务模块"]
CARD_ALIASES = {"成本测算版本": None}  # 主卡中由 §6 来源列给出，单独处理
NAME_RE = re.compile(r"^\d{4}-\d{3}(?:-\d{2})?_[^_]+_(对客|内部)_V\d+_(草稿|已发送|已确认|作废)_\d{8}\.[A-Za-z0-9]+$")


def norm(v: str) -> str:
    v = (v or "").strip().replace("，", ",").replace(" ", "")
    v = re.sub(r"[〔（(].*?[〕）)]", "", v)  # 去掉括注
    num = v.replace(",", "").replace("元", "")
    try:
        f = float(num)
        return f"{f:.2f}"
    except ValueError:
        return v


def parse_table_rows(text: str):
    rows = []
    for line in text.splitlines():
        if line.startswith("|") and not re.match(r"^\|\s*-", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(cells)
    return rows


def card_values(card: Path):
    text = card.read_text(encoding="utf-8")
    vals = {}
    # §1 项目编号
    m = re.search(r"\|\s*项目编号\s*\|\s*([^|]*)\|", text)
    if m and m.group(1).strip():
        vals["项目编号"] = m.group(1).strip()
    # §3 当前有效条件：项 | 值 | 状态 | 来源（作废的不取）
    sec3 = re.search(r"## 3 当前有效条件(.*?)\n## ", text, re.S)
    if sec3:
        for cells in parse_table_rows(sec3.group(1)):
            if len(cells) >= 3 and cells[0] in KEYS and cells[1] and cells[2] != "作废":
                vals[cells[0]] = cells[1]
    # §6 报价摘要
    sec6 = re.search(r"## 6 资源与报价摘要(.*?)\n## ", text, re.S)
    if sec6:
        for cells in parse_table_rows(sec6.group(1)):
            if len(cells) >= 3 and cells[0] == "报价总额" and cells[1]:
                vals["报价总额"] = cells[1]
                m2 = re.search(r"V\d+", cells[2])
                if m2:
                    vals["成本测算版本"] = m2.group(0)
            if len(cells) >= 2 and cells[0] == "含税" and cells[1]:
                vals["含税"] = cells[1]
    # §7 版本指针
    pointers = []
    sec7 = re.search(r"## 7 版本指针(.*?)\n## ", text, re.S)
    if sec7:
        for cells in parse_table_rows(sec7.group(1)):
            if len(cells) >= 2 and cells[0] != "成果" and cells[1]:
                pointers.append(cells[1])
    return vals, pointers


def key_block(path: Path):
    text = path.read_text(encoding="utf-8")
    m = re.search(r"<!-- 关键数据 -->(.*?)<!-- /关键数据 -->", text, re.S)
    if not m:
        return None
    vals = {}
    for cells in parse_table_rows(m.group(1)):
        if len(cells) >= 2 and cells[0] in KEYS and cells[1] and not cells[1].startswith("{"):
            vals[cells[0]] = cells[1]
    return vals


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("workspace")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    ws = Path(a.workspace)
    card = ws / "00_项目主卡.md"
    if not card.exists():
        sys.exit(f"找不到主卡：{card}")
    cvals, pointers = card_values(card)
    issues, checked = [], []

    files = []
    if a.all:
        files = [p for p in ws.rglob("*.md") if p.name != "00_项目主卡.md" and "_旧版" not in p.parts]
    else:
        for ptr in pointers:
            hits = list(ws.rglob(Path(ptr).name))
            md = [h for h in hits if h.suffix == ".md"] or [h.with_suffix(".md") for h in hits if h.with_suffix(".md").exists()]
            if not hits:
                issues.append(f"版本指针中的文件不存在：{ptr}")
            files += md
            for h in hits:
                if not NAME_RE.match(h.name) and "成本测算" not in h.name and "需求" not in h.name:
                    issues.append(f"文件名不符合 D05 §6.1：{h.name}")

    for f in sorted(set(files)):
        kv = key_block(f)
        if kv is None:
            continue
        checked.append(f.name)
        for k, v in kv.items():
            if k in cvals and norm(cvals[k]) != norm(v):
                issues.append(f"{f.name}：{k} 为“{v}”，主卡为“{cvals[k]}”")

    print(f"# 一致性检查：{ws.name}\n")
    print(f"主卡关键数据：{', '.join(f'{k}={v}' for k, v in cvals.items()) or '（主卡 §3、§6 尚未填写）'}")
    print(f"检查的文件：{', '.join(checked) or '（没有带关键数据块的文件）'}\n")
    if issues:
        print("## 问题")
        for i in issues:
            print(f"- {i}")
        sys.exit(1)
    print("## 结论\n通过：已检查文件的关键数据与主卡一致。")


if __name__ == "__main__":
    main()
