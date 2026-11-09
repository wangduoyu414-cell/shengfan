#!/usr/bin/env python3
"""业务库初始化与新建项目（X04）。

用法：
  python3 init_project.py init-library <业务库路径>
      建业务库目录结构和空表格（A01、A03、A04、A05、A08；需要 openpyxl，没有时生成 CSV）
  python3 init_project.py new-project <业务库路径> --client C-001 --client-short 客户简称 --name 项目简称
      [--entry 招投标|框架内订单|直接委托] [--framework 2025-007] [--year 2026] [--owner 姓名]
      建项目工作区、主卡初稿、日志第一条，并在项目总表中追加一行。

规则依据：D01 §6、D05 §5、§9；project-hub P1。主卡中的事实一律为"待确认"，立项须由人确认。
"""
import argparse
import csv
import datetime as dt
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# 在方法库中运行时模板在 ../templates；在 Skill 包中运行时在 ../templates
TEMPLATES = next((p for p in [HERE.parent / "templates", HERE / "templates"] if p.exists()), None)

TABLES = {
    "项目总表": ["项目编号", "子编号类型", "项目名称", "客户编号", "客户部门", "入口类型", "所属框架", "关联项目",
              "主产品族", "其他产品族", "主要客户目标", "城市", "计划人数", "开始日期", "结束日期", "项目阶段",
              "负责人", "主执行平台", "下一节点日期", "下一节点事项", "预算金额（客户口径）", "报价金额",
              "中选金额", "合同金额", "结算金额", "实际成本", "工作区路径", "备注"],
    "共享资产/资源与报价/资源档案": ["资源编号", "类别", "名称", "地区", "规格容量", "服务范围", "联系人", "合作次数",
                         "最近合作项目", "评价", "风险记录", "状态", "备注"],
    "共享资产/资源与报价/报价记录": ["报价编号", "资源编号", "关联项目", "服务模块", "规格描述", "数量", "计价单位", "单价",
                         "币种", "是否含税", "税率或发票类型", "包含", "排除", "起订条件", "取消条款", "有效期至",
                         "价格状态", "来源", "取得日期", "录入人", "备注"],
    "共享资产/能力与证据/证据目录": ["证据编号", "类别", "名称", "适用主体", "证据状态", "有效期至", "可否对外", "关联项目",
                         "原件位置", "摘要", "备注"],
    "共享资产/名册/联系人": ["person_id", "sender_id", "称呼", "单位", "角色", "关联", "决策角色", "存档同意", "备注"],
    "共享资产/名册/群与项目映射": ["conversation_id", "群简称", "群类型", "客户编号", "活跃项目", "默认项目", "是否摄取",
                          "生效起止", "负责人"],
}
DIRS = ["项目", "共享资产/资源与报价/报价原件", "共享资产/能力与证据/原件", "共享资产/客户档案",
        "共享资产/方案素材/优秀方案", "共享资产/方案素材/风格卡与品牌", "共享资产/方案素材/授权图片",
        "共享资产/名册", "收件箱/待归属", "收件箱/手工投递"]
PROJECT_DIRS = ["01_原始资料", "02_沟通记录", "03_资源与报价", "04_策划与设计/视觉", "05_对外成果",
                "06_执行与结算", "07_复盘", "_任务"]

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font
    HAVE_XLSX = True
except ImportError:
    HAVE_XLSX = False


def write_table(base: Path, rel: str, headers):
    if HAVE_XLSX:
        path = base / f"{rel}.xlsx"
        if path.exists():
            return path
        wb = Workbook()
        ws = wb.active
        ws.title = Path(rel).name
        ws.append(headers)
        for c in ws[1]:
            c.font = Font(bold=True)
        ws.freeze_panes = "A2"
        path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(path)
    else:
        path = base / f"{rel}.csv"
        if path.exists():
            return path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow(headers)
    return path


def init_library(base: Path):
    for d in DIRS:
        (base / d).mkdir(parents=True, exist_ok=True)
    for rel, headers in TABLES.items():
        print("表格：", write_table(base, rel, headers).relative_to(base))
    tpl = base / "共享资产" / "客户档案" / "_客户档案模板.md"
    if not tpl.exists():
        tpl.write_text(CLIENT_TEMPLATE, encoding="utf-8")
    snippets = base / "共享资产" / "方案素材" / "策划片段.md"
    if not snippets.exists():
        snippets.write_text("# 策划片段\n\n| 片段 | 适用产品族 | 适用条件 | 来源项目 | 可否对外 |\n|---|---|---|---|---|\n", encoding="utf-8")
    print(f"业务库已初始化：{base}")


def next_project_no(base: Path, year: int) -> str:
    nums = []
    for p in (base / "项目").glob(f"{year}-*"):
        m = re.match(rf"{year}-(\d{{3}})", p.name)
        if m:
            nums.append(int(m.group(1)))
    return f"{year}-{(max(nums) + 1) if nums else 1:03d}"


def append_registry(base: Path, row: dict):
    headers = TABLES["项目总表"]
    xlsx, csvp = base / "项目总表.xlsx", base / "项目总表.csv"
    if HAVE_XLSX and xlsx.exists():
        wb = load_workbook(xlsx)
        wb.active.append([row.get(h, "") for h in headers])
        wb.save(xlsx)
        return xlsx
    if csvp.exists():
        with csvp.open("a", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow([row.get(h, "") for h in headers])
        return csvp
    print("未找到项目总表，请先运行 init-library；需要追加的行：")
    print(" | ".join(f"{h}={row.get(h, '')}" for h in headers if row.get(h)))
    return None


def new_project(a):
    base = Path(a.library)
    if not (base / "项目").exists():
        sys.exit("业务库未初始化：先运行 init-library")
    year = a.year or dt.date.today().year
    no = next_project_no(base, year)
    ws = base / "项目" / f"{no}_{a.client_short}_{a.name}"
    for d in PROJECT_DIRS:
        (ws / d).mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    if TEMPLATES is None:
        sys.exit("找不到模板目录 templates/")
    card = (TEMPLATES / "TP01-project-card.md").read_text(encoding="utf-8")
    card = (card.replace("{项目编号}", no).replace("{项目名称}", a.name)
            .replace("{YYYY-MM-DD}", today).replace("{姓名}", a.owner or "待定")
            .replace("{项目阶段，见 D05 §3.3}", "线索"))
    card = card.replace("| 项目编号 | |", f"| 项目编号 | {no} |", 1)
    card = card.replace("| 项目名称 | |", f"| 项目名称 | {a.name} |", 1)
    card = card.replace("{C-编号} {客户简称}", f"{a.client} {a.client_short}")
    if a.entry:
        card = card.replace("招投标／框架内订单／直接委托", a.entry, 1)
    card = card.replace("{框架项目编号，或\"无\"}", a.framework or "无")
    card = card.replace("| 工作区 | {路径} |", f"| 工作区 | 项目/{ws.name} |")
    (ws / "00_项目主卡.md").write_text(card, encoding="utf-8")
    log = (TEMPLATES / "TP02-project-log.md").read_text(encoding="utf-8")
    log = log.replace("{项目编号}", no).replace("{项目名称}", a.name)
    log = log.replace("| {YYYY-MM-DD HH:MM} | | | | | |",
                      f"| {dt.datetime.now():%Y-%m-%d %H:%M} | 事件 | 立项初稿（待项目经理确认） | init_project.py | 系统 | 新建工作区 |")
    (ws / "00_项目日志.md").write_text(log, encoding="utf-8")
    reg = append_registry(base, {"项目编号": no, "项目名称": a.name, "客户编号": a.client, "入口类型": a.entry or "",
                                 "所属框架": a.framework or "", "项目阶段": "线索", "负责人": a.owner or "",
                                 "工作区路径": f"项目/{ws.name}"})
    print(f"已新建：{ws}")
    if reg:
        print(f"已追加到：{reg.name}（立项须由项目经理确认）")


CLIENT_TEMPLATE = """# {客户编号} {客户简称} · 客户档案

更新：{YYYY-MM-DD}

| 项 | 内容 |
|---|---|
| 名称与简称 | |
| 行业 | |
| 组织与部门 | |
| 采购方式与周期 | |
| 框架资格 | {框架项目编号、有效期、考核要求} |
| 常见需求 | |
| 偏好与评审关注 | |
| 价格敏感度 | |
| 常用城市与场地 | |
| 历史项目 | {项目编号列表} |
| 关键联系人 | {P-编号，详情见名册} |
| 风险与注意 | |

## 更新记录

| 日期 | 内容 | 来源 |
|---|---|---|
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s1 = sub.add_parser("init-library")
    s1.add_argument("library")
    s2 = sub.add_parser("new-project")
    s2.add_argument("library")
    s2.add_argument("--client", required=True)
    s2.add_argument("--client-short", required=True)
    s2.add_argument("--name", required=True)
    s2.add_argument("--entry", choices=["招投标", "框架内订单", "直接委托"])
    s2.add_argument("--framework")
    s2.add_argument("--year", type=int)
    s2.add_argument("--owner")
    a = ap.parse_args()
    if a.cmd == "init-library":
        init_library(Path(a.library))
    else:
        new_project(a)


if __name__ == "__main__":
    main()
