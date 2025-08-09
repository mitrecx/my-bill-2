# 分类规则管理工具使用说明

## 概述

分类规则功能已成功集成到账单分类系统中。现在导入账单时，系统会：

1. **优先使用规则分类**：根据 `classification_rules` 表中的规则进行匹配
2. **AI分类补充**：对于规则未匹配的账单，使用AI进行分类
3. **提高效率**：规则分类速度快，AI分类准确性高

## 管理工具

使用 `manage_classification_rules.py` 脚本管理分类规则：

### 查看所有规则
```bash
cd backend/scripts
python manage_classification_rules.py list
```

### 添加新规则
```bash
# 语法：python manage_classification_rules.py add "规则文本" 来源类型 目标分类 [--priority 优先级]
python manage_classification_rules.py add "滴滴" alipay "交通出行"
python manage_classification_rules.py add "7-11" all "日用百货" --priority 8
```

### 删除规则
```bash
python manage_classification_rules.py delete 规则ID
```

### 切换规则状态
```bash
python manage_classification_rules.py toggle 规则ID
```

### 测试规则匹配
```bash
python manage_classification_rules.py test "滴滴" "滴滴出行-行程费用"
```

### 查看统计信息
```bash
python manage_classification_rules.py stats
```

## 规则格式

支持多种规则格式：

1. **简单关键词**：`滴滴`
2. **多关键词**：`keywords:滴滴,出行,打车`
3. **正则表达式**：`regex:滴滴.*出行`

## 来源类型

- `alipay`：支付宝账单
- `jd`：京东账单
- `cmb`：招商银行账单
- `all`：所有来源

## 优先级

- 数值越大，优先级越高
- 建议范围：1-10
- 默认值：5

## 测试结果

根据最新测试：
- 规则分类成功率：50%
- AI分类补充后总成功率：100%
- 批量分类性能良好

## 常用规则示例

已创建的常用规则包括：
- 交通出行：滴滴、地铁、公交、加油站
- 餐饮美食：美团、饿了么、肯德基、星巴克
- 日用百货：7-11、全家、超市
- 医疗健康：医院、药店
- 投资理财：基金、股票

## 注意事项

1. 规则按优先级和创建时间排序
2. 同一账单只会匹配第一个符合条件的规则
3. 目标分类必须在系统中存在
4. 建议定期检查和优化规则