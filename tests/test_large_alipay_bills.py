#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建大的支付宝账单文件来测试超时问题
"""

import csv
import random
from datetime import datetime, timedelta

def create_large_alipay_file(filename, num_records=1000):
    """创建包含大量记录的支付宝账单文件"""
    
    categories = ["餐饮美食", "交通出行", "生活服务", "购物消费", "医疗健康", "娱乐休闲", "教育培训", "转账"]
    transaction_types = ["支出", "收入"]
    accounts = ["支付宝余额", "招商银行储蓄卡(1234)", "花呗", "余额宝"]
    descriptions = [
        "午餐费用", "地铁费", "超市购物", "网购商品", "挂号费", "电影票", "培训费", "工资发放",
        "打车费用", "咖啡", "日用品", "服装", "药费", "游戏充值", "书籍", "转账给朋友",
        "早餐", "公交费", "水果", "电子产品", "体检费", "KTV", "课程费", "奖金",
        "晚餐", "出租车", "蔬菜", "化妆品", "看病", "旅游", "证书费", "退款"
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # 写入表头
        writer.writerow(['记录时间', '分类', '收支类型', '金额', '备注', '账户', '来源', '标签'])
        
        # 生成记录
        start_date = datetime.now() - timedelta(days=365)
        
        for i in range(num_records):
            # 随机生成时间
            random_days = random.randint(0, 365)
            random_hours = random.randint(0, 23)
            random_minutes = random.randint(0, 59)
            record_time = start_date + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
            
            # 随机选择其他字段
            category = random.choice(categories)
            transaction_type = random.choice(transaction_types)
            amount = round(random.uniform(1.0, 500.0), 2)
            description = random.choice(descriptions)
            account = random.choice(accounts)
            
            writer.writerow([
                record_time.strftime('%Y-%m-%d %H:%M:%S'),
                category,
                transaction_type,
                amount,
                description,
                account,
                '账单同步',
                ''
            ])
    
    print(f"✅ 创建了包含 {num_records} 条记录的支付宝账单文件: {filename}")

if __name__ == "__main__":
    # 创建包含1000条记录的大文件
    create_large_alipay_file("tests/large_alipay_bills.csv", 1000)