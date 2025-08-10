#!/usr/bin/env python3
"""
创建微信账单测试文件
"""

import pandas as pd
from datetime import datetime, timedelta
import os

def create_wechat_test_file():
    """创建微信账单测试Excel文件"""
    
    # 创建测试数据
    base_date = datetime(2024, 8, 1)
    data = []
    
    # 添加多种类型的交易记录
    transactions = [
        {
            'days_offset': 0,
            'time': '09:30:00',
            'type': '商户消费',
            'counterparty': '星巴克咖啡',
            'product': '拿铁咖啡',
            'income_expense': '支出',
            'amount': '35.00',
            'payment_method': '零钱通',
            'status': '支付成功',
            'transaction_id': '1000000000000001',
            'merchant_order_id': 'SB20240801001',
            'remark': '/'
        },
        {
            'days_offset': 0,
            'time': '12:45:00',
            'type': '商户消费',
            'counterparty': '美团外卖',
            'product': '午餐套餐',
            'income_expense': '支出',
            'amount': '42.50',
            'payment_method': '招商银行储蓄卡(1234)',
            'status': '支付成功',
            'transaction_id': '1000000000000002',
            'merchant_order_id': 'MT20240801001',
            'remark': '/'
        },
        {
            'days_offset': 1,
            'time': '18:20:00',
            'type': '转账',
            'counterparty': '张三',
            'product': '转账',
            'income_expense': '支出',
            'amount': '100.00',
            'payment_method': '零钱',
            'status': '转账成功',
            'transaction_id': '1000000000000003',
            'merchant_order_id': '/',
            'remark': '生活费'
        },
        {
            'days_offset': 2,
            'time': '09:15:00',
            'type': '商户消费',
            'counterparty': '滴滴出行',
            'product': '快车服务',
            'income_expense': '支出',
            'amount': '28.80',
            'payment_method': '微信支付分',
            'status': '支付成功',
            'transaction_id': '1000000000000004',
            'merchant_order_id': 'DD20240802001',
            'remark': '/'
        },
        {
            'days_offset': 2,
            'time': '14:30:00',
            'type': '红包',
            'counterparty': '李四',
            'product': '新年红包',
            'income_expense': '收入',
            'amount': '50.00',
            'payment_method': '/',
            'status': '已收钱',
            'transaction_id': '1000000000000005',
            'merchant_order_id': '/',
            'remark': '新年快乐'
        },
        {
            'days_offset': 3,
            'time': '10:00:00',
            'type': '商户消费',
            'counterparty': '盒马鲜生',
            'product': '生鲜购物',
            'income_expense': '支出',
            'amount': '89.60',
            'payment_method': '花呗',
            'status': '支付成功',
            'transaction_id': '1000000000000006',
            'merchant_order_id': 'HM20240804001',
            'remark': '/'
        },
        {
            'days_offset': 4,
            'time': '16:45:00',
            'type': '商户消费',
            'counterparty': '中石化加油站',
            'product': '汽油',
            'income_expense': '支出',
            'amount': '320.00',
            'payment_method': '建设银行信用卡(5678)',
            'status': '支付成功',
            'transaction_id': '1000000000000007',
            'merchant_order_id': 'ZSH20240805001',
            'remark': '/'
        },
        {
            'days_offset': 5,
            'time': '11:20:00',
            'type': '转账',
            'counterparty': '王五',
            'product': '转账',
            'income_expense': '收入',
            'amount': '200.00',
            'payment_method': '/',
            'status': '转账成功',
            'transaction_id': '1000000000000008',
            'merchant_order_id': '/',
            'remark': '还款'
        }
    ]
    
    # 构建数据
    for trans in transactions:
        trans_date = base_date + timedelta(days=trans['days_offset'])
        data.append({
            '交易时间': f"{trans_date.strftime('%Y-%m-%d')} {trans['time']}",
            '交易类型': trans['type'],
            '交易对方': trans['counterparty'],
            '商品': trans['product'],
            '收/支': trans['income_expense'],
            '金额(元)': f"¥{trans['amount']}",
            '支付方式': trans['payment_method'],
            '当前状态': trans['status'],
            '交易单号': trans['transaction_id'],
            '商户单号': trans['merchant_order_id'],
            '备注': trans['remark']
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 计算统计信息
    total_count = len(data)
    income_records = [d for d in data if d['收/支'] == '收入']
    expense_records = [d for d in data if d['收/支'] == '支出']
    
    income_count = len(income_records)
    expense_count = len(expense_records)
    
    income_amount = sum(float(d['金额(元)'].replace('¥', '')) for d in income_records)
    expense_amount = sum(float(d['金额(元)'].replace('¥', '')) for d in expense_records)
    
    # 创建完整的Excel文件，包含微信账单的标准格式
    filename = 'wechat_bills_test.xlsx'
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # 添加说明行（模拟微信账单的格式）
        header_data = [
            ['微信支付账单'],
            [''],
            [f'起始时间：{base_date.strftime("%Y-%m-%d")} 00:00:00'],
            [f'终止时间：{(base_date + timedelta(days=5)).strftime("%Y-%m-%d")} 23:59:59'],
            [f'导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'],
            [''],
            [f'共{total_count}笔交易'],
            [''],
            [f'收入：{income_count}笔 {income_amount:.2f}元'],
            [f'支出：{expense_count}笔 {expense_amount:.2f}元'],
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
    
    print(f"微信账单测试文件已创建: {filename}")
    print(f"文件路径: {os.path.abspath(filename)}")
    print(f"包含 {total_count} 条交易记录")
    print(f"收入: {income_count} 笔，共 {income_amount:.2f} 元")
    print(f"支出: {expense_count} 笔，共 {expense_amount:.2f} 元")
    
    return filename

if __name__ == "__main__":
    create_wechat_test_file()