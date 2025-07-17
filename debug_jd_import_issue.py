#!/usr/bin/env python3
"""
分析京东账单导入问题的调试脚本
"""

import os
import sys
import chardet
import csv
from pathlib import Path

def analyze_file(file_path):
    """分析文件内容"""
    print(f"=== 分析文件: {file_path} ===")
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    # 检测文件编码
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        encoding_result = chardet.detect(raw_data)
        print(f"检测到的编码: {encoding_result}")
    
    # 尝试用不同编码读取文件
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
    
    for encoding in encodings:
        try:
            print(f"\n--- 尝试编码: {encoding} ---")
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            
            print(f"总行数: {len(lines)}")
            
            # 查找表头行
            header_line_num = None
            for i, line in enumerate(lines):
                if "交易时间" in line or "记录时间" in line:
                    header_line_num = i
                    print(f"找到表头行 (第{i+1}行): {line.strip()}")
                    break
            
            if header_line_num is not None:
                # 统计数据行
                data_lines = 0
                for i in range(header_line_num + 1, len(lines)):
                    line = lines[i].strip()
                    if line and not line.startswith('#') and ',' in line:
                        data_lines += 1
                
                print(f"数据行数: {data_lines}")
                
                # 显示前几行数据
                print("\n前5行数据:")
                for i in range(header_line_num + 1, min(header_line_num + 6, len(lines))):
                    line = lines[i].strip()
                    if line:
                        print(f"第{i+1}行: {line[:100]}...")
                
                # 显示最后几行数据
                print("\n最后5行数据:")
                for i in range(max(len(lines) - 5, header_line_num + 1), len(lines)):
                    line = lines[i].strip()
                    if line:
                        print(f"第{i+1}行: {line[:100]}...")
                
                break
            else:
                print("未找到表头行")
                # 显示前10行内容
                print("前10行内容:")
                for i, line in enumerate(lines[:10]):
                    print(f"第{i+1}行: {line.strip()[:100]}")
                
        except Exception as e:
            print(f"编码 {encoding} 读取失败: {e}")
            continue

def check_jd_bills_in_db():
    """检查数据库中的京东账单"""
    print("\n=== 检查数据库中的京东账单 ===")
    
    try:
        import psycopg2
        conn = psycopg2.connect("postgresql://josie:bills_password_2024@localhost:5432/bills_db")
        cur = conn.cursor()
        
        # 统计京东账单
        cur.execute("SELECT COUNT(*) FROM bills WHERE source_type = 'jd'")
        total_jd = cur.fetchone()[0]
        print(f"数据库中京东账单总数: {total_jd}")
        
        # 按文件名统计
        cur.execute("""
            SELECT source_filename, COUNT(*) 
            FROM bills 
            WHERE source_type = 'jd' 
            GROUP BY source_filename
        """)
        
        files = cur.fetchall()
        print("按文件名统计:")
        for filename, count in files:
            print(f"  {filename}: {count}条")
        
        # 查看最近的几条记录
        cur.execute("""
            SELECT id, order_id, transaction_time, amount, transaction_desc 
            FROM bills 
            WHERE source_type = 'jd' 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        recent_bills = cur.fetchall()
        print("\n最近的5条京东账单:")
        for bill in recent_bills:
            print(f"  ID: {bill[0]}, Order: {bill[1]}, Time: {bill[2]}, Amount: {bill[3]}, Desc: {bill[4]}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"数据库查询失败: {e}")

def main():
    # 查找可能的京东账单文件
    possible_files = [
        "/Users/chenxing/projects/my-bills-2/bills/cashbook_record_20250705_095457.csv",
    ]
    
    # 查找其他可能的文件
    bills_dir = Path("/Users/chenxing/projects/my-bills-2/bills")
    if bills_dir.exists():
        for file in bills_dir.glob("*.csv"):
            if str(file) not in possible_files:
                possible_files.append(str(file))
    
    # 分析每个文件
    for file_path in possible_files:
        if os.path.exists(file_path):
            analyze_file(file_path)
            print("\n" + "="*80 + "\n")
    
    # 检查数据库
    check_jd_bills_in_db()

if __name__ == "__main__":
    main()