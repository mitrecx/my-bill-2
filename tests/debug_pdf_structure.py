#!/usr/bin/env python3
"""
详细调试招商银行PDF表格结构的脚本
"""

import pdfplumber
import sys
from pathlib import Path

def debug_pdf_structure():
    """调试PDF的表格结构"""
    test_file = "/Users/chenxing/projects/my-bills-2/bills/招商银行交易流水(申请时间2025年07月05日10时27分05秒).pdf"
    
    print("=== 调试PDF表格结构 ===")
    print(f"文件: {test_file}")
    
    try:
        with pdfplumber.open(test_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                print(f"\n--- 第 {page_num + 1} 页 ---")
                
                # 提取表格
                tables = page.extract_tables()
                
                if tables:
                    for table_num, table in enumerate(tables):
                        print(f"\n表格 {table_num + 1}:")
                        print(f"行数: {len(table)}")
                        
                        # 显示前几行
                        for row_idx, row in enumerate(table[:10]):  # 只显示前10行
                            print(f"  行 {row_idx + 1}: {row}")
                            
                            # 查找表头行
                            if row and any("记账日期" in str(cell) or "Date" in str(cell) for cell in row if cell):
                                print(f"    *** 这是表头行 ***")
                                
                                # 分析表头结构
                                print(f"    表头字段数: {len(row)}")
                                for i, header in enumerate(row):
                                    if header:
                                        print(f"      列 {i}: '{header}'")
                        
                        if len(table) > 10:
                            print(f"  ... (还有 {len(table) - 10} 行)")
                else:
                    print("  没有找到表格")
                
                # 提取文本（前500字符）
                text = page.extract_text()
                if text:
                    print(f"\n文本内容（前500字符）:")
                    print(text[:500])
                    print("...")
    
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

def debug_specific_record():
    """调试具体的问题记录"""
    print("\n=== 调试具体问题记录 ===")
    
    # 添加项目根目录到Python路径
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "backend"))
    
    from backend.parsers.cmb_parser import CMBParser
    
    test_file = "/Users/chenxing/projects/my-bills-2/bills/招商银行交易流水(申请时间2025年07月05日10时27分05秒).pdf"
    
    parser = CMBParser()
    result = parser.parse_file(test_file)
    
    print(f"解析结果: 成功 {len(result.success_records)}, 失败 {len(result.failed_records)}")
    
    # 查找有问题的记录
    for i, record in enumerate(result.success_records):
        # 检查是否缺少 transaction_time
        if "transaction_time" not in record or record["transaction_time"] is None:
            print(f"\n问题记录 {i+1}:")
            for key, value in record.items():
                print(f"  {key}: {value}")
            
            # 检查 raw_data
            if "raw_data" in record:
                print(f"  raw_data:")
                for key, value in record["raw_data"].items():
                    print(f"    {key}: {value}")
            break

if __name__ == "__main__":
    debug_pdf_structure()
    debug_specific_record()