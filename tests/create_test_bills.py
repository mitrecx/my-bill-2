#!/usr/bin/env python3
"""
创建测试账单数据
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

def login():
    """登录获取token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result["data"]["access_token"]
    
    print(f"登录失败: {response.text}")
    return None

def get_categories(token):
    """获取账单分类"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/bills/categories", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result["data"]
    
    print(f"获取分类失败: {response.text}")
    return []

def create_bill(token, bill_data):
    """创建账单"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/v1/bills", headers=headers, json=bill_data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result["data"]
    
    print(f"创建账单失败: {response.text}")
    return None

def main():
    print("开始创建测试账单...")
    
    # 登录
    token = login()
    if not token:
        print("登录失败，退出")
        return
    
    print("登录成功!")
    
    # 获取分类
    categories = get_categories(token)
    print(f"获取到 {len(categories)} 个分类")
    
    # 创建测试账单数据
    test_bills = [
        {
            "amount": 3500.00,
            "transaction_type": "收入",
            "description": "招商银行工资发放",
            "source_type": "cmb",  # 招商银行
            "transaction_time": (datetime.now() - timedelta(days=1)).isoformat()
        },
        {
            "amount": 89.90,
            "transaction_type": "支出", 
            "description": "淘宝购物-日用品",
            "source_type": "alipay",  # 支付宝
            "transaction_time": (datetime.now() - timedelta(days=2)).isoformat()
        },
        {
            "amount": 45.50,
            "transaction_type": "支出",
            "description": "美团外卖-午餐",
            "source_type": "alipay",  # 支付宝
            "transaction_time": (datetime.now() - timedelta(days=3)).isoformat()
        },
        {
            "amount": 1200.00,
            "transaction_type": "支出",
            "description": "房租支付",
            "source_type": "cmb",  # 招商银行
            "transaction_time": (datetime.now() - timedelta(days=5)).isoformat()
        },
        {
            "amount": 68.00,
            "transaction_type": "支出",
            "description": "中石化加油",
            "source_type": "alipay",  # 支付宝
            "transaction_time": (datetime.now() - timedelta(days=7)).isoformat()
        }
    ]
    
    # 创建账单
    created_bills = []
    for i, bill_data in enumerate(test_bills):
        print(f"\n创建第 {i+1} 个账单: {bill_data['description']}")
        bill = create_bill(token, bill_data)
        if bill:
            created_bills.append(bill)
            print(f"创建成功，账单ID: {bill['id']}")
        else:
            print("创建失败")
    
    print(f"\n成功创建 {len(created_bills)} 个测试账单")
    
    # 显示创建的账单
    for bill in created_bills:
        print(f"ID: {bill['id']}, 金额: {bill['amount']}, 描述: {bill['transaction_desc']}")

if __name__ == "__main__":
    main()