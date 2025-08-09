#!/usr/bin/env python3
"""
测试AI批量分类解析修复
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def login():
    """用户登录"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result["data"]["access_token"]
    
    print(f"登录失败: {response.status_code} - {response.text}")
    return None

def create_test_bills(token):
    """创建测试账单"""
    headers = {"Authorization": f"Bearer {token}"}
    
    test_bills = [
        {
            "amount": 100.0,
            "transaction_type": "expense",
            "description": "测试账单1",
            "transaction_time": "2025-01-01T12:00:00",
            "source_type": "alipay"
        },
        {
            "amount": 200.0,
            "transaction_type": "expense", 
            "description": "测试账单2",
            "transaction_time": "2025-01-01T13:00:00",
            "source_type": "alipay"
        },
        {
            "amount": 300.0,
            "transaction_type": "expense",
            "description": "测试账单3", 
            "transaction_time": "2025-01-01T14:00:00",
            "source_type": "alipay"
        }
    ]
    
    created_bills = []
    for bill_data in test_bills:
        response = requests.post(f"{BASE_URL}/bills", json=bill_data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                created_bills.append(result["data"]["id"])
                print(f"✓ 创建账单成功，ID: {result['data']['id']}")
            else:
                print(f"✗ 创建账单失败: {result}")
        else:
            print(f"✗ 创建账单请求失败: {response.status_code} - {response.text}")
    
    return created_bills

def test_batch_ai_classification(token, bill_ids):
    """测试批量AI分类"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 批量AI分类 - 直接发送账单ID列表
    response = requests.post(f"{BASE_URL}/bills/ai-classify-batch", json=bill_ids, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("✓ 批量AI分类成功")
            print(f"分类结果: {json.dumps(result['data'], indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"✗ 批量AI分类失败: {result}")
    else:
        print(f"✗ 批量AI分类请求失败: {response.status_code} - {response.text}")
    
    return False

def delete_bills(token, bill_ids):
    """删除测试账单"""
    headers = {"Authorization": f"Bearer {token}"}
    
    for bill_id in bill_ids:
        response = requests.delete(f"{BASE_URL}/bills/{bill_id}", headers=headers)
        if response.status_code == 200:
            print(f"✓ 删除账单 {bill_id}")
        else:
            print(f"✗ 删除账单 {bill_id} 失败")

def main():
    print("=== 测试AI批量分类解析修复 ===")
    
    # 登录
    token = login()
    if not token:
        print("登录失败，无法继续测试")
        return
    
    print("✓ 用户登录成功")
    
    # 创建测试账单
    print("\n--- 创建测试账单 ---")
    bill_ids = create_test_bills(token)
    
    if not bill_ids:
        print("没有成功创建任何账单，测试结束")
        return
    
    print(f"成功创建 {len(bill_ids)} 个测试账单")
    
    try:
        # 测试批量AI分类
        print("\n--- 测试批量AI分类 ---")
        success = test_batch_ai_classification(token, bill_ids)
        
        if success:
            print("✓ 批量AI分类测试通过")
        else:
            print("✗ 批量AI分类测试失败")
            
    finally:
        # 清理测试数据
        print("\n=== 清理测试数据 ===")
        delete_bills(token, bill_ids)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()