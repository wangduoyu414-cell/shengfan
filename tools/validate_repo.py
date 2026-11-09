#!/usr/bin/env python3
"""方法库自检（X08，V04 的自动部分）。

用法：python3 tools/validate_repo.py
检查：
  1. 各类编号的引用都在已定义的范围内；
  2. 场景编号在路由表、场景卡、D03 场景矩阵三处一致，路由表指向的场景卡文件存在；
  3. 文档中的相对链接都能找到文件；
  4. manifest 中的模板、脚本、共用规则都存在；
  5. 方法库中没有写入密钥（access_token、Bearer 令牌）。
只用 Python 标准库。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"dist", ".git", "generated"}
RANGES = {
    "DQ": (1, 30), "TP": (1, 20), "S": (0, 8), "A": (1, 8), "X": (1, 8), "I": (1, 5), "V": (1, 4),
    "RG": (1, 3), "D": (1, 12), "M": (1, 16), "W": (0, 10), "CK": (1, 12), "AL": (1, 8), "SC": (1, 47),
    "T": (1, 4), "L": (1, 4), "G": (1, 7),
}
PATTERNS = {
    "DQ": r"(?<![A-Za-z])DQ(\d{2})", "TP": r"(?<![A-Za-z])TP(\d{2})", "S": r"(?<![A-Za-z])S(0\d)(?!\d)",
    "A": r"(?<![A-Za-z])A(0\d)(?!\d)", "X": r"(?<![A-Za-z])X(0\d)(?!\d)", "I": r"(?<![A-Za-z])I(0\d)(?!\d)",
    "V": r"(?<![A-Za-z-])V(0\d)(?!\d)", "RG": r"(?<![A-Za-z])RG(0\d)", "D": r"(?<![A-Za-z])D(\d{2})(?!\d)",
    "M": r"(?<![A-Za-z])M(\d{2})(?!\d)", "W": r"(?<![A-Za-z])W(\d{2})(?!\d)", "CK": r"(?<![A-Za-z])CK(\d{2})",
    "AL": r"(?<![A-Za-z])AL(\d)(?!\d)", "SC": r"(?<![A-Za-z])SC(\d{2})", "T": r"(?<![A-Za-z])T([1-9])(?!\d)",
    "L": r"(?<![A-Za-z])L([1-9])(?!\d)", "G": r"(?<![A-Za-z])G([1-9])(?!\d)",
}


def md_files():
    for p in ROOT.rglob("*.md"):
        if not (set(p.relative_to(ROOT).parts) & SKIP_DIRS) and "references/shared" not in str(p):
            yield p


def main():
    problems = []
    texts = {p: p.read_text(encoding="utf-8") for p in md_files()}

    # 1 编号范围
    for prefix, pat in PATTERNS.items():
        lo, hi = RANGES[prefix]
        for p, t in texts.items():
            for m in re.finditer(pat, t):
                n = int(m.group(1))
                if not lo <= n <= hi:
                    problems.append(f"编号越界 {prefix}{m.group(1)}：{p.relative_to(ROOT)}")

    # 2 场景一致
    hub = ROOT / ".agents/skills/project-hub/references"
    routing = (hub / "routing.md").read_text(encoding="utf-8")
    route_ids = set(re.findall(r"^\| SC(\d{2}) ", routing, re.M))
    card_ids = set()
    for f in (hub / "scenarios").glob("*.md"):
        card_ids |= set(re.findall(r"^## SC(\d{2}) ", f.read_text(encoding="utf-8"), re.M))
    d03 = (ROOT / "docs/03_场景覆盖与一致性校验.md").read_text(encoding="utf-8")
    d03_ids = set(re.findall(r"^\| SC(\d{2}) ", d03, re.M))
    if not (route_ids == card_ids == d03_ids):
        problems.append(f"场景编号不一致：路由表 {len(route_ids)}，场景卡 {len(card_ids)}，D03 {len(d03_ids)}；"
                        f"差异 {sorted((route_ids ^ card_ids) | (route_ids ^ d03_ids))}")
    for card in set(re.findall(r"scenarios/([A-I]-[a-z]+\.md)", routing)):
        if not (hub / "scenarios" / card).exists():
            problems.append(f"路由表指向的场景卡不存在：{card}")

    # 3 相对链接
    for p, t in texts.items():
        for target in re.findall(r"\]\(([^)#\s]+?)(?:#[^)]*)?\)", t):
            if re.match(r"^[a-z]+:", target):
                continue
            if not (p.parent / target).exists():
                problems.append(f"链接找不到：{p.relative_to(ROOT)} → {target}")

    # 4 manifest
    man = json.loads((ROOT / "skill-source/manifest.json").read_text(encoding="utf-8"))
    for f in man["shared"]:
        if not (ROOT / "skill-source/shared" / f).exists():
            problems.append(f"manifest 共用规则不存在：{f}")
    for name, spec in man["skills"].items():
        if not (ROOT / ".agents/skills" / name / "SKILL.md").exists():
            problems.append(f"manifest 中的 Skill 不存在：{name}")
        for f in spec["templates"]:
            if not (ROOT / "templates" / f).exists():
                problems.append(f"{name}：模板不存在 {f}")
        for f in spec["scripts"]:
            if not (ROOT / "tools" / f).exists():
                problems.append(f"{name}：脚本不存在 {f}")

    # 5 密钥
    secret = re.compile(r"access_token=(?!\{|你的|\$|<|&|\.\.\.|…)[A-Za-z0-9._-]{12,}|Bearer\s+[A-Za-z0-9._-]{20,}")
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in {".md", ".json", ".py", ".txt", ".toml", ".yaml", ".yml"} \
                and not (set(p.relative_to(ROOT).parts) & SKIP_DIRS):
            if secret.search(p.read_text(encoding="utf-8", errors="ignore")):
                problems.append(f"疑似写入了密钥：{p.relative_to(ROOT)}")

    if problems:
        print("自检发现问题：")
        for x in problems:
            print(" -", x)
        sys.exit(1)
    print(f"自检通过：{len(texts)} 个文档；场景 {len(route_ids)} 个，三处一致。")


if __name__ == "__main__":
    main()
