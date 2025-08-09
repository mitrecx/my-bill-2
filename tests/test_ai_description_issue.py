#!/usr/bin/env python3
"""
测试AI分类描述字段问题
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def login():
    """登录获取token"""
    login_data = {
        "username": "test",
        "password": "test123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        print(f"登录响应: {result}")
        # 检查不同的可能字段
        if "access_token" in result:
            return result["access_token"]
        elif "data" in result and "access_token" in result["data"]:
            return result["data"]["access_token"]
        else:
            print(f"未找到access_token字段: {result}")
            return None
    else:
        print(f"登录失败: {response.text}")
        return None

def test_single_ai_classification(token, bill_id):
    """测试单个账单AI分类"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n=== 测试账单 {bill_id} 的AI分类 ===")
    
    # 调用AI分类接口
    response = requests.post(f"{BASE_URL}/bills/{bill_id}/ai-classify", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"AI分类结果: {result}")
        return result
    else:
        print(f"AI分类失败: {response.status_code} - {response.text}")
        return None

def test_batch_ai_classification(token, bill_ids):
    """测试批量AI分类"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n=== 测试批量AI分类 ===")
    print(f"账单IDs: {bill_ids}")
    
    # 调用批量AI分类接口
    data = {"bill_ids": bill_ids}
    response = requests.post(f"{BASE_URL}/bills/batch-ai-classify", json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"批量AI分类结果: {result}")
        return result
    else:
        print(f"批量AI分类失败: {response.status_code} - {response.text}")
        return None

def get_bill_detail(token, bill_id):
    """获取账单详情"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/bills/{bill_id}", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取账单详情失败: {response.status_code} - {response.text}")
        return None

def main():
    # 登录
    token = login()
    if not token:
        return
    
    # 测试的账单IDs
    test_bill_ids = [13328, 13329, 13330]
    
    # 先获取账单详情
    for bill_id in test_bill_ids:
        print(f"\n=== 账单 {bill_id} 详情 ===")
        bill_detail = get_bill_detail(token, bill_id)
        if bill_detail:
            print(f"交易描述: {bill_detail.get('transaction_desc', 'N/A')}")
            print(f"来源类型: {bill_detail.get('source_type', 'N/A')}")
            print(f"原始数据: {bill_detail.get('raw_data', 'N/A')}")
    
    # 测试单个AI分类
    for bill_id in test_bill_ids:
        test_single_ai_classification(token, bill_id)
    
    # 测试批量AI分类
    test_batch_ai_classification(token, test_bill_ids)

if __name__ == "__main__":
    main()