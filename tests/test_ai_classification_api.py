#!/usr/bin/env python3
"""
测试AI分类API端点
"""

import requests
import json

def test_ai_classification_api():
    """测试AI分类API端点"""
    base_url = "http://localhost:8000"
    
    print("=== AI分类API测试 ===\n")
    
    # 首先登录获取token
    print("0. 用户登录...")
    login_data = {
        "username": "testapi",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,  # 使用JSON data
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            token = result["data"]["access_token"]
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            print("  登录成功，获取到token")
        else:
            print(f"  登录失败: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"  登录请求失败: {e}")
        return
    
    # 测试数据 - 不同来源的账单
    test_bills = [
        {
            "transaction_type": "支出",
            "description": "美团外卖-麦当劳",
            "source_type": "alipay"
        },
        {
            "transaction_type": "支出", 
            "description": "滴滴出行-打车费",
            "source_type": "cmb"
        },
        {
            "transaction_type": "支出",
            "description": "京东商城-手机充电器",
            "source_type": "jd"
        },
        {
            "transaction_type": "收入",
            "description": "工资发放",
            "source_type": "cmb"
        }
    ]
    
    # 首先创建一些测试账单
    print("1. 创建测试账单...")
    created_bill_ids = []
    
    for i, bill in enumerate(test_bills, 1):
        try:
            # 创建账单的数据结构
            bill_create_data = {
                "transaction_time": "2024-01-01T10:00:00",
                "description": bill["description"],
                "amount": 100.0,  # 固定金额用于测试
                "transaction_type": bill["transaction_type"],
                "source_type": bill["source_type"],
                "category_id": 8  # 默认分类ID
            }
            
            response = requests.post(
                f"{base_url}/api/v1/bills",
                json=bill_create_data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                bill_id = result["data"]["id"]
                created_bill_ids.append(bill_id)
                print(f"  创建账单 {i}: ID={bill_id}, 描述={bill['description']}")
            else:
                print(f"  创建账单 {i} 失败: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"  创建账单 {i} 请求失败: {e}")
    
    if not created_bill_ids:
        print("没有成功创建任何账单，无法进行AI分类测试")
        return
    
    print(f"\n成功创建 {len(created_bill_ids)} 个测试账单")
    
    # 测试单个账单分类
    print("\n2. 测试单个账单AI分类...")
    for i, bill_id in enumerate(created_bill_ids[:2], 1):  # 只测试前2个
        try:
            response = requests.post(
                f"{base_url}/api/v1/bills/{bill_id}/ai-classify",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"账单 {bill_id} AI分类结果:")
                print(f"  成功: {result.get('success')}")
                print(f"  消息: {result.get('message')}")
                if result.get('data'):
                    data = result['data']
                    print(f"  当前分类: {data.get('current_category')}")
                    print(f"  建议分类: {data.get('suggested_category')}")
            else:
                print(f"账单 {bill_id} AI分类失败: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"账单 {bill_id} AI分类请求失败: {e}")
        print()
    
    # 测试批量账单分类
    print("3. 测试批量账单AI分类...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/bills/ai-classify-batch",
            json=created_bill_ids,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print("批量AI分类结果:")
            print(f"  成功: {result.get('success')}")
            print(f"  消息: {result.get('message')}")
            if result.get('data') and result['data'].get('results'):
                for bill_result in result['data']['results']:
                    print(f"  账单ID {bill_result['bill_id']}: {bill_result.get('suggested_category', '分类失败')}")
        else:
            print(f"批量AI分类失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"批量AI分类请求失败: {e}")
    
    # 清理测试数据
    print("\n4. 清理测试账单...")
    for bill_id in created_bill_ids:
        try:
            response = requests.delete(f"{base_url}/api/v1/bills/{bill_id}", headers=headers)
            if response.status_code == 200:
                print(f"  删除账单 {bill_id} 成功")
            else:
                print(f"  删除账单 {bill_id} 失败: {response.status_code}")
        except Exception as e:
            print(f"  删除账单 {bill_id} 请求失败: {e}")

if __name__ == "__main__":
    test_ai_classification_api()