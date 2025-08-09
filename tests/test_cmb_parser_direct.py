#!/usr/bin/env python3
"""
直接测试CMB解析器的脚本
验证清理硬编码分类逻辑后的解析器功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from parsers.cmb_parser import CMBParser

def test_cmb_parser_direct():
    """直接测试CMB解析器"""
    print("🧪 直接测试CMB解析器...")
    
    # 模拟CMB PDF提取后的文本内容
    cmb_content = """2024-01-15
CNY
-500.00
10000.00
超市购物
沃尔玛超市

2024-01-16
CNY
+3000.00
13000.00
工资收入
公司转账

2024-01-17
CNY
-200.00
12800.00
餐饮消费
麦当劳

2024-01-18
CNY
-1000.00
11800.00
房租支出
房东转账

2024-01-19
CNY
+100.00
11900.00
退款
淘宝退款"""
    
    # 创建解析器实例
    parser = CMBParser()
    
    # 解析内容
    print("📄 解析CMB账单内容...")
    result = parser.parse_content(cmb_content)
    
    print(f"✅ 解析完成:")
    print(f"   - 成功记录: {len(result.success_records)}")
    print(f"   - 失败记录: {len(result.failed_records)}")
    
    # 检查解析结果
    if result.success_records:
        print("\n📊 解析结果详情:")
        for i, record in enumerate(result.success_records, 1):
            print(f"   记录 {i}:")
            print(f"     - 日期: {record.get('transaction_time')}")
            print(f"     - 金额: {record.get('amount')}")
            print(f"     - 类型: {record.get('transaction_type')}")
            print(f"     - 描述: {record.get('transaction_desc')}")
            print(f"     - 分类: {record.get('category', '未设置')}")
            print(f"     - 来源: {record.get('source_type')}")
            print()
    
    # 验证没有硬编码分类
    has_hardcoded_category = any(
        record.get('category') and record.get('category') != '未分类'
        for record in result.success_records
    )
    
    if has_hardcoded_category:
        print("❌ 发现硬编码分类，清理不完整！")
        return False
    else:
        print("✅ 确认没有硬编码分类，清理成功！")
        return True

if __name__ == "__main__":
    success = test_cmb_parser_direct()
    if success:
        print("\n🎉 CMB解析器直接测试通过！")
    else:
        print("\n❌ CMB解析器直接测试失败！")
        sys.exit(1)