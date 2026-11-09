#!/usr/bin/env python3
"""摄取摘要转换（X06，D04 的参考实现）：把统一消息记录（JSON Lines）转成项目沟通摘要。

用法：python3 digest_from_jsonl.py <统一消息记录.jsonl> <业务库路径> [--batch IB-YYYYMMDD-HHMM]
- 已归属（mapped、confirmed）的消息写入 项目/{项目}/02_沟通记录/{日期}_{群简称}.md；
- 待归属（pending、suggested）的消息写入 收件箱/待归属/{日期}.md；
- 按 D04 §8 遮蔽个人信息；撤回的消息显示"[已撤回]"；已写入的 record_id 不重复写（幂等）。
只用 Python 标准库。开发方的摄取系统可以直接输出同样格式的摘要，本脚本用于测试和兜底。
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

LEVEL_ORDER = {"L1": 1, "L2": 2, "L3": 3, "L4": 4}
ORIGIN = {"ocr": "图片·识别", "asr": "语音·转写", "extracted": "文件·抽取", "caption": "链接"}


def mask(text: str) -> str:
    text = re.sub(r"(?<!\d)(\d{6})(\d{8})(\d{3}[\dXx])(?!\d)", lambda m: "**************" + m.group(3)[-4:], text)
    text = re.sub(r"(?<!\d)(1[3-9]\d)(\d{4})(\d{4})(?!\d)", r"\1****\3", text)
    text = re.sub(r"(?<!\d)(\d{12,15})(\d{4})(?!\d)", lambda m: "*" * len(m.group(1)) + m.group(2), text)
    return text


def line_for(r: dict) -> str:
    t = r.get("sent_at", "")[11:16]
    who = r.get("sender_name") or r.get("sender_id", "未知")
    role = r.get("sender_role", "未知")
    org = r.get("sender_org")
    tag = f"{who}（{role}{'·' + org if org else ''}）"
    rid = r.get("record_id", "")
    if r.get("recalled"):
        return f"[{t}] {tag} [已撤回]  ‹{rid}›"
    body = (r.get("text") or "").strip().replace("\n", " ")
    pii = r.get("pii_types") or []
    if r.get("msg_type") == "file" and "名单" in pii:
        body = "[文件] 名单文件，见原件"
    else:
        body = mask(body)
        origin = ORIGIN.get(r.get("text_origin", ""))
        if origin:
            body = f"[{origin}] {body}"
        elif r.get("msg_type") == "file":
            body = f"[文件] {body}"
    extra = ""
    atts = r.get("attachments") or []
    if atts:
        extra += "  〔原件：" + "；".join(a.get("storage_path") or a.get("file_name", "") for a in atts) + "〕"
    if r.get("masked_in_digest") or r.get("sensitivity") == "L4":
        extra += "  〔L4，已遮蔽〕"
    for fw in r.get("forwarded") or []:
        extra += f"\n    ↳ 转发：{fw.get('sender_name', '')}：{mask(fw.get('text', ''))}"
    return f"[{t}] {tag} {body}  ‹{rid}›{extra}"


def find_project_dir(base: Path, pid: str):
    hits = sorted((base / "项目").glob(f"{pid}_*"))
    return hits[0] if hits else None


def append(path: Path, header: str, lines):
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    new = [l for l in lines if f"‹{re.search(r'‹(.+?)›', l).group(1)}›" not in existing]
    if not new:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        if not existing:
            f.write(header + "\n\n")
        f.write("\n".join(new) + "\n")
    return len(new)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("jsonl")
    ap.add_argument("library")
    ap.add_argument("--batch", default="")
    a = ap.parse_args()
    base = Path(a.library)
    records = [json.loads(l) for l in Path(a.jsonl).read_text(encoding="utf-8").splitlines() if l.strip()]
    # 撤回事件：把原消息标为已撤回
    recalled = {r.get("source_msg_id") for r in records if r.get("action") == "recall"}
    groups, pending = defaultdict(list), defaultdict(list)
    for r in records:
        if r.get("action") == "recall":
            continue
        if r.get("source_msg_id") in recalled:
            r["recalled"] = True
        day = r.get("sent_at", "")[:10]
        if r.get("attribution") in ("mapped", "confirmed") and r.get("project_ids"):
            for pid in r["project_ids"]:
                groups[(pid, day, r.get("conversation_name") or r.get("conversation_id"), r.get("conversation_kind", ""))].append(r)
        else:
            pending[day].append(r)
    written = 0
    for (pid, day, gname, kind), rs in sorted(groups.items()):
        pdir = find_project_dir(base, pid)
        if not pdir:
            pending[day] += rs
            continue
        rs.sort(key=lambda x: x.get("sent_at", ""))
        level = max((r.get("sensitivity", "L1") for r in rs), key=lambda x: LEVEL_ORDER.get(x, 1))
        short = re.sub(r"[\\/:*?\"<>|\s]", "", str(gname))[:20]
        header = (f"# {day} {gname}\n\n项目：{pid}　群类型：{kind}　批次：{a.batch or '未注明'}"
                  f"　消息数：{len(rs)}　最高级别：{level}")
        written += append(pdir / "02_沟通记录" / f"{day}_{short}.md", header, [line_for(r) for r in rs])
    for day, rs in sorted(pending.items()):
        lines = [f"{line_for(r)}  〔群：{r.get('conversation_name') or r.get('conversation_id')}；可能项目：{','.join(r.get('project_ids') or []) or '未知'}〕"
                 for r in sorted(rs, key=lambda x: x.get("sent_at", ""))]
        written += append(base / "收件箱" / "待归属" / f"{day}.md", f"# 待归属 {day}", lines)
    print(f"写入 {written} 条（已存在的记录不重复写入）")


if __name__ == "__main__":
    main()
