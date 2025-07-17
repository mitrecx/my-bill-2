#!/usr/bin/env python3
"""
详细对比CSV文件和解析结果，找出丢失的记录
"""

import sys
import os
sys.path.append('/Users/chenxing/projects/my-bills-2/backend')

from parsers.jd_parser import JDParser
from config.database import get_db
from models.bill import Bill
from sqlalchemy.orm import Session
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.WARNING)  # 减少日志输出
logger = logging.getLogger(__name__)

def analyze_csv_raw(file_path):
    """分析CSV文件原始内容"""
    print(f"分析CSV文件: {file_path}")
    
    # 检测编码
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
    content = None
    used_encoding = None
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                used_encoding = encoding
                break
        except UnicodeDecodeError:
            continue
    
    if not content:
        print("无法读取文件")
        return []
    
    print(f"使用编码: {used_encoding}")
    
    lines = content.strip().split('\n')
    print(f"文件总行数: {len(lines)}")
    
    # 查找数据开始行
    data_start_line = -1
    for i, line in enumerate(lines):
        if '交易时间' in line and '收支情况' in line:
            data_start_line = i
            print(f"找到数据开始行: {i+1}")
            break
    
    if data_start_line == -1:
        print("未找到数据开始行")
        return []
    
    # 统计数据行
    data_lines = lines[data_start_line + 1:]
    valid_data_lines = []
    
    for i, line in enumerate(data_lines):
        line = line.strip()
        if line and not line.startswith('---') and '说明' not in line:
            valid_data_lines.append((i + data_start_line + 2, line))  # 保存行号和内容
    
    print(f"有效数据行数: {len(valid_data_lines)}")
    return valid_data_lines

def compare_with_parser(file_path, csv_lines):
    """对比解析器结果"""
    print("\n" + "="*50)
    print("对比解析器结果")
    print("="*50)
    
    parser = JDParser()
    result = parser.parse_file(file_path)
    
    print(f"CSV有效行数: {len(csv_lines)}")
    print(f"解析成功记录数: {result.success_count}")
    print(f"解析失败记录数: {result.failed_count}")
    print(f"解析总记录数: {result.total_count}")
    
    if len(csv_lines) != result.total_count:
        print(f"⚠️  记录数不匹配！CSV: {len(csv_lines)}, 解析器: {result.total_count}")
        
        # 找出差异
        if len(csv_lines) > result.total_count:
            print(f"CSV文件比解析器多 {len(csv_lines) - result.total_count} 条记录")
            
            # 显示可能被跳过的行
            print("\n可能被跳过的行:")
            for i, (line_num, line_content) in enumerate(csv_lines):
                if i >= result.total_count:
                    print(f"  行 {line_num}: {line_content[:100]}...")
    
    # 检查失败记录
    if result.failed_records:
        print(f"\n解析失败的记录:")
        for i, record in enumerate(result.failed_records):
            print(f"  失败记录 {i+1}: {record}")
    
    return result

def compare_with_database(parsed_records):
    """对比数据库记录"""
    print("\n" + "="*50)
    print("对比数据库记录")
    print("="*50)
    
    db = next(get_db())
    
    try:
        # 查询京东账单
        jd_bills = db.query(Bill).filter(Bill.source_type == 'jd').all()
        print(f"数据库中京东账单数: {len(jd_bills)}")
        print(f"解析成功记录数: {len(parsed_records)}")
        
        if len(jd_bills) != len(parsed_records):
            print(f"⚠️  记录数不匹配！数据库: {len(jd_bills)}, 解析器: {len(parsed_records)}")
            
            # 创建解析记录的索引（用于快速查找）
            parsed_index = {}
            for record in parsed_records:
                key = (
                    record.get('transaction_time'),
                    record.get('amount'),
                    record.get('transaction_desc', '')[:50]  # 只取前50个字符
                )
                parsed_index[key] = record
            
            # 检查数据库记录是否都能在解析记录中找到
            missing_in_db = []
            for record in parsed_records:
                key = (
                    record.get('transaction_time'),
                    record.get('amount'),
                    record.get('transaction_desc', '')[:50]
                )
                
                # 在数据库中查找匹配的记录
                found = False
                for bill in jd_bills:
                    if (bill.transaction_time == record.get('transaction_time') and
                        abs(float(bill.amount) - float(record.get('amount', 0))) < 0.01 and
                        (bill.transaction_desc or '')[:50] == (record.get('transaction_desc', '') or '')[:50]):
                        found = True
                        break
                
                if not found:
                    missing_in_db.append(record)
            
            if missing_in_db:
                print(f"\n在数据库中找不到的解析记录 ({len(missing_in_db)}条):")
                for i, record in enumerate(missing_in_db[:3]):  # 只显示前3条
                    print(f"  缺失记录 {i+1}:")
                    print(f"    时间: {record.get('transaction_time')}")
                    print(f"    金额: {record.get('amount')}")
                    print(f"    描述: {record.get('transaction_desc', '')[:50]}...")
                    print(f"    类型: {record.get('transaction_type')}")
                    print()
    
    finally:
        db.close()

def main():
    file_path = "/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    # 分析CSV文件
    csv_lines = analyze_csv_raw(file_path)
    
    # 对比解析器结果
    parse_result = compare_with_parser(file_path, csv_lines)
    
    # 对比数据库记录
    compare_with_database(parse_result.success_records)

if __name__ == "__main__":
    main()