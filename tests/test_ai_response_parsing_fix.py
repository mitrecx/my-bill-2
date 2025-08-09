#!/usr/bin/env python3
"""
测试AI响应解析修复
验证单个分类方法能否正确处理多行AI响应
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import requests
import json

def test_ai_response_parsing():
    """测试AI响应解析修复"""
    
    # 服务器配置
    BASE_URL = "http://localhost:8000/api/v1"
    
    # 登录获取token
    print("1. 登录获取认证token...")
    login_data = {
        "username": "test",
        "password": "test123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"登录失败: {response.status_code} - {response.text}")
        return False
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("登录成功!")
    
    # 创建一个测试账单，触发AI分类
    print("\n2. 创建测试账单，触发AI分类...")
    
    bill_data = {
        "transaction_date": "2025-01-15",
        "transaction_type": "支出",
        "amount": 25.50,
        "transaction_desc": "午餐费用",
        "source_type": "手动录入",
        "raw_data": {}
    }
    
    response = requests.post(f"{BASE_URL}/bills/", json=bill_data, headers=headers)
    if response.status_code != 200:
        print(f"创建账单失败: {response.status_code} - {response.text}")
        return False
    
    result = response.json()
    bill_id = result["id"]
    print(f"账单创建成功，ID: {bill_id}")
    print(f"AI分类结果: {result.get('ai_category_name', 'N/A')}")
    
    # 获取账单详情，验证分类结果
    print("\n3. 获取账单详情，验证分类结果...")
    response = requests.get(f"{BASE_URL}/bills/{bill_id}", headers=headers)
    if response.status_code != 200:
        print(f"获取账单详情失败: {response.status_code} - {response.text}")
        return False
    
    bill_detail = response.json()
    print(f"账单详情:")
    print(f"  - ID: {bill_detail['id']}")
    print(f"  - 描述: {bill_detail['transaction_desc']}")
    print(f"  - 分类: {bill_detail.get('category_name', 'N/A')}")
    print(f"  - AI分类: {bill_detail.get('ai_category_name', 'N/A')}")
    
    # 验证AI分类是否成功
    if bill_detail.get('ai_category_name'):
        print("\n✅ AI响应解析修复验证成功!")
        print(f"AI成功分类为: {bill_detail['ai_category_name']}")
        return True
    else:
        print("\n❌ AI响应解析修复验证失败!")
        print("AI分类结果为空")
        return False

if __name__ == "__main__":
    print("开始测试AI响应解析修复...")
    success = test_ai_response_parsing()
    
    if success:
        print("\n🎉 测试通过!")
    else:
        print("\n💥 测试失败!")
        sys.exit(1)