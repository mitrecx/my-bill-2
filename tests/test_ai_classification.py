#!/usr/bin/env python3
"""
AI分类功能测试脚本
测试基于GLM-4.5的账单分类功能
"""

import requests
import json
import sys
import os

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

def test_ai_service_status(token):
    """测试AI分类服务状态"""
    print("\n=== 测试AI分类服务状态 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/bills/ai-classification/status", headers=headers)
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result.get("data", {}).get("available", False)
    else:
        print(f"错误: {response.text}")
        return False

def get_bills(token, limit=5):
    """获取账单列表"""
    print(f"\n=== 获取前{limit}个账单 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/bills?limit={limit}", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"账单API响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        if result.get("success"):
            # 检查响应数据结构
            data = result.get("data", {})
            bills = data.get("bills", data.get("items", []))  # 尝试不同的字段名
            print(f"获取到 {len(bills)} 个账单")
            for bill in bills:
                category_name = bill.get('category', {}).get('name', '未分类') if bill.get('category') else '未分类'
                print(f"账单ID: {bill['id']}, 金额: {bill['amount']}, 描述: {bill['transaction_desc']}, 当前分类: {category_name}")
            return bills
    
    print(f"获取账单失败: {response.text}")
    return []

def test_single_bill_ai_classification(token, bill_id):
    """测试单个账单AI分类"""
    print(f"\n=== 测试账单 {bill_id} 的AI分类 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/v1/bills/{bill_id}/ai-classify", headers=headers)
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"AI分类结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    else:
        print(f"AI分类失败: {response.text}")
        return None

def test_batch_ai_classification(token, bill_ids):
    """测试批量AI分类"""
    print(f"\n=== 测试批量AI分类 ===")
    print(f"账单IDs: {bill_ids}")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/v1/bills/ai-classify-batch", 
                           headers=headers, 
                           json=bill_ids)
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"批量AI分类结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    else:
        print(f"批量AI分类失败: {response.text}")
        return None

def test_apply_ai_classification(token, bill_id):
    """测试应用AI分类结果"""
    print(f"\n=== 测试应用账单 {bill_id} 的AI分类结果 ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/v1/bills/{bill_id}/apply-ai-classification", headers=headers)
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"应用AI分类结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    else:
        print(f"应用AI分类失败: {response.text}")
        return None

def main():
    print("开始测试AI分类功能...")
    
    # 登录
    token = login()
    if not token:
        print("登录失败，退出测试")
        return
    
    print("登录成功!")
    
    # 测试AI服务状态
    ai_available = test_ai_service_status(token)
    if not ai_available:
        print("AI服务不可用，可能需要配置ZHIPU_API_KEY")
        print("继续测试API端点...")
    
    # 获取账单
    bills = get_bills(token, 3)
    if not bills:
        print("没有账单可供测试")
        return
    
    # 测试单个账单AI分类
    first_bill_id = bills[0]["id"]
    ai_result = test_single_bill_ai_classification(token, first_bill_id)
    
    # 测试批量AI分类
    bill_ids = [bill["id"] for bill in bills[:2]]
    batch_result = test_batch_ai_classification(token, bill_ids)
    
    # 如果AI服务可用且有分类结果，测试应用分类
    if ai_available and ai_result and ai_result.get("success"):
        test_apply_ai_classification(token, first_bill_id)
    
    print("\n=== AI分类功能测试完成 ===")

if __name__ == "__main__":
    main()