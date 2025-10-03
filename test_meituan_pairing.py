#!/usr/bin/env python3
"""
测试美团账单支付退款配对功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.parsers.meituan_parser import MeituanParser
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_meituan_pairing():
    """测试美团账单支付退款配对功能"""
    
    # 美团账单文件路径
    file_path = "/Users/chenxing/projects/my-bills-2/bills/美团账单(20250101-20250401).csv"
    
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return
    
    # 创建解析器
    parser = MeituanParser()
    
    # 解析文件
    logger.info("开始解析美团账单文件...")
    result = parser.parse_file(file_path)
    
    logger.info(f"解析结果:")
    logger.info(f"  成功记录数: {len(result.success_records)}")
    logger.info(f"  失败记录数: {len(result.failed_records)}")
    
    if result.failed_records:
        logger.warning("失败记录:")
        for i, (record, error) in enumerate(result.failed_records):
            logger.warning(f"  {i+1}. 错误: {error}")
    
    # 分析成功记录
        if result.success_records:
            logger.info("\n=== 账单记录分析 ===")
            
            payment_count = 0
            refund_count = 0
            transfer_count = 0
            
            paired_records = []
            
            # 先分析原始数据中的交易类型
            logger.info("\n=== 原始交易类型分析 ===")
            for record in result.success_records:
                transaction_type = record.get('transaction_type', '')
                transaction_desc = record.get('transaction_desc', '')
                amount = record.get('amount', '')
                remark = record.get('remark', '')
                
                # 从原始数据中获取交易类型
                raw_data = record.get('raw_data', {})
                original_category = raw_data.get('transaction_category', '')
                original_income_expense = raw_data.get('income_expense', '')
                
                logger.info(f"记录: {transaction_desc}")
                logger.info(f"  原始交易类型: {original_category}")
                logger.info(f"  原始收支类型: {original_income_expense}")
                logger.info(f"  解析后类型: {transaction_type}")
                logger.info(f"  金额: {amount}")
                logger.info(f"  备注: {remark}")
                logger.info("---")
                
                if transaction_type == 'expense':
                    payment_count += 1
                elif transaction_type == 'income':
                    refund_count += 1
                elif transaction_type == 'transfer':
                    transfer_count += 1
                    paired_records.append(record)
                    
                if '[已配对]' in str(remark):
                    logger.info(f"  -> 配对信息: {remark}")
        
        logger.info(f"\n=== 统计结果 ===")
        logger.info(f"支出记录: {payment_count} 笔")
        logger.info(f"收入记录: {refund_count} 笔") 
        logger.info(f"不计收支记录: {transfer_count} 笔")
        
        if paired_records:
            logger.info(f"\n=== 配对记录详情 ===")
            for record in paired_records:
                logger.info(f"订单: {record.get('transaction_desc')} | 金额: {record.get('amount')} | 备注: {record.get('remark')}")
        
        # 验证配对逻辑
        logger.info(f"\n=== 配对逻辑验证 ===")
        
        # 从CSV文件中我们可以看到应该有3对配对记录：
        # 1. 乌托邦桌球俱乐部 ¥19.90 (支付) + 乌托邦桌球俱乐部 ¥19.90 (退款) - 招商银行信用卡
        # 2. 乌托邦桌球俱乐部 ¥19.90 (支付) + 乌托邦桌球俱乐部 ¥19.90 (退款) - 支付宝支付  
        # 3. 乌托邦桌球俱乐部 ¥59.80 (支付) + 乌托邦桌球俱乐部 ¥59.80 (退款) - 支付宝支付
        
        expected_pairs = 3
        actual_pairs = transfer_count // 2  # 每对包含2条记录
        
        if actual_pairs == expected_pairs:
            logger.info(f"✅ 配对逻辑正确: 预期 {expected_pairs} 对，实际 {actual_pairs} 对")
        else:
            logger.error(f"❌ 配对逻辑错误: 预期 {expected_pairs} 对，实际 {actual_pairs} 对")
            
        # 验证原始统计数据
        logger.info(f"\n=== 原始数据对比 ===")
        logger.info("原始CSV统计: 支出10笔, 收入3笔, 不计收支0笔")
        logger.info(f"解析后统计: 支出{payment_count}笔, 收入{refund_count}笔, 不计收支{transfer_count}笔")
        
        # 预期结果：支出应该减少3笔，收入应该减少3笔，不计收支应该增加6笔
        expected_payment = 10 - 3  # 7笔
        expected_refund = 3 - 3    # 0笔  
        expected_transfer = 0 + 6  # 6笔
        
        if (payment_count == expected_payment and 
            refund_count == expected_refund and 
            transfer_count == expected_transfer):
            logger.info("✅ 配对结果符合预期")
        else:
            logger.error("❌ 配对结果不符合预期")
            logger.error(f"预期: 支出{expected_payment}笔, 收入{expected_refund}笔, 不计收支{expected_transfer}笔")

if __name__ == "__main__":
    test_meituan_pairing()