#!/usr/bin/env python3
"""Skill 维护工具（X03）：同步、生成指令版、打包、校验。

用法：
  python3 tools/skilltool.py sync       把共用规则、模板、脚本和跨包副本复制进各 Skill 包
  python3 tools/skilltool.py build      生成指令版单文件到 adapters/generated/
  python3 tools/skilltool.py package    把每个 Skill 包打成 zip 到 dist/（供 WorkBuddy 等导入）
  python3 tools/skilltool.py validate   校验 Skill 包（frontmatter、九项、链接、副本一致、大小）
  python3 tools/skilltool.py all        依次执行 sync、build、package、validate

只用 Python 标准库。规则依据：D01 §7.5–7.6、D08。
"""
import hashlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".agents" / "skills"
SHARED = ROOT / "skill-source" / "shared"
TEMPLATES = ROOT / "templates"
TOOLS = ROOT / "tools"
GENERATED = ROOT / "adapters" / "generated"
DIST = ROOT / "dist"
MANIFEST = json.loads((ROOT / "skill-source" / "manifest.json").read_text(encoding="utf-8"))

REQUIRED_SECTIONS = ["## 1 ", "## 2 ", "## 3 ", "## 4 ", "## 5 ", "## 6 ", "## 7 ", "## 8 ", "## 9 "]
NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
MAX_SKILL_MD = 20_000  # 字符；超过时提示精简（D01 §8.3 第 7 条）


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def copy(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def sync():
    stamp = {}
    for name, spec in MANIFEST["skills"].items():
        pkg = SKILLS / name
        if not pkg.exists():
            print(f"[跳过] 缺少包 {name}")
            continue
        # 清理旧副本
        for sub in ("references/shared", "templates", "scripts"):
            d = pkg / sub
            if d.exists():
                shutil.rmtree(d)
        entries = {}
        for f in MANIFEST["shared"]:
            copy(SHARED / f, pkg / "references" / "shared" / f)
            entries[f"references/shared/{f}"] = sha(SHARED / f)
        for f in spec["templates"]:
            copy(TEMPLATES / f, pkg / "templates" / f)
            entries[f"templates/{f}"] = sha(TEMPLATES / f)
        for f in spec["scripts"]:
            copy(TOOLS / f, pkg / "scripts" / f)
            entries[f"scripts/{f}"] = sha(TOOLS / f)
        for c in spec["copies"]:
            src = ROOT / c["from"]
            copy(src, pkg / c["to"])
            entries[c["to"]] = sha(src)
        stamp[name] = entries
        print(f"[同步] {name}: {len(entries)} 个副本")
    (ROOT / "skill-source" / "sync-stamp.json").write_text(
        json.dumps(stamp, ensure_ascii=False, indent=2), encoding="utf-8")


def strip_frontmatter(text: str):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def build():
    GENERATED.mkdir(parents=True, exist_ok=True)
    header = "<!-- 由 tools/skilltool.py build 生成，不手改。源文件：.agents/skills/{name}/ -->\n\n"
    for name in MANIFEST["skills"]:
        pkg = SKILLS / name
        meta, body = strip_frontmatter((pkg / "SKILL.md").read_text(encoding="utf-8"))
        parts = [header.format(name=name),
                 f"# 指令版：{name}\n\n> 用途：{meta.get('description', '')}\n\n"
                 "> 使用方法：作为项目或智能体的指令，或放进任务包。通用规则见 shared-rules.md；"
                 "project-hub 的场景见 scenarios.md。\n\n", body.strip(), "\n"]
        refs = sorted((pkg / "references").glob("*.md"))
        refs += sorted((pkg / "references" / "cards").glob("*.md")) if (pkg / "references" / "cards").exists() else []
        for ref in refs:
            parts.append(f"\n\n---\n\n<!-- 附：references/{ref.relative_to(pkg / 'references')} -->\n\n")
            parts.append(ref.read_text(encoding="utf-8").strip() + "\n")
        (GENERATED / f"{name}.md").write_text("".join(parts), encoding="utf-8")
        print(f"[指令版] {name}.md")
    # 共用规则合集
    shared_parts = ["<!-- 由 tools/skilltool.py build 生成，不手改。源文件：skill-source/shared/ -->\n\n"
                    "# 通用规则合集（D05、D06、D07、D09、D10）\n"]
    for f in MANIFEST["shared"]:
        shared_parts.append(f"\n\n---\n\n<!-- {f} -->\n\n" + (SHARED / f).read_text(encoding="utf-8").strip() + "\n")
    (GENERATED / "shared-rules.md").write_text("".join(shared_parts), encoding="utf-8")
    # 场景合集
    hub = SKILLS / "project-hub" / "references"
    sc_parts = ["<!-- 由 tools/skilltool.py build 生成，不手改。源文件：project-hub/references/ -->\n\n"
                "# 场景路由表与场景卡合集\n\n", (hub / "routing.md").read_text(encoding="utf-8").strip() + "\n"]
    for f in sorted((hub / "scenarios").glob("*.md")):
        sc_parts.append(f"\n\n---\n\n" + f.read_text(encoding="utf-8").strip() + "\n")
    (GENERATED / "scenarios.md").write_text("".join(sc_parts), encoding="utf-8")
    print("[指令版] shared-rules.md、scenarios.md")


def package():
    DIST.mkdir(exist_ok=True)
    for name in MANIFEST["skills"]:
        pkg = SKILLS / name
        out = DIST / f"{name}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(pkg.rglob("*")):
                if f.is_file() and not f.name.startswith("."):
                    z.write(f, Path(name) / f.relative_to(pkg))
        print(f"[打包] {out.relative_to(ROOT)}")


def validate() -> int:
    problems = []
    stamp_path = ROOT / "skill-source" / "sync-stamp.json"
    stamp = json.loads(stamp_path.read_text(encoding="utf-8")) if stamp_path.exists() else {}
    for name, spec in MANIFEST["skills"].items():
        pkg = SKILLS / name
        sk = pkg / "SKILL.md"
        if not sk.exists():
            problems.append(f"{name}: 缺 SKILL.md")
            continue
        text = sk.read_text(encoding="utf-8")
        meta, body = strip_frontmatter(text)
        keys = set(meta)
        if keys != {"name", "description"}:
            problems.append(f"{name}: frontmatter 只能有 name 和 description，实际 {sorted(keys)}")
        if meta.get("name") != name:
            problems.append(f"{name}: name 与文件夹名不一致（{meta.get('name')}）")
        if not NAME_RE.match(meta.get("name", "")):
            problems.append(f"{name}: name 不符合小写英文加连字符")
        desc = meta.get("description", "")
        if not (20 <= len(desc) <= 1024):
            problems.append(f"{name}: description 长度 {len(desc)} 不在 20–1024")
        for sec in REQUIRED_SECTIONS:
            if sec not in body:
                problems.append(f"{name}: SKILL.md 缺少第 {sec.strip('# ').strip()} 项")
        if len(text) > MAX_SKILL_MD:
            problems.append(f"{name}: SKILL.md {len(text)} 字符，超过 {MAX_SKILL_MD}，建议把细节移到 references")
        # 链接与引用的文件
        for ref in re.findall(r"`((?:references|templates|scripts)/[^`*]+?)`", text):
            ref = ref.split(" ")[0]
            if "{" in ref or ref.endswith("/"):
                continue
            if not (pkg / ref).exists():
                problems.append(f"{name}: SKILL.md 引用的 {ref} 不存在")
        # 副本一致
        for rel, h in stamp.get(name, {}).items():
            p = pkg / rel
            if not p.exists():
                problems.append(f"{name}: 缺同步副本 {rel}（请运行 sync）")
            elif sha(p) != h:
                problems.append(f"{name}: 副本 {rel} 被改动或已过期（请改源文件后重新 sync）")
        # 源文件比副本新
        for f in MANIFEST["shared"]:
            p = pkg / "references" / "shared" / f
            if p.exists() and sha(p) != sha(SHARED / f):
                problems.append(f"{name}: 共用规则 {f} 与源文件不一致（请运行 sync）")
        # 文件名只用 ASCII（打包兼容）
        for f in pkg.rglob("*"):
            if any(ord(ch) > 127 for ch in f.name):
                problems.append(f"{name}: 包内文件名含非 ASCII 字符：{f.relative_to(pkg)}")
    if problems:
        print("校验发现问题：")
        for p in problems:
            print(" -", p)
        return 1
    print(f"校验通过：{len(MANIFEST['skills'])} 个 Skill 包")
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "sync":
        sync()
    elif cmd == "build":
        build()
    elif cmd == "package":
        package()
    elif cmd == "validate":
        sys.exit(validate())
    elif cmd == "all":
        sync(); build(); package(); sys.exit(validate())
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
