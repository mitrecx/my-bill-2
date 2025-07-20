#!/usr/bin/env python3
"""
调试京东账单解析问题
"""

import sys
import os
import logging

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.jd_parser import JDParser

# 设置日志级别为DEBUG以查看详细信息
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def debug_jd_parsing():
    """调试京东文件解析"""
    file_path = "/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    print(f"开始解析文件: {file_path}")
    
    # 创建解析器
    parser = JDParser()
    
    # 解析文件
    result = parser.parse_file(file_path)
    
    print(f"\n=== 解析结果摘要 ===")
    summary = result.get_summary()
    print(f"总记录数: {summary['total_count']}")
    print(f"成功记录数: {summary['success_count']}")
    print(f"失败记录数: {summary['failed_count']}")
    print(f"成功率: {summary['success_rate']:.2%}")
    
    if summary['errors']:
        print(f"\n=== 错误信息 ===")
        for i, error in enumerate(summary['errors'][:5], 1):
            print(f"{i}. {error}")
    
    if result.success_records:
        print(f"\n=== 成功记录示例 ===")
        for i, record in enumerate(result.success_records[:3], 1):
            print(f"\n第{i}条成功记录:")
            for key, value in record.items():
                if key != 'raw_data':  # 跳过原始数据
                    print(f"  {key}: {value}")
    
    if result.failed_records:
        print(f"\n=== 失败记录示例 ===")
        for i, record in enumerate(result.failed_records[:3], 1):
            print(f"\n第{i}条失败记录:")
            print(f"  错误: {record.get('parse_error', 'Unknown error')}")
            if 'line_content' in record:
                print(f"  行内容: {record['line_content'][:100]}...")

if __name__ == "__main__":
    debug_jd_parsing()