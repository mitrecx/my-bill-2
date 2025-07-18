#!/usr/bin/env python3
"""
测试具体的问题行解析
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from backend.parsers.cmb_parser import CMBParser

def test_problematic_line():
    """测试有问题的行"""
    
    # 从调试输出中看到的问题行
    # 这行包含了时间 10:27:05，但被错误解析为金额
    test_lines = [
        "2025-07-05 CNY 10:27:05 验证码：6K2PPET4",  # 模拟问题行
        "2025-01-03 CNY 300.00 328.96 银联渠道转入 陈兴",  # 正常行
        "2025-03-14 CNY -1,743.51 15,854.31 银联快捷支付 京东肯特瑞基金销售有限公司",  # 正常行
    ]
    
    parser = CMBParser()
    
    for i, line in enumerate(test_lines):
        print(f"\n=== 测试行 {i+1} ===")
        print(f"原始行: {line}")
        
        # 测试 _parse_text_line 方法
        raw_record = parser._parse_text_line(line)
        print(f"解析结果: {raw_record}")
        
        if raw_record:
            # 测试 _process_cmb_fields 方法
            processed = parser._process_cmb_fields(raw_record)
            print(f"处理后: {processed}")
            
            # 测试标准化
            standardized = parser.standardize_record(processed)
            print(f"标准化: {standardized}")
        
        print("-" * 50)

def analyze_pdf_text():
    """分析PDF文本中的问题行"""
    import pdfplumber
    
    test_file = "/Users/chenxing/projects/my-bills-2/bills/招商银行交易流水(申请时间2025年07月05日10时27分05秒).pdf"
    
    print("\n=== 分析PDF文本中的问题行 ===")
    
    with pdfplumber.open(test_file) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                
                # 查找包含时间格式的行
                for line_num, line in enumerate(lines):
                    if "10:27:05" in line or "验证码" in line:
                        print(f"第{page_num+1}页，第{line_num+1}行: {line}")
                        
                        # 分析这行的结构
                        parts = line.strip().split()
                        print(f"  分割后: {parts}")

if __name__ == "__main__":
    test_problematic_line()
    analyze_pdf_text()