#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.meituan_parser import MeituanParser
import json

def debug_record_structure():
    parser = MeituanParser()
    
    # 解析美团账单文件
    file_path = "/Users/chenxing/projects/my-bills-2/bills/美团账单(20250101-20250401).csv"
    result = parser.parse_file(file_path)
    
    print(f"解析结果: 成功{len(result.success_records)}条, 失败{len(result.failed_records)}条")
    
    if result.success_records:
        print("\n=== 第一条记录的完整结构 ===")
        first_record = result.success_records[0]
        
        # 手动打印记录结构，避免JSON序列化问题
        for key, value in first_record.items():
            print(f"  {key}: {value} ({type(value).__name__})")
        
        print("\n=== 前3条记录的关键字段 ===")
        for i, record in enumerate(result.success_records[:3]):
            print(f"\n记录 {i+1}:")
            print(f"  transaction_desc: {record.get('transaction_desc')}")
            print(f"  amount: {record.get('amount')}")
            print(f"  transaction_type: {record.get('transaction_type')}")
            print(f"  income_expense: {record.get('income_expense')}")
            
            raw_data = record.get('raw_data', {})
            print(f"  raw_data.transaction_category: {raw_data.get('transaction_category')}")
            print(f"  raw_data.income_expense: {raw_data.get('income_expense')}")

if __name__ == "__main__":
    debug_record_structure()