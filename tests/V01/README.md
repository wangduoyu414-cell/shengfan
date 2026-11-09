# V01 Skill 检验样本集

版本 v1.0 · 2026-11-09

> **本目录全部是合成样本**：客户、人员、价格均为虚构，只用于检验 Skill 与工具的行为，不代表真实业务数据。

## 用法

1. 在被测平台加载对应 Skill（或指令版）。
2. 把"输入"交给它，按"任务"一栏的说法发起。
3. 对照"预期要点"逐条判定：全部满足为通过；记录不满足的条目和原因。
4. 结果写入 `adapters/兼容矩阵.md` 第 2 节。

| Skill | 样本 | 输入 | 任务 | 预期要点 |
|---|---|---|---|---|
| intake-update | 群聊批次 | `intake-update/sample_messages.jsonl`（先用 X06 转成摘要） | "更新项目 2026-001" | `intake-update/expected.md` |
| brief-analysis | 采购文件节选 | `brief-analysis/sample_tender.md` | "解析这份招标文件" | `brief-analysis/expected.md` |
| planning-design | 出行类需求 | `planning-design/sample_brief.md` | "给这个项目出三个方向" | `planning-design/expected.md` |
| sourcing-costing | 三家酒店报价＋测算表 | `sourcing-costing/sample_quotes.md`、`示例_成本测算_V1.xlsx` | "比较这几家酒店报价"；"按 40、50、60 人测算" | `sourcing-costing/expected.md` |
| deliverable-production | 主卡＋方案结构 | 示例业务库中的项目 2026-001 | "按主卡出对客 PPT 内容稿" | `deliverable-production/expected.md` |
| change-review | 变更请求＋不一致的成果 | `change-review/` | "客户改了人数，查影响"；"发送前检查" | `change-review/expected.md` |

## 真实样本（第三期补充）

从前期的 270 份招投标材料中，按产品族各选 1–2 份（共 5–8 份）作为 brief-analysis 的真实样本：

- 选择要求：采购文件完整、评分标准清楚、我方已知结果（中选或未中选）。
- 脱敏：客户名称换代号，联系人删除，金额保留（L3，只在国内平台测试）。
- 预期要点由商务负责人按实际情况填写。
- 扫描页先做文字识别。
