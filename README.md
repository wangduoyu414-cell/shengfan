# AI 协同工作体系（方法库）

本目录是公司 AI 协同工作体系的**方法库**：设计、通用规则、Skill、场景路由、模板、工具、平台适配和检验样本。客户和项目的事实不放在这里，放在业务库和乐享（总纲第 3.2、6、10 章）。

- **业务**：为金融等机构客户提供会议活动、培训学习、客户活动和出行福利（定制游、研学、游学、疗休养、团建）等综合服务；项目来自招投标、框架内二次比选和直接委托。
- **分工**：GPT 做复杂判断、创意、图片生成与编辑、高难度理解，以及 Skill 和工具的设计优化；WorkBuddy 和豆包同档，做重复性、文案、整理归档和中文语境的工作。所有 Skill 和资产在三个平台上都能用。
- **信息来源**：企业微信会话存档（摄取口径 D04）、乐享知识库（接入方案 D12）、人工投递的文件和纪要。

---

## 当前状态（v1.0，2026-11-09）

| 阶段 | 状态 |
|---|---|
| 第一期 顶层设计 | 已完成并确认 |
| 第二至四期 方法库建设 | 已完成：通用规则、9 个 Skill、47 张场景卡、20 个模板、成本测算表、8 个工具、平台适配、检验样本、登记、使用手册；自动校验通过 |
| 乐享接入 | 可行性已验证（服务在线、标准 OAuth）；登录后的验证待做 |
| 尚需在公司完成 | 三个平台实测、乐享登录验证、公司参数与品牌素材、试点项目、真实样本、培训 |

需要公司提供或决定的事项见 [待定事项登记](registry/RG02_待定事项登记.md)。

---

## 内容分层：通用规则与具体场景

| 层 | 回答什么 | 位置 |
|---|---|---|
| 1 通用规则层 | 任何任务都必须遵守什么 | [skill-source/shared/](skill-source/shared/00-index.md)：D05 记录规范、D06 分工路由与复核、D07 数据分级、D09 报价口径、D10 视觉规范 |
| 2 路由层 | 这句话或这个事件属于哪个场景 | [场景路由表](.agents/skills/project-hub/references/routing.md) |
| 3 场景层 | 这个场景按什么顺序经过哪些 Skill | [场景卡](.agents/skills/project-hub/references/scenarios/A-intake.md)（A–I 九组，47 张） |
| 4 方法层 | 某个 Skill 在某种模式下怎么做 | 各 Skill 的 references/modes.md |
| 5 素材层 | 用什么格式、参照什么内容 | [templates/](templates/TP01-project-card.md)、策划卡、共享资产 |

下层只引用上层的编号，不复制上层原文；冲突时上层优先。完整说明见总纲第 3.6、3.7 节。

---

## 阅读顺序

| 读者 | 先读 |
|---|---|
| 负责人、建设方 | [顶层设计总纲](docs/01_顶层设计总纲.md) → [产物全清单](docs/02_产物全清单.md) → [场景覆盖与一致性校验](docs/03_场景覆盖与一致性校验.md) → [待定事项](registry/RG02_待定事项登记.md) |
| 员工 | [使用手册与角色口令卡](docs/11_使用手册与角色口令卡.md) |
| AI 协同负责人 | [平台适配与兼容规范](adapters/D08_平台适配与兼容规范.md) → [兼容矩阵](adapters/兼容矩阵.md) → [乐享接入方案](docs/12_乐享知识库接入方案.md) |
| 会话存档开发方 | [聊天记录摄取口径](docs/04_聊天记录摄取口径.md) |
| 维护方法库的 AI | [AGENTS.md](AGENTS.md) |

---

## 目录

```
./
├── README.md、AGENTS.md
├── docs/                    设计与说明：D01–D04、D11、D12
├── skill-source/
│   ├── shared/              通用规则（唯一来源）：00 索引、D05、D06、D07、D09、D10
│   └── manifest.json        每个 Skill 需要同步的规则、模板、脚本
├── .agents/skills/          9 个 Skill 包（Codex 自动发现；其他平台导入 dist/ 下的 zip）
│   ├── project-hub/         主 Skill：路由表、47 张场景卡、P1–P6 流程
│   ├── intake-update/       资料收录与项目更新
│   ├── brief-analysis/      需求与标书解析
│   ├── planning-design/     策划与方案设计（四张策划卡）
│   ├── sourcing-costing/    资源询价与成本报价
│   ├── deliverable-production/  成果制作
│   ├── change-review/       变更与一致性复核
│   ├── delivery-settlement/ 执行交付与结算（第二批）
│   └── closeout-review/     复盘与资产沉淀（第二批）
├── templates/               TP01–TP20、X01 成本测算表、brand/（待提供）
├── tools/                   X01–X08 工具
├── adapters/                D08、兼容矩阵、gpt/、workbuddy/、doubao/、lexiang/、generated/（指令版）
├── tests/                   V01 样本（合成）、V02 兼容用例、V03 情景推演、V04 一致性检查
├── registry/                RG01 扩展登记、RG02 待定事项、RG03 变更记录
├── examples/示例业务库/      合成的业务库示例（演示与测试用）
└── dist/                    Skill 导入包（生成）
```

---

## 常用命令

```bash
python3 tools/skilltool.py all
```

```bash
python3 tools/validate_repo.py
```

```bash
python3 tools/init_project.py init-library {业务库路径}
```

```bash
python3 tools/init_project.py new-project {业务库路径} --client C-001 --client-short 客户简称 --name 项目简称
```

```bash
python3 tools/check_consistency.py {项目工作区路径}
```

```bash
python3 tools/remind.py {业务库路径}
```

## 标记约定

【定】本期确定 · 【默认】默认做法，可调整 · 【待定】需要决策或实测 · 【预留】为未来保留
