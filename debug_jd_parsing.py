#!/usr/bin/env python3
"""
京东账单解析详细调试脚本
分析解析过程中的数据丢失问题
"""

import os
import sys
sys.path.append('/Users/chenxing/projects/my-bills-2/backend')

from parsers.jd_parser import JDParser
from config.database import get_db
from models.bill import Bill
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def analyze_jd_parsing():
    """分析京东账单解析过程"""
    csv_file = "/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"
    
    if not os.path.exists(csv_file):
        print(f"文件不存在: {csv_file}")
        return
    
    print("="*60)
    print("京东账单解析详细分析")
    print("="*60)
    
    # 1. 检查文件基本信息
    print(f"\n1. 文件基本信息:")
    print(f"   文件路径: {csv_file}")
    
    # 检测编码
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
    content = None
    used_encoding = None
    
    for encoding in encodings:
        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                content = f.read()
                used_encoding = encoding
                break
        except UnicodeDecodeError:
            continue
    
    if not content:
        print("   ❌ 无法读取文件")
        return
    
    print(f"   文件编码: {used_encoding}")
    
    # 统计行数
    lines = content.strip().split('\n')
    print(f"   总行数: {len(lines)}")
    
    # 2. 查找表头行
    print(f"\n2. 表头分析:")
    header_line = None
    data_start_index = 0
    
    for i, line in enumerate(lines):
        if "交易时间" in line and "商户名称" in line and "金额" in line:
            header_line = line
            data_start_index = i + 1
            print(f"   表头行位置: 第{i+1}行")
            print(f"   表头内容: {line[:100]}...")
            break
    
    if not header_line:
        print("   ❌ 未找到表头行")
        return
    
    # 3. 分析数据行
    data_lines = lines[data_start_index:]
    print(f"\n3. 数据行分析:")
    print(f"   数据行数: {len(data_lines)}")
    
    # 过滤空行
    non_empty_lines = [line for line in data_lines if line.strip()]
    print(f"   非空数据行数: {len(non_empty_lines)}")
    
    # 4. 使用解析器解析
    print(f"\n4. 解析器分析:")
    parser = JDParser()
    result = parser.parse_content(content)
    
    print(f"   解析总记录数: {result.total_count}")
    print(f"   解析成功记录数: {result.success_count}")
    print(f"   解析失败记录数: {result.failed_count}")
    print(f"   成功率: {result.success_count/result.total_count*100:.1f}%" if result.total_count > 0 else "   成功率: 0%")
    
    # 5. 分析失败记录
    if result.failed_records:
        print(f"\n5. 失败记录分析:")
        print(f"   失败记录数: {len(result.failed_records)}")
        
        # 显示前5个失败记录
        for i, failed_record in enumerate(result.failed_records[:5]):
            print(f"\n   失败记录 {i+1}:")
            print(f"     错误: {failed_record.get('parse_error', '未知错误')}")
            print(f"     原始数据: {str(failed_record)[:200]}...")
    
    # 6. 分析错误类型
    if result.errors:
        print(f"\n6. 错误类型统计:")
        error_counts = {}
        for error in result.errors:
            error_type = error.split(':')[0] if ':' in error else error
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        for error_type, count in error_counts.items():
            print(f"   {error_type}: {count}次")
    
    # 7. 分析成功记录的字段完整性
    if result.success_records:
        print(f"\n7. 成功记录字段分析:")
        sample_record = result.success_records[0]
        print(f"   字段数量: {len(sample_record)}")
        print(f"   字段列表: {list(sample_record.keys())}")
        
        # 检查关键字段的完整性
        key_fields = ['transaction_time', 'amount', 'merchant_name', 'order_id']
        for field in key_fields:
            non_null_count = sum(1 for record in result.success_records if record.get(field))
            print(f"   {field}: {non_null_count}/{len(result.success_records)} ({non_null_count/len(result.success_records)*100:.1f}%)")
    
    # 8. 检查数据库中的记录
    print(f"\n8. 数据库记录检查:")
    db = next(get_db())
    try:
        jd_bills = db.query(Bill).filter(Bill.source_type == "jd").all()
        print(f"   数据库中京东账单总数: {len(jd_bills)}")
        
        # 检查是否有重复记录
        order_ids = [bill.order_id for bill in jd_bills if bill.order_id]
        unique_order_ids = set(order_ids)
        print(f"   有order_id的记录数: {len(order_ids)}")
        print(f"   唯一order_id数: {len(unique_order_ids)}")
        if len(order_ids) != len(unique_order_ids):
            print(f"   ⚠️  检测到重复的order_id")
        
    except Exception as e:
        print(f"   ❌ 数据库查询失败: {e}")
    finally:
        db.close()
    
    # 9. 总结
    print(f"\n9. 问题总结:")
    expected_records = len(non_empty_lines)
    actual_records = result.success_count
    missing_records = expected_records - actual_records
    
    print(f"   预期记录数: {expected_records}")
    print(f"   实际解析成功: {actual_records}")
    print(f"   丢失记录数: {missing_records}")
    
    if missing_records > 0:
        print(f"   ❌ 有 {missing_records} 条记录在解析过程中丢失")
        print(f"   主要原因可能是:")
        if result.failed_count > 0:
            print(f"     - 解析失败: {result.failed_count} 条")
        if missing_records > result.failed_count:
            print(f"     - 其他原因: {missing_records - result.failed_count} 条")
    else:
        print(f"   ✅ 所有记录都已成功解析")

if __name__ == "__main__":
    analyze_jd_parsing()