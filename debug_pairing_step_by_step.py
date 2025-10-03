#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.meituan_parser import MeituanParser

def debug_pairing_step_by_step():
    parser = MeituanParser()
    
    # 解析美团账单文件
    file_path = "/Users/chenxing/projects/my-bills-2/bills/美团账单(20250101-20250401).csv"
    result = parser.parse_file(file_path)
    
    print(f"解析结果: 成功{len(result.success_records)}条, 失败{len(result.failed_records)}条")
    
    # 模拟配对过程
    print("\n=== 模拟配对过程 ===")
    
    # 创建测试记录
    test_records = []
    for record in result.success_records:
        raw_data = record.get('raw_data', {})
        test_record = {
            'transaction_desc': record.get('transaction_desc'),
            'amount': record.get('amount'),
            'transaction_type': record.get('transaction_type'),
            'income_expense': record.get('income_expense'),
            'raw_data': raw_data
        }
        test_records.append(test_record)
    
    print(f"创建了 {len(test_records)} 条测试记录")
    
    # 手动执行配对逻辑
    paired_records = []
    processed_indices = set()
    
    for i, record in enumerate(test_records):
        if i in processed_indices:
            continue
            
        # 从raw_data中获取原始交易类型
        raw_data = record.get('raw_data', {})
        transaction_category = raw_data.get('transaction_category', '')
        
        print(f"\n处理记录 {i}: {record.get('transaction_desc')} | 原始类型: {transaction_category} | 交易类型: {record.get('transaction_type')}")
        
        # 如果是支付记录，寻找对应的退款记录
        if (transaction_category == '支付' and 
            record.get('transaction_type') == 'expense'):
            
            payment_title = record.get('transaction_desc', '')
            payment_amount = record.get('amount', '')
            
            print(f"  这是支付记录，寻找匹配的退款记录...")
            print(f"  支付标题: {payment_title}")
            print(f"  支付金额: {payment_amount}")
            
            # 寻找匹配的退款记录
            for j, other_record in enumerate(test_records):
                if j != i and j not in processed_indices:
                    other_raw_data = other_record.get('raw_data', {})
                    other_category = other_raw_data.get('transaction_category', '')
                    
                    if (other_category == '退款' and
                        other_record.get('transaction_type') == 'income'):
                        
                        refund_title = other_record.get('transaction_desc', '')
                        refund_amount = other_record.get('amount', '')
                        
                        print(f"    检查退款记录 {j}: {refund_title} | {refund_amount}")
                        
                        # 检查订单标题和金额是否完全匹配
                        if (payment_title == refund_title and 
                            payment_amount == refund_amount and
                            payment_title.strip() != '' and
                            payment_amount.strip() != ''):
                            
                            print(f"    ✅ 找到匹配！配对 {i} 和 {j}")
                            
                            # 修改支付记录
                            payment_record = record.copy()
                            payment_record['transaction_type'] = 'transfer'
                            payment_record['income_expense'] = '不计收支'
                            
                            # 修改退款记录
                            refund_record = other_record.copy()
                            refund_record['transaction_type'] = 'transfer'
                            refund_record['income_expense'] = '不计收支'
                            
                            paired_records.append(payment_record)
                            paired_records.append(refund_record)
                            
                            processed_indices.add(i)
                            processed_indices.add(j)
                            break
                        else:
                            print(f"    ❌ 不匹配: 标题={payment_title == refund_title}, 金额={payment_amount == refund_amount}")
            
            # 如果没找到配对，添加原记录
            if i not in processed_indices:
                print(f"  没找到配对，保持原记录")
                paired_records.append(record)
                processed_indices.add(i)
        else:
            # 非支付记录或已处理的记录，直接添加
            if i not in processed_indices:
                print(f"  非支付记录，直接添加")
                paired_records.append(record)
                processed_indices.add(i)
    
    print(f"\n配对完成，共 {len(paired_records)} 条记录")
    
    # 统计结果
    transfer_count = 0
    for record in paired_records:
        if record.get('income_expense') == '不计收支':
            transfer_count += 1
            print(f"不计收支记录: {record.get('transaction_desc')} | {record.get('amount')}")
    
    print(f"\n最终统计: {transfer_count} 条不计收支记录")

if __name__ == "__main__":
    debug_pairing_step_by_step()