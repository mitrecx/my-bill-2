#!/usr/bin/env python3
"""
测试清理后的CMB解析器
验证移除硬编码分类逻辑后解析器是否正常工作
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from parsers.cmb_parser import CMBParser

def test_cmb_parser_without_hardcoded_categories():
    """测试清理后的CMB解析器"""
    print("🧪 测试清理后的CMB解析器...")
    
    # 模拟CMB账单文本内容
    test_content = """
2024-01-15
CNY
-500.00
10000.00
午餐-麦当劳
麦当劳餐厅

2024-01-16
CNY
3000.00
13000.00
工资发放
信雅达系统工程股份有限公司

2024-01-17
CNY
-1200.00
11800.00
基金购买
天弘基金管理有限公司

2024-01-18
CNY
800.00
12600.00
基金赎回
天弘基金管理有限公司

2024-01-19
CNY
-50.00
12550.00
打车费用
滴滴出行
"""
    
    parser = CMBParser()
    result = parser.parse_content(test_content)
    
    print(f"✅ 解析成功: {len(result.success_records)} 条记录")
    print(f"❌ 解析失败: {len(result.failed_records)} 条记录")
    
    # 检查解析结果
    for i, record in enumerate(result.success_records, 1):
        print(f"\n📋 记录 {i}:")
        print(f"   交易时间: {record.get('transaction_time')}")
        print(f"   交易类型: {record.get('transaction_type')}")
        print(f"   金额: {record.get('amount')}")
        print(f"   描述: {record.get('transaction_desc')}")
        print(f"   对手方: {record.get('counter_party')}")
        print(f"   分类: {record.get('category', '未设置')}")  # 应该是None或未设置
        print(f"   来源: {record.get('source_type')}")
    
    # 验证关键点
    print("\n🔍 验证关键点:")
    
    # 1. 检查是否没有硬编码分类
    categories_found = [record.get('category') for record in result.success_records if record.get('category')]
    if not categories_found:
        print("✅ 确认：没有硬编码分类，分类字段为空")
    else:
        print(f"❌ 发现硬编码分类: {categories_found}")
    
    # 2. 检查交易类型是否正确设置
    transaction_types = [record.get('transaction_type') for record in result.success_records]
    expected_types = ['支出', '收入', '支出', '收入', '支出']
    if transaction_types == expected_types:
        print("✅ 交易类型设置正确")
    else:
        print(f"❌ 交易类型不正确: 期望 {expected_types}, 实际 {transaction_types}")
    
    # 3. 检查金额是否为正数
    amounts = [float(record.get('amount', 0)) for record in result.success_records]
    if all(amount > 0 for amount in amounts):
        print("✅ 所有金额都是正数")
    else:
        print(f"❌ 发现负数金额: {amounts}")
    
    # 4. 检查必要字段是否存在
    required_fields = ['transaction_time', 'transaction_type', 'amount', 'transaction_desc', 'source_type']
    all_fields_present = True
    for record in result.success_records:
        for field in required_fields:
            if field not in record or record[field] is None:
                print(f"❌ 记录缺少必要字段 {field}: {record}")
                all_fields_present = False
                break
    
    if all_fields_present:
        print("✅ 所有记录都包含必要字段")
    
    print("\n🎯 测试总结:")
    print(f"   - 解析成功率: {len(result.success_records)}/{len(result.success_records) + len(result.failed_records)}")
    print(f"   - 硬编码分类已清理: {'是' if not categories_found else '否'}")
    print(f"   - 交易类型正确: {'是' if transaction_types == expected_types else '否'}")
    print(f"   - 金额格式正确: {'是' if all(amount > 0 for amount in amounts) else '否'}")
    print(f"   - 必要字段完整: {'是' if all_fields_present else '否'}")

if __name__ == "__main__":
    test_cmb_parser_without_hardcoded_categories()