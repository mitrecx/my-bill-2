#!/usr/bin/env python3
"""
调试美团账单支付退款配对功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.parsers.meituan_parser import MeituanParser
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_pairing():
    """调试配对逻辑"""
    
    # 美团账单文件路径
    file_path = "/Users/chenxing/projects/my-bills-2/bills/美团账单(20250101-20250401).csv"
    
    # 创建解析器
    parser = MeituanParser()
    
    # 解析文件
    result = parser.parse_file(file_path)
    
    print(f"解析结果: 成功{len(result.success_records)}条, 失败{len(result.failed_records)}条")
    
    # 分析原始数据
    print("\n=== 原始数据分析 ===")
    payment_records = []
    refund_records = []
    
    for i, record in enumerate(result.success_records):
        raw_data = record.get('raw_data', {})
        category = raw_data.get('transaction_category', '')
        income_expense = raw_data.get('income_expense', '')
        title = record.get('transaction_desc', '')
        amount = record.get('amount', '')
        
        print(f"{i+1}. {title} | {category} | {income_expense} | {amount}")
        
        if category == '支付' and income_expense == '支出':
            payment_records.append((i, record))
        elif category == '退款' and income_expense == '收入':
            refund_records.append((i, record))
    
    print(f"\n找到支付记录: {len(payment_records)}条")
    print(f"找到退款记录: {len(refund_records)}条")
    
    # 手动检查配对
    print("\n=== 手动配对检查 ===")
    pairs_found = 0
    
    for pay_idx, pay_record in payment_records:
        pay_title = pay_record.get('transaction_desc', '')
        pay_amount = pay_record.get('amount', '')
        
        for ref_idx, ref_record in refund_records:
            ref_title = ref_record.get('transaction_desc', '')
            ref_amount = ref_record.get('amount', '')
            
            if pay_title == ref_title and pay_amount == ref_amount:
                pairs_found += 1
                print(f"配对 {pairs_found}: {pay_title} | {pay_amount}")
                print(f"  支付记录索引: {pay_idx}")
                print(f"  退款记录索引: {ref_idx}")
    
    print(f"\n总共找到 {pairs_found} 对匹配记录")
    
    # 检查最终结果中的transaction_type
    print("\n=== 最终结果分析 ===")
    expense_count = 0
    income_count = 0
    transfer_count = 0
    
    for record in result.success_records:
        transaction_type = record.get('transaction_type')
        income_expense = record.get('income_expense')
        
        print(f"记录: {record.get('transaction_desc')} | transaction_type: {transaction_type} | income_expense: {income_expense}")
        
        if transaction_type == 'expense':
            expense_count += 1
        elif transaction_type == 'income':
            income_count += 1
        elif transaction_type == 'transfer' or income_expense == '不计收支':
            transfer_count += 1
    
    print(f"\n最终统计:")
    print(f"支出: {expense_count}条")
    print(f"收入: {income_count}条") 
    print(f"不计收支: {transfer_count}条")
    
    if transfer_count == pairs_found * 2:
        print("✅ 配对逻辑正确工作")
    else:
        print("❌ 配对逻辑有问题")

if __name__ == "__main__":
    debug_pairing()