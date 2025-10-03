#!/usr/bin/env python3
"""
测试美团账单解析器的transaction_type字段修复
验证是否正确使用中文类型："收入"、"支出"、"不计收支"
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from parsers.meituan_parser import MeituanParser
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_meituan_transaction_types():
    """测试美团账单transaction_type字段"""
    
    # 初始化解析器
    parser = MeituanParser()
    
    # 解析美团账单文件
    file_path = "/Users/chenxing/projects/my-bills-2/bills/美团账单(20250101-20250401).csv"
    
    try:
        result = parser.parse_file(file_path)
        
        logger.info(f"解析结果: 成功 {len(result.success_records)} 条，失败 {len(result.failed_records)} 条")
        
        # 统计transaction_type字段的值
        type_counts = {}
        paired_records = []
        
        for record in result.success_records:
            transaction_type = record.get('transaction_type', '')
            transaction_desc = record.get('transaction_desc', '')
            amount = record.get('amount', '')
            remark = record.get('remark', '')
            
            # 统计类型
            if transaction_type in type_counts:
                type_counts[transaction_type] += 1
            else:
                type_counts[transaction_type] = 1
            
            # 记录详细信息
            logger.info(f"记录: {transaction_desc}")
            logger.info(f"  transaction_type: {transaction_type}")
            logger.info(f"  金额: {amount}")
            logger.info(f"  备注: {remark}")
            
            if transaction_type == '不计收支':
                paired_records.append(record)
            
            logger.info("---")
        
        logger.info(f"\n=== transaction_type 统计 ===")
        for type_name, count in type_counts.items():
            logger.info(f"{type_name}: {count} 条")
        
        logger.info(f"\n=== 验证结果 ===")
        valid_types = {'收入', '支出', '不计收支'}
        invalid_types = set(type_counts.keys()) - valid_types
        
        if invalid_types:
            logger.error(f"❌ 发现无效的transaction_type值: {invalid_types}")
            return False
        else:
            logger.info(f"✅ 所有transaction_type值都是有效的中文类型")
            logger.info(f"✅ 配对记录数量: {len(paired_records)} 条")
            return True
            
    except Exception as e:
        logger.error(f"解析失败: {e}")
        return False

if __name__ == "__main__":
    success = test_meituan_transaction_types()
    sys.exit(0 if success else 1)