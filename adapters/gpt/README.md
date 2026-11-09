# GPT 平台接入说明（ChatGPT、Codex）

版本 v1.0 · 默认层级 T1（判断与创造、关键视觉、Skill 与工具的设计优化）

---

## 1 ChatGPT

### 1.1 加载 Skill【待实测入口】

- 方式一（原生）：在 ChatGPT 的技能管理中导入 `dist/` 下的 zip（至少导入 `project-hub`、`brief-analysis`、`planning-design`、`change-review`；其他按需）。团队可以通过插件统一分发。具体入口以当前版本为准。
- 方式二（项目）：建一个 ChatGPT 项目，项目指令粘贴 `platform-identity.md` 和 `../generated/project-hub.md`；上传 `../generated/shared-rules.md`、`../generated/scenarios.md` 和需要的 Skill 指令版作为项目文件。

### 1.2 平台身份声明

把 `platform-identity.md` 的内容放进项目指令或自定义指令的开头。

### 1.3 业务资料

ChatGPT 不能直接访问业务库。由执行层生成任务包（project-hub P4），把任务包里的文件上传到对话中。只上传准入级别以内的资料（D07 §2：L1、L2，L3 只给脱敏版本，L4 不上传）。

### 1.4 产出回收

ChatGPT 生成的文件下载后，按任务包中的产出要求（文件名、位置）保存到业务库，或交给主执行平台保存。

### 1.5 乐享【待实测】

在开发者模式下添加自定义连接器，地址 `https://mcp.lexiang-app.com/mcp?company_from={乐享code}`，认证选 OAuth。建议使用只开放 L1、L2 知识库的账号（D07 §5、DQ17）。不能使用时，由 WorkBuddy 检索后放进任务包。

---

## 2 Codex

### 2.1 加载 Skill

- 在方法库目录中工作时，Codex 自动发现 `.agents/skills/` 下的全部 Skill。
- 在业务库中工作时：把方法库的 `.agents/skills/` 复制或链接到业务库根目录，或安装为用户级技能（位置以 Codex 文档为准）【待实测】。

### 2.2 平台身份声明

在工作目录放一个 AGENTS.md，内容为 `platform-identity.md`。方法库根目录已有 AGENTS.md（维护方法库用）。

### 2.3 用途

- 设计和优化 Skill、模板、工具（方法库维护，见根目录 AGENTS.md）。
- 在本地业务库中执行 T1 任务（数据级别按 D07）。

### 2.4 乐享【待实测】

在 Codex 的 MCP 配置中添加远程服务器（配置示例见 `../lexiang/连接配置示例.md`）。
