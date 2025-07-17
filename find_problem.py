#!/usr/bin/env python3
"""详细检查CSV文件中的问题记录"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.jd_parser import JDParser

def find_problem_record():
    """查找包含问题金额的记录"""
    csv_file = "/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"
    
    if not os.path.exists(csv_file):
        print(f"CSV文件不存在: {csv_file}")
        return
    
    parser = JDParser()
    
    # 直接读取CSV文件内容
    with open(csv_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"CSV文件总行数: {len(lines)}")
    
    # 查找包含问题金额的行
    problem_lines = []
    for i, line in enumerate(lines, 1):
        if "577.61" in line:
            problem_lines.append((i, line.strip()))
    
    print(f"\n包含577.61的行数: {len(problem_lines)}")
    for line_num, line_content in problem_lines:
        print(f"第{line_num}行: {line_content}")
    
    # 解析文件
    result = parser.parse_file(csv_file)
    print(f"\n解析结果:")
    print(f"总记录数: {result.total_count}")
    print(f"成功解析: {result.success_count}")
    print(f"失败记录: {result.failed_count}")
    
    # 检查所有成功记录中是否有包含577.61的
    found_records = []
    for record in result.success_records:
        # 检查所有字段
        record_str = str(record)
        if "577.61" in record_str or "304.13" in record_str:
            found_records.append(record)
    
    print(f"\n找到相关记录: {len(found_records)} 条")
    for i, record in enumerate(found_records, 1):
        print(f"\n记录 {i}:")
        print(f"  金额: {record.get('amount')}")
        print(f"  交易时间: {record.get('transaction_time')}")
        print(f"  交易描述: {record.get('transaction_desc')}")
        print(f"  备注: {record.get('remark')}")
        print(f"  原始数据: {record.get('raw_data', {}).get('amount', '无')}")

if __name__ == "__main__":
    find_problem_record()