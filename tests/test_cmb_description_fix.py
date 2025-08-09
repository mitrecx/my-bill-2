#!/usr/bin/env python3
"""
测试CMB账单描述字段组合修复
"""

import requests
import json
import sys
import os

# 添加项目根目录到Python路径
project_root = "/Users/chenxing/projects/my-bills-2"
backend_root = os.path.join(project_root, "backend")
sys.path.insert(0, project_root)
sys.path.insert(0, backend_root)

# API基础URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

def login_user():
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
        else:
            print(f"登录失败: {result.get('message', '未知错误')}")
            return None
    else:
        print(f"登录请求失败: {response.status_code}")
        return None

def create_test_bill(token, description):
    """创建测试账单"""
    headers = {"Authorization": f"Bearer {token}"}
    
    bill_data = {
        "amount": 100.0,
        "transaction_type": "expense",
        "transaction_desc": description,
        "transaction_time": "2025-01-01T12:00:00",
        "source_type": "cmb"
    }
    
    response = requests.post(f"{BASE_URL}/bills", json=bill_data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result["data"]["id"]
        else:
            print(f"创建账单失败: {result.get('message', '未知错误')}")
            return None
    else:
        print(f"创建账单请求失败: {response.status_code}")
        return None

def get_bill_details(token, bill_id):
    """获取账单详情"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/bills/{bill_id}", headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result["data"]
        else:
            print(f"获取账单失败: {result.get('message', '未知错误')}")
            return None
    else:
        print(f"获取账单请求失败: {response.status_code}")
        return None

def delete_bill(token, bill_id):
    """删除账单"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.delete(f"{BASE_URL}/bills/{bill_id}", headers=headers)
    if response.status_code == 200:
        result = response.json()
        return result.get("success", False)
    else:
        print(f"删除账单请求失败: {response.status_code}")
        return False

def test_cmb_description_combination():
    """测试CMB账单描述字段组合"""
    print("=== 测试CMB账单描述字段组合 ===")
    
    # 登录
    token = login_user()
    if not token:
        print("登录失败，无法继续测试")
        return
    
    print("✓ 用户登录成功")
    
    # 测试用例 - 现在直接使用组合后的描述
    test_cases = [
        {
            "description": "快捷支付-美团外卖",
            "expected": "快捷支付-美团外卖"
        },
        {
            "description": "网上支付-京东商城",
            "expected": "网上支付-京东商城"
        },
        {
            "description": "转账汇款-张三",
            "expected": "转账汇款-张三"
        }
    ]
    
    created_bills = []
    
    try:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- 测试用例 {i} ---")
            print(f"描述: {test_case['description']}")
            print(f"期望结果: {test_case['expected']}")
            
            # 创建账单
            bill_id = create_test_bill(token, test_case['description'])
            if not bill_id:
                print(f"✗ 创建账单失败")
                continue
            
            created_bills.append(bill_id)
            print(f"✓ 账单创建成功，ID: {bill_id}")
            
            # 获取账单详情
            bill_details = get_bill_details(token, bill_id)
            if not bill_details:
                print(f"✗ 获取账单详情失败")
                continue
            
            # 检查描述字段
            actual_description = bill_details.get('transaction_desc', '')
            print(f"实际描述: {actual_description}")
            
            if actual_description == test_case['expected']:
                print(f"✓ 描述字段正确")
            else:
                print(f"✗ 描述字段错误，期望: {test_case['expected']}, 实际: {actual_description}")
    
    finally:
        # 清理测试数据
        print(f"\n=== 清理测试数据 ===")
        for bill_id in created_bills:
            if delete_bill(token, bill_id):
                print(f"✓ 删除账单 {bill_id}")
            else:
                print(f"✗ 删除账单 {bill_id} 失败")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_cmb_description_combination()