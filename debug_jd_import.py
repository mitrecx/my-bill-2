#!/usr/bin/env python3
"""
调试京东账单导入问题的脚本
分析CSV文件内容和解析过程
"""

import sys
import os
sys.path.append('/Users/chenxing/projects/my-bills-2/backend')

from parsers.jd_parser import JDParser
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def analyze_csv_file(file_path):
    """分析CSV文件内容"""
    print(f"分析文件: {file_path}")
    
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
        return
    
    print(f"使用编码: {used_encoding}")
    
    lines = content.strip().split('\n')
    print(f"文件总行数: {len(lines)}")
    
    # 显示前几行内容
    print("\n前10行内容:")
    for i, line in enumerate(lines[:10]):
        print(f"行 {i+1}: {repr(line)}")
    
    # 查找数据开始行
    data_start_line = -1
    for i, line in enumerate(lines):
        if '交易时间' in line and '收支情况' in line:
            data_start_line = i
            print(f"\n找到数据开始行: {i+1}")
            print(f"表头内容: {repr(line)}")
            break
    
    if data_start_line == -1:
        print("未找到数据开始行")
        return
    
    # 统计数据行
    data_lines = lines[data_start_line + 1:]
    valid_data_lines = []
    
    for i, line in enumerate(data_lines):
        line = line.strip()
        if line and not line.startswith('---') and '说明' not in line:
            valid_data_lines.append(line)
    
    print(f"\n有效数据行数: {len(valid_data_lines)}")
    
    # 显示最后几行数据
    print("\n最后5行有效数据:")
    for i, line in enumerate(valid_data_lines[-5:]):
        print(f"数据行 {len(valid_data_lines)-4+i}: {repr(line)}")
    
    return valid_data_lines

def test_parser(file_path):
    """测试解析器"""
    print("\n" + "="*50)
    print("测试解析器")
    print("="*50)
    
    parser = JDParser()
    result = parser.parse_file(file_path)
    
    print(f"解析结果:")
    print(f"  总记录数: {result.total_count}")
    print(f"  成功记录数: {result.success_count}")
    print(f"  失败记录数: {result.failed_count}")
    print(f"  成功率: {result.success_count / result.total_count * 100:.2f}%" if result.total_count > 0 else "N/A")
    
    if result.errors:
        print(f"\n错误信息:")
        for error in result.errors[:5]:  # 只显示前5个错误
            print(f"  - {error}")
    
    if result.failed_records:
        print(f"\n失败记录示例 (前3个):")
        for i, record in enumerate(result.failed_records[:3]):
            print(f"  失败记录 {i+1}: {record}")
    
    if result.success_records:
        print(f"\n成功记录示例 (前3个):")
        for i, record in enumerate(result.success_records[:3]):
            print(f"  成功记录 {i+1}:")
            for key, value in record.items():
                if key != 'raw_data':  # 跳过原始数据以减少输出
                    print(f"    {key}: {value}")
            print()

def main():
    file_path = "/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    # 分析CSV文件
    valid_lines = analyze_csv_file(file_path)
    
    # 测试解析器
    test_parser(file_path)
    
    print(f"\n总结:")
    print(f"CSV文件有效数据行数: {len(valid_lines) if valid_lines else 0}")

if __name__ == "__main__":
    main()