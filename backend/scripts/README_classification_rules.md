# 分类规则管理工具使用说明

## 概述

分类规则用于在 **AI 自动分类** 时注入提示词，供模型 **优先参考**。系统 **不在后端做正则或关键词硬匹配**。

导入账单并开启「导入后 AI 自动分类」时，流程为：

1. 读取当前用户启用的分类规则（按来源、收支类型、优先级筛选）
2. 将规则格式化为自然语言，写入 AI 提示词
3. AI 结合规则与账单描述选择分类；无适用规则时再智能推断

规则 CRUD 可通过 Web「分类规则」页、REST API 或 MCP 工具完成。

## 规则字段

| 字段 | 说明 |
|------|------|
| `rule_text` | 供 AI 参考的自然语言描述（如「滴滴」「7-11」），**不是正则表达式** |
| `source_type` | 适用来源：`alipay` / `jd` / `cmb` / `wechat` / `meituan` / `manual` / `all` |
| `transaction_type` | 适用收支类型：`expense` / `income` / `transfer` |
| `target_category` | 目标分类名称（须为系统中已存在的分类） |
| `priority` | 优先级，数值越大越靠前展示给 AI |
| `is_active` | 是否启用 |

## 管理脚本

```bash
cd backend/scripts
python manage_classification_rules.py list
python manage_classification_rules.py add "滴滴" alipay "交通出行" --transaction-type expense --priority 10
python manage_classification_rules.py preview "滴滴" "滴滴出行-行程费用"
python manage_classification_rules.py toggle 规则ID
python manage_classification_rules.py delete 规则ID
python manage_classification_rules.py stats
```

`preview` 展示规则注入 AI 提示词时的格式，**不代表程序硬匹配结果**。

## 编写建议

- `rule_text` 写简短、可识别的线索（商户名、平台关键词）
- 同一 `(rule_text, source_type, transaction_type)` 不可重复
- 支出/收入规则的目标分类须与收支类型一致
- 需要覆盖多种收支类型时，分别建多条规则

## 常用示例

| rule_text | source_type | transaction_type | target_category |
|-----------|-------------|------------------|-----------------|
| 滴滴 | alipay | expense | 交通出行 |
| 美团 | all | expense | 食品餐饮 |
| 退款 | alipay | income | 退款收入 |

## 注意事项

1. 规则按用户隔离，仅对规则创建者的 AI 分类生效
2. MCP 导入账单时，Agent 应 `query_classification_rules` 并以与 AI 相同的方式参考规则选类
3. 关闭「AI 自动分类」时，规则不会自动生效
