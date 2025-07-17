#!/usr/bin/env python3
"""
查找并分析有问题的金额记录
"""

import sys
import os
sys.path.append('/Users/chenxing/projects/my-bills-2/backend')

def find_problematic_amount(file_path):
    """查找有问题的金额记录"""
    print(f"查找文件中的问题金额: {file_path}")
    
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
    
    # 查找数据开始行
    data_start_line = -1
    for i, line in enumerate(lines):
        if '交易时间' in line and '收支情况' in line:
            data_start_line = i
            print(f"找到数据开始行: {i+1}")
            print(f"表头: {line}")
            break
    
    if data_start_line == -1:
        print("未找到数据开始行")
        return
    
    # 分析表头
    header_line = lines[data_start_line]
    # 处理混合分隔符
    if '\t' in header_line and ',' in header_line:
        # 先按制表符分割，再处理逗号
        parts = header_line.split('\t')
        headers = []
        for part in parts:
            if ',' in part:
                headers.extend(part.split(','))
            else:
                headers.append(part)
    else:
        headers = header_line.replace('\t', ',').split(',')
    
    headers = [h.strip().strip('"') for h in headers if h.strip()]
    print(f"表头字段: {headers}")
    
    # 查找金额字段的索引
    amount_index = -1
    for i, header in enumerate(headers):
        if '金额' in header:
            amount_index = i
            print(f"金额字段索引: {i} ({header})")
            break
    
    if amount_index == -1:
        print("未找到金额字段")
        return
    
    # 查找包含问题金额的行
    problem_amounts = []
    data_lines = lines[data_start_line + 1:]
    
    for line_num, line in enumerate(data_lines, start=data_start_line + 2):
        line = line.strip()
        if not line or line.startswith('---') or '说明' in line:
            continue
        
        # 处理混合分隔符
        if '\t' in line and ',' in line:
            parts = line.split('\t')
            fields = []
            for part in parts:
                if ',' in part:
                    fields.extend(part.split(','))
                else:
                    fields.append(part)
        else:
            fields = line.replace('\t', ',').split(',')
        
        fields = [f.strip().strip('"') for f in fields]
        
        if len(fields) > amount_index:
            amount_str = fields[amount_index]
            
            # 检查是否包含问题金额
            if '577.61273.48' in amount_str:
                problem_amounts.append({
                    'line_num': line_num,
                    'amount_str': amount_str,
                    'full_line': line,
                    'fields': fields
                })
                print(f"\n找到问题行 {line_num}:")
                print(f"  原始行: {line}")
                print(f"  金额字段: '{amount_str}'")
                print(f"  所有字段: {fields}")
    
    if not problem_amounts:
        print("未找到包含 '577.61273.48' 的记录")
        
        # 查找其他可能有问题的金额
        print("\n查找其他可能有问题的金额...")
        for line_num, line in enumerate(data_lines[:10], start=data_start_line + 2):
            line = line.strip()
            if not line or line.startswith('---') or '说明' in line:
                continue
            
            # 处理混合分隔符
            if '\t' in line and ',' in line:
                parts = line.split('\t')
                fields = []
                for part in parts:
                    if ',' in part:
                        fields.extend(part.split(','))
                    else:
                        fields.append(part)
            else:
                fields = line.replace('\t', ',').split(',')
            
            fields = [f.strip().strip('"') for f in fields]
            
            if len(fields) > amount_index:
                amount_str = fields[amount_index]
                print(f"行 {line_num} 金额: '{amount_str}'")

def main():
    file_path = "/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    find_problematic_amount(file_path)

if __name__ == "__main__":
    main()