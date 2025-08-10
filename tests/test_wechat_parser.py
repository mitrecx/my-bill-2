#!/usr/bin/env python3
"""
测试微信账单解析器
"""

import sys
import os
import pandas as pd
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from parsers.wechat_parser import WeChatParser


def create_test_wechat_excel():
    """创建测试用的微信账单Excel文件"""
    # 创建测试数据
    data = {
        '交易时间': [
            '2024-01-15 10:30:00',
            '2024-01-15 12:45:00',
            '2024-01-15 18:20:00',
            '2024-01-16 09:15:00',
            '2024-01-16 14:30:00'
        ],
        '交易类型': [
            '商户消费',
            '商户消费',
            '转账',
            '商户消费',
            '红包'
        ],
        '交易对方': [
            '星巴克咖啡',
            '美团外卖',
            '张三',
            '滴滴出行',
            '李四'
        ],
        '商品': [
            '拿铁咖啡',
            '午餐套餐',
            '转账',
            '快车服务',
            '新年红包'
        ],
        '收/支': [
            '支出',
            '支出',
            '支出',
            '支出',
            '收入'
        ],
        '金额(元)': [
            '¥35.00',
            '¥42.50',
            '¥100.00',
            '¥28.80',
            '¥50.00'
        ],
        '支付方式': [
            '零钱通',
            '招商银行储蓄卡(1234)',
            '零钱',
            '微信支付分',
            '/'
        ],
        '当前状态': [
            '支付成功',
            '支付成功',
            '转账成功',
            '支付成功',
            '已收钱'
        ],
        '交易单号': [
            '1000000000000001',
            '1000000000000002',
            '1000000000000003',
            '1000000000000004',
            '1000000000000005'
        ],
        '商户单号': [
            'SB20240115001',
            'MT20240115001',
            '/',
            'DD20240116001',
            '/'
        ],
        '备注': [
            '/',
            '/',
            '生活费',
            '/',
            '新年快乐'
        ]
    }
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 创建完整的Excel文件，包含微信账单的标准格式
    with pd.ExcelWriter('test_wechat_bills.xlsx', engine='openpyxl') as writer:
        # 添加说明行（模拟微信账单的格式）
        header_data = [
            ['微信支付账单'],
            [''],
            ['起始时间：2024-01-15 00:00:00'],
            ['终止时间：2024-01-16 23:59:59'],
            ['导出时间：2024-01-17 10:00:00'],
            [''],
            ['共5笔交易'],
            [''],
            ['收入：1笔 50.00元'],
            ['支出：4笔 206.30元'],
            [''],
            ['注：'],
            ['1. 本账单仅展示微信支付相关交易'],
            ['2. 如有疑问请联系微信客服'],
            [''],
            ['----------------------交易记录明细列表----------------------']
        ]
        
        # 写入说明行
        header_df = pd.DataFrame(header_data)
        header_df.to_excel(writer, sheet_name='Sheet1', index=False, header=False)
        
        # 写入数据（从第17行开始，索引16）
        df.to_excel(writer, sheet_name='Sheet1', startrow=16, index=False)
    
    print("测试微信账单Excel文件已创建: test_wechat_bills.xlsx")
    return 'test_wechat_bills.xlsx'


def test_wechat_parser():
    """测试微信账单解析器"""
    print("开始测试微信账单解析器...")
    
    # 创建测试文件
    test_file = create_test_wechat_excel()
    
    try:
        # 创建解析器实例
        parser = WeChatParser()
        
        # 解析文件
        result = parser.parse_file(test_file)
        
        print(f"\n解析结果:")
        print(f"成功记录数: {len(result.success_records)}")
        print(f"失败记录数: {len(result.failed_records)}")
        print(f"错误信息: {result.errors}")
        
        # 显示成功解析的记录
        if result.success_records:
            print("\n成功解析的记录:")
            for i, record in enumerate(result.success_records, 1):
                print(f"\n记录 {i}:")
                print(f"  来源类型: {record.get('source_type', 'N/A')}")
                print(f"  交易时间: {record.get('transaction_time', 'N/A')}")
                print(f"  交易描述: {record.get('transaction_desc', 'N/A')}")
                print(f"  金额: {record.get('amount', 'N/A')}")
                print(f"  货币: {record.get('currency', 'N/A')}")
                print(f"  交易类型: {record.get('transaction_type', 'N/A')}")
                print(f"  分类: {record.get('category', 'N/A')}")
                print(f"  备注: {record.get('remark', 'N/A')}")
                print(f"  原始数据: {record.get('raw_data', {})}")
        
        # 显示失败的记录
        if result.failed_records:
            print("\n失败的记录:")
            for i, failed in enumerate(result.failed_records, 1):
                print(f"\n失败记录 {i}:")
                print(f"  行号: {failed['row']}")
                print(f"  错误: {failed['error']}")
        
        # 显示错误信息
        if result.errors:
            print("\n错误信息:")
            for error in result.errors:
                print(f"  - {error}")
                
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n已清理测试文件: {test_file}")


if __name__ == "__main__":
    test_wechat_parser()