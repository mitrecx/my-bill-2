#!/usr/bin/env python3
"""
京东账单上传过程调试脚本
模拟完整的上传过程，找出数据丢失的原因
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
import tempfile

# 添加backend路径到sys.path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from parsers.jd_parser import JDParser
from api.upload import find_existing_jd_bill, check_duplicate_bill_other_sources

# 设置日志级别为DEBUG以查看详细信息
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_upload_process(file_path, family_id=1):
    """模拟完整的上传过程"""
    print(f"\n{'='*60}")
    print(f"模拟京东账单上传过程: {file_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        return
    
    # 步骤1: 解析文件
    print(f"\n步骤1: 解析文件")
    parser = JDParser()
    parse_result = parser.parse_file(file_path)
    
    print(f"- 解析成功记录数: {len(parse_result.success_records)}")
    print(f"- 解析失败记录数: {len(parse_result.failed_records)}")
    
    if parse_result.failed_records:
        print(f"解析失败的记录:")
        for i, failed in enumerate(parse_result.failed_records):
            print(f"  {i+1}: {failed}")
    
    # 步骤1.5: 检查standardize_record过程
    print(f"\n步骤1.5: 检查记录标准化过程")
    
    # 重新解析文件，但这次检查每个记录的标准化过程
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 手动解析内容，检查标准化过程
    lines = content.strip().split('\n')
    
    # 找到表头行
    header_line = None
    data_start_index = 0
    
    for i, line in enumerate(lines):
        if "交易时间" in line and "商户名称" in line and "金额" in line:
            header_line = line
            data_start_index = i + 1
            break
    
    if header_line:
        # 解析表头
        if '\t' in header_line:
            first_tab_pos = header_line.find('\t')
            first_header = header_line[:first_tab_pos].strip()
            remaining_headers = header_line[first_tab_pos:].lstrip('\t,')
            headers = [first_header] + [h.strip() for h in remaining_headers.split(',') if h.strip()]
        else:
            headers = [h.strip() for h in header_line.split(',') if h.strip()]
        
        standardize_failed_count = 0
        
        # 处理数据行，检查标准化过程
        for line_num, line in enumerate(lines[data_start_index:], start=data_start_index + 1):
            if not line.strip():
                continue
            
            try:
                # 解析这一行（简化版本）
                first_tab_pos = line.find('\t')
                if first_tab_pos == -1:
                    continue
                
                transaction_time = line[:first_tab_pos].strip()
                remaining = line[first_tab_pos:].lstrip('\t,')
                parts = remaining.split(',')
                
                cleaned_parts = [transaction_time]
                for part in parts:
                    cleaned = part.replace('\t', '').strip()
                    cleaned = ' '.join(cleaned.split())
                    cleaned_parts.append(cleaned)
                
                while cleaned_parts and not cleaned_parts[-1]:
                    cleaned_parts.pop()
                
                if len(cleaned_parts) < len(headers):
                    cleaned_parts.extend([''] * (len(headers) - len(cleaned_parts)))
                elif len(cleaned_parts) > len(headers):
                    cleaned_parts = cleaned_parts[:len(headers)]
                
                raw_record = dict(zip(headers, cleaned_parts))
                
                # 映射字段名
                field_mapping = {
                    "交易时间": "transaction_time",
                    "商户名称": "merchant_name",
                    "交易说明": "transaction_desc",
                    "金额": "amount",
                    "收/付款方式": "payment_method",
                    "交易状态": "transaction_status",
                    "收/支": "income_expense",
                    "交易分类": "category",
                    "交易订单号": "order_id",
                    "商家订单号": "merchant_order_id",
                    "备注": "remark"
                }
                
                mapped_record = {}
                for original_field, standard_field in field_mapping.items():
                    if original_field in raw_record:
                        mapped_record[standard_field] = raw_record[original_field]
                
                # 处理京东特有字段
                processed_record = mapped_record.copy()
                
                # 处理收支情况
                income_expense = mapped_record.get("income_expense", "")
                if income_expense:
                    if "收入" in income_expense:
                        processed_record["transaction_type"] = "收入"
                    elif "支出" in income_expense:
                        processed_record["transaction_type"] = "支出"
                    elif "不计收支" in income_expense:
                        processed_record["transaction_type"] = "不计收支"
                
                # 处理金额
                amount_str = str(mapped_record.get("amount", ""))
                if amount_str:
                    processed_record["amount"] = amount_str
                
                # 处理交易描述
                desc_parts = []
                if mapped_record.get("merchant_name"):
                    desc_parts.append(str(mapped_record["merchant_name"]))
                if mapped_record.get("transaction_desc"):
                    desc_parts.append(str(mapped_record["transaction_desc"]))
                    
                if desc_parts:
                    processed_record["transaction_desc"] = " - ".join(desc_parts)
                
                processed_record["raw_data"] = raw_record
                
                # 尝试标准化记录
                standardized = parser.standardize_record(processed_record)
                
                if standardized is None:
                    standardize_failed_count += 1
                    print(f"  ❌ 第{line_num}行标准化失败:")
                    print(f"     原始记录: {raw_record}")
                    print(f"     处理后记录: {processed_record}")
                    
                    # 检查具体哪个字段导致失败
                    test_fields = {
                        "transaction_time": parser._parse_datetime(processed_record.get("transaction_time")),
                        "amount": parser._parse_amount(processed_record.get("amount")),
                        "transaction_type": processed_record.get("transaction_type")
                    }
                    
                    for field, value in test_fields.items():
                        if value is None:
                            print(f"       失败字段: {field} = {processed_record.get(field)}")
                
            except Exception as e:
                print(f"  ❌ 第{line_num}行处理异常: {e}")
        
        print(f"标准化失败记录数: {standardize_failed_count}")
    
    # 步骤2: 模拟上传过程中的验证
    print(f"\n步骤2: 模拟上传验证过程")
    
    success_count = 0
    failed_count = 0
    updated_count = 0
    batch_records = set()
    
    # 模拟必需字段检查
    required_fields = ["amount", "transaction_time", "transaction_type"]
    
    for i, record in enumerate(parse_result.success_records):
        print(f"\n处理记录 {i+1}/{len(parse_result.success_records)}")
        
        # 检查必需字段
        missing_fields = [field for field in required_fields if field not in record or record[field] is None]
        
        if missing_fields:
            print(f"  ❌ 缺少必需字段: {missing_fields}")
            failed_count += 1
            continue
        
        # 批次内去重检查（京东账单也会进行批次内去重）
        record_key = (
            record["transaction_time"].isoformat() if hasattr(record["transaction_time"], 'isoformat') else str(record["transaction_time"]),
            str(record["amount"]),
            record.get("transaction_desc", "")
        )
        
        if record_key in batch_records:
            print(f"  ❌ 批次内重复记录: {record_key}")
            continue
        
        batch_records.add(record_key)
        
        # 模拟京东账单的重复检查（这里我们假设没有数据库，所以不会找到重复）
        # 在实际情况下，这里会调用 find_existing_jd_bill
        
        print(f"  ✅ 记录验证通过")
        print(f"     - 交易时间: {record.get('transaction_time')}")
        print(f"     - 金额: {record.get('amount')}")
        print(f"     - 交易描述: {record.get('transaction_desc', '')[:50]}")
        print(f"     - 订单号: {record.get('raw_data', {}).get('order_id', 'N/A')}")
        
        success_count += 1
    
    print(f"\n验证结果统计:")
    print(f"- 成功验证记录数: {success_count}")
    print(f"- 验证失败记录数: {failed_count}")
    print(f"- 批次内去重数量: {len(parse_result.success_records) - success_count - failed_count}")
    
    # 步骤3: 分析可能的数据丢失原因
    print(f"\n步骤3: 数据丢失原因分析")
    
    if success_count < len(parse_result.success_records):
        lost_count = len(parse_result.success_records) - success_count
        print(f"❌ 发现数据丢失: {lost_count} 条记录")
        
        # 分析丢失的原因
        if failed_count > 0:
            print(f"  - 必需字段缺失导致丢失: {failed_count} 条")
        
        batch_dedup_lost = len(parse_result.success_records) - success_count - failed_count
        if batch_dedup_lost > 0:
            print(f"  - 批次内去重导致丢失: {batch_dedup_lost} 条")
    else:
        print(f"✅ 没有数据丢失")
    
    # 步骤4: 分析重复记录
    print(f"\n步骤4: 重复记录分析")
    
    # 统计相同的记录键
    record_keys = {}
    for i, record in enumerate(parse_result.success_records):
        record_key = (
            record["transaction_time"].isoformat() if hasattr(record["transaction_time"], 'isoformat') else str(record["transaction_time"]),
            str(record["amount"]),
            record.get("transaction_desc", "")
        )
        
        if record_key not in record_keys:
            record_keys[record_key] = []
        record_keys[record_key].append(i+1)
    
    # 找出重复的记录
    duplicate_keys = {k: v for k, v in record_keys.items() if len(v) > 1}
    
    if duplicate_keys:
        print(f"发现 {len(duplicate_keys)} 组重复记录:")
        for key, indices in duplicate_keys.items():
            print(f"  重复组: {key}")
            print(f"    记录索引: {indices}")
            print(f"    重复次数: {len(indices)}")
    else:
        print(f"没有发现重复记录")
    
    return {
        'parsed_count': len(parse_result.success_records),
        'success_count': success_count,
        'failed_count': failed_count,
        'duplicate_groups': len(duplicate_keys) if duplicate_keys else 0
    }

def find_jd_files():
    """查找京东账单文件"""
    possible_paths = [
        "/Users/chenxing/projects/my-bills-2/test_data",
        "/Users/chenxing/projects/my-bills-2/backend/test_data",
        "/Users/chenxing/Downloads",
        "/Users/chenxing/Desktop"
    ]
    
    jd_files = []
    for path in possible_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith('.csv') and ('京东' in file or 'jd' in file.lower() or '账单' in file):
                    jd_files.append(os.path.join(path, file))
    
    return jd_files

def main():
    print("京东账单上传过程调试工具")
    print("="*60)
    
    # 查找京东账单文件
    jd_files = find_jd_files()
    
    if not jd_files:
        print("未找到京东账单文件")
        return
    
    print(f"找到 {len(jd_files)} 个可能的京东账单文件:")
    for i, file_path in enumerate(jd_files):
        print(f"{i+1}. {file_path}")
    
    # 分析每个文件
    for file_path in jd_files:
        try:
            result = simulate_upload_process(file_path)
            
            print(f"\n总结:")
            print(f"- 解析记录数: {result['parsed_count']}")
            print(f"- 验证成功数: {result['success_count']}")
            print(f"- 验证失败数: {result['failed_count']}")
            print(f"- 重复记录组: {result['duplicate_groups']}")
            
            if result['success_count'] != result['parsed_count']:
                print(f"⚠️  数据丢失: {result['parsed_count'] - result['success_count']} 条")
            else:
                print(f"✅ 没有数据丢失")
                
        except Exception as e:
            print(f"分析文件 {file_path} 时出错: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()