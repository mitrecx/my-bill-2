#!/usr/bin/env python3
"""
测试修复后的CMB解析器
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from backend.parsers.cmb_parser import CMBParser

def test_fixed_parser():
    """测试修复后的解析器"""
    
    test_file = "/Users/chenxing/projects/my-bills-2/bills/招商银行交易流水(申请时间2025年07月05日10时27分05秒).pdf"
    
    print("=== 测试修复后的CMB解析器 ===")
    print(f"文件: {test_file}")
    
    parser = CMBParser()
    result = parser.parse_file(test_file)
    
    print(f"\n解析结果:")
    print(f"  成功记录: {len(result.success_records)}")
    print(f"  失败记录: {len(result.failed_records)}")
    
    # 检查是否还有问题记录
    problem_found = False
    for i, record in enumerate(result.success_records):
        # 检查是否缺少 transaction_time
        if "transaction_time" not in record or record["transaction_time"] is None:
            print(f"\n❌ 仍有问题记录 {i+1}:")
            for key, value in record.items():
                print(f"  {key}: {value}")
            problem_found = True
            break
        
        # 检查金额是否为时间格式
        amount = record.get("amount")
        if amount and str(amount).count(':') >= 2:  # 时间格式 HH:MM:SS
            print(f"\n❌ 金额格式错误记录 {i+1}:")
            for key, value in record.items():
                print(f"  {key}: {value}")
            problem_found = True
            break
    
    if not problem_found:
        print("\n✅ 所有记录都正常！")
        
        # 显示前3条记录作为示例
        print("\n前3条记录示例:")
        for i, record in enumerate(result.success_records[:3]):
            print(f"\n记录 {i+1}:")
            print(f"  时间: {record.get('transaction_time')}")
            print(f"  金额: {record.get('amount')}")
            print(f"  货币: {record.get('currency')}")
            print(f"  描述: {record.get('transaction_desc')}")
            print(f"  对手方: {record.get('counter_party')}")
    
    # 显示失败记录
    if result.failed_records:
        print(f"\n失败记录:")
        for i, (record, error) in enumerate(result.failed_records):
            print(f"  失败 {i+1}: {error}")
            print(f"    数据: {record}")

def test_line_filtering():
    """测试行过滤功能"""
    
    print("\n=== 测试行过滤功能 ===")
    
    test_lines = [
        "申请时间：2025-07-05 10:27:05 验证码：6K2PPET4",  # 应该被过滤
        "2025-01-03 CNY 300.00 328.96 银联渠道转入 陈兴",  # 应该保留
        "记账日期 货币 交易金额 联机余额 交易摘要 对手信息",  # 应该被过滤
        "2025-03-14 CNY -1,743.51 15,854.31 银联快捷支付 京东",  # 应该保留
        "招商银行股份有限公司",  # 应该被过滤
    ]
    
    parser = CMBParser()
    
    for line in test_lines:
        is_transaction = parser._is_transaction_line(line)
        status = "✅ 保留" if is_transaction else "❌ 过滤"
        print(f"{status}: {line}")

if __name__ == "__main__":
    test_line_filtering()
    test_fixed_parser()