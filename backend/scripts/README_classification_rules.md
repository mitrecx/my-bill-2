# 分类规则管理工具使用说明

## 概述

分类规则支持 **个人级** 与 **家庭级** 两种作用域，用于 **AI 自动分类** 时注入提示词，供模型 **优先参考**（非程序硬匹配）。

- **personal（个人）**：仅对创建者生效，AI 分类时只使用该用户自己的个人规则
- **family（家庭）**：对家庭成员共享，任意成员可管理；AI 分类时合并使用

## 规则字段

| 字段 | 说明 |
|------|------|
| `scope` | 作用域：`personal` / `family` |
| `family_id` | 家庭级规则所属家庭（个人级为 null） |
| `rule_text` | 供 AI 参考的自然语言描述 |
| `source_type` | 适用来源 |
| `transaction_type` | 适用收支类型 |
| `target_category` | 目标分类名称 |
| `created_by` | 创建者 |

## 管理脚本

```bash
cd backend/scripts
python manage_classification_rules.py list
python manage_classification_rules.py add "滴滴" alipay "交通出行" --transaction-type expense --scope family --priority 10
python manage_classification_rules.py preview "滴滴" "滴滴出行-行程费用"
python manage_classification_rules.py stats
```

## 权限

- **个人规则**：仅创建者可查看、修改、删除
- **家庭规则**：家庭成员均可查看、修改、删除（须已加入家庭）
- **AI 自动分类**：合并使用当前用户的个人规则 + 其所在家庭的家庭规则

## 注意事项

1. 历史上已存在的规则在迁移后默认为 **家庭级**（`scope=family`）
2. 未加入家庭的用户仍可创建 **个人级** 规则，但无法创建家庭级规则
3. MCP `query_classification_rules` 返回当前 Key 用户可见的规则（个人 + 家庭）
