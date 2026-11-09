# 方法库维护约定（给维护方法库的 AI，例如 Codex）

本目录是 AI 协同工作体系的方法库，不含客户事实。入口说明见 README.md，上位设计见 docs/01_顶层设计总纲.md。

## 分层（不要混写）

| 层 | 位置 | 只写什么 |
|---|---|---|
| 通用规则 | skill-source/shared/（D05、D06、D07、D09、D10） | 对所有场景都成立的规则 |
| 路由 | .agents/skills/project-hub/references/routing.md | 说法或事件 → 场景 → 路径 |
| 场景 | .agents/skills/project-hub/references/scenarios/ | 跨 Skill 的路径；通用规则只引用编号 |
| 方法 | .agents/skills/*/references/modes.md 等 | 单个 Skill 在某个模式下的做法 |
| 素材 | templates/、策划卡 | 格式与内容参照 |

## 修改规则

1. 共用规则只改 skill-source/shared/；模板只改 templates/；脚本只改 tools/。各 Skill 包中的 references/shared/、templates/、scripts/ 是同步副本，不要手改。
2. 改完运行：`python3 tools/skilltool.py all`，再运行 `python3 tools/validate_repo.py`；两者都通过才算完成。
3. Skill 包内的文件名只用 ASCII；SKILL.md 的 frontmatter 只写 name 和 description；正文保留九项（D01 §7.6）。
4. 新增场景时，路由表、场景卡和 docs/03 的场景矩阵三处同时改；新增 Skill 或模板时，同时改 skill-source/manifest.json 和 docs/02。
5. 不在任何文件里写入令牌或密钥。
6. 每次改动在 registry/RG03_变更记录.md 记一条。
