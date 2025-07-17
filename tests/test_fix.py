#!/usr/bin/env python3
"""测试修复后的京东解析器"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.jd_parser import JDParser

def test_amount_parsing():
    """测试金额解析功能"""
    parser = JDParser()
    
    # 测试用例
    test_cases = [
        {
            "amount": "577.61(已退款273.48)",
            "expected_amount": "304.13",  # 577.61 - 273.48
            "description": "部分退款"
        },
        {
            "amount": "100.00(已全额退款)",
            "expected_amount": "100.00",
            "description": "全额退款"
        },
        {
            "amount": "50.00",
            "expected_amount": "50.00",
            "description": "正常金额"
        }
    ]
    
    print("测试金额解析功能:")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {test_case['description']}")
        print(f"输入金额: {test_case['amount']}")
        
        # 创建测试记录
        test_record = {
            "amount": test_case["amount"],
            "income_expense": "支出",
            "merchant_name": "测试商户",
            "transaction_desc": "测试交易",
            "remark": ""
        }
        
        # 处理记录
        processed = parser._process_jd_fields(test_record)
        
        print(f"处理后金额: {processed.get('amount')}")
        print(f"期望金额: {test_case['expected_amount']}")
        print(f"备注: {processed.get('remark', '无')}")
        
        # 验证结果
        if processed.get('amount') == test_case['expected_amount']:
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")

def test_csv_parsing():
    """测试CSV文件解析"""
    csv_file = "/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"
    
    if not os.path.exists(csv_file):
        print(f"CSV文件不存在: {csv_file}")
        return
    
    print("\n\n测试CSV文件解析:")
    print("=" * 50)
    
    parser = JDParser()
    result = parser.parse_file(csv_file)
    
    print(f"总记录数: {result.total_count}")
    print(f"成功解析: {result.success_count}")
    print(f"失败记录: {result.failed_count}")
    print(f"错误信息: {len(result.errors)}")
    
    # 查找包含问题金额的记录
    problem_records = []
    for record in result.success_records:
        # 检查原始数据中是否包含问题金额
        raw_data = record.get("raw_data", {})
        original_amount = raw_data.get("amount", "")
        if "577.61" in str(original_amount):
            problem_records.append(record)
    
    if problem_records:
        print(f"\n找到包含问题金额的记录: {len(problem_records)} 条")
        for i, record in enumerate(problem_records, 1):
            raw_data = record.get("raw_data", {})
            print(f"\n记录 {i}:")
            print(f"  原始金额: {raw_data.get('amount', '未知')}")
            print(f"  处理后金额: {record.get('amount', '未知')}")
            print(f"  交易类型: {record.get('transaction_type', '未知')}")
            print(f"  备注: {record.get('remark', '无')}")
    else:
        print("\n未找到包含问题金额的记录")
        
    # 检查是否有解析失败的记录
    if result.failed_count > 0:
        print(f"\n解析失败的记录: {result.failed_count} 条")
        for i, failed_record in enumerate(result.failed_records[:3], 1):  # 只显示前3条
            print(f"\n失败记录 {i}:")
            print(f"  错误: {failed_record.get('parse_error', '未知错误')}")
            print(f"  原始数据: {str(failed_record)[:100]}...")  # 只显示前100字符

if __name__ == "__main__":
    test_amount_parsing()
    test_csv_parsing()