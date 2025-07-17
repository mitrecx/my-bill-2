#!/usr/bin/env python3
"""测试完整的导入流程"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.jd_parser import JDParser
from config.database import get_db
from models.bill import Bill
from sqlalchemy.orm import sessionmaker

def test_full_import():
    """测试完整的导入流程"""
    csv_file = "/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"
    
    if not os.path.exists(csv_file):
        print(f"CSV文件不存在: {csv_file}")
        return
    
    # 解析文件
    parser = JDParser()
    result = parser.parse_file(csv_file)
    
    print(f"解析结果:")
    print(f"总记录数: {result.total_count}")
    print(f"成功解析: {result.success_count}")
    print(f"失败记录: {result.failed_count}")
    
    # 模拟上传API的验证逻辑
    valid_records = []
    invalid_records = []
    
    for record in result.success_records:
        # 检查必需字段
        if (record.get('amount') is None or 
            record.get('transaction_time') is None or 
            record.get('transaction_type') is None):
            invalid_records.append(record)
            print(f"无效记录: 金额={record.get('amount')}, 时间={record.get('transaction_time')}, 类型={record.get('transaction_type')}")
        else:
            valid_records.append(record)
    
    print(f"\n验证结果:")
    print(f"有效记录: {len(valid_records)}")
    print(f"无效记录: {len(invalid_records)}")
    
    # 显示包含退款的记录
    refund_records = []
    for record in valid_records:
        if "退款" in str(record.get('remark', '')):
            refund_records.append(record)
    
    print(f"\n包含退款信息的记录: {len(refund_records)}")
    for i, record in enumerate(refund_records, 1):
        print(f"\n退款记录 {i}:")
        print(f"  金额: {record.get('amount')}")
        print(f"  交易时间: {record.get('transaction_time')}")
        print(f"  交易类型: {record.get('transaction_type')}")
        print(f"  备注: {record.get('remark')}")

if __name__ == "__main__":
    test_full_import()