#!/usr/bin/env python3
"""
调试账单详情获取问题
"""

import requests
import json

# 配置
BASE_URL = "http://127.0.0.1:8000/api/v1"

def login():
    """登录获取token"""
    login_data = {
        "username": "testuser123",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        return data["data"]["access_token"]
    else:
        print(f"❌ 登录失败: {response.status_code}")
        print(response.text)
        return None

def get_bills_list(token):
    """获取账单列表"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/bills", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data["data"]["items"]
    else:
        print(f"❌ 获取账单列表失败: {response.status_code}")
        print(response.text)
        return []

def get_bill_detail(token, bill_id):
    """获取账单详情"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/bills/{bill_id}", headers=headers)
    
    print(f"📋 获取账单 {bill_id} 详情:")
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 成功获取账单详情")
        bill = data["data"]
        print(f"   - ID: {bill['id']}")
        print(f"   - 描述: {bill.get('transaction_desc', 'N/A')}")
        print(f"   - 金额: {bill['amount']}")
        print(f"   - 类型: {bill['transaction_type']}")
        print(f"   - 分类: {bill.get('category', {}).get('name', '未分类')}")
        print(f"   - 时间: {bill['transaction_date']}")
        return bill
    else:
        print(f"   ❌ 获取失败")
        print(f"   错误信息: {response.text}")
        return None

def main():
    print("🔍 开始调试账单详情获取问题")
    print("=" * 50)
    
    # 登录
    token = login()
    if not token:
        return
    
    print("✅ 登录成功")
    
    # 获取账单列表
    bills = get_bills_list(token)
    if not bills:
        print("❌ 没有找到账单")
        return
    
    print(f"📊 找到 {len(bills)} 个账单")
    
    # 测试获取前3个账单的详情
    for i, bill in enumerate(bills[:3]):
        bill_id = bill["id"]
        print(f"\n🔍 测试账单 {i+1}/{min(3, len(bills))}")
        get_bill_detail(token, bill_id)

if __name__ == "__main__":
    main()