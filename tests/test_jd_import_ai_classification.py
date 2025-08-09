#!/usr/bin/env python3
"""
测试JD账单导入时AI分类是否包含分类信息
"""

import requests
import json

def test_jd_import_ai_classification():
    """测试JD账单导入时AI分类"""
    
    # 1. 登录获取token
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {
        "username": "test",
        "password": "test123"
    }
    
    print("正在登录...")
    response = requests.post(login_url, json=login_data)
    if response.status_code != 200:
        print(f"登录失败: {response.status_code} - {response.text}")
        return
    
    login_result = response.json()
    if not login_result.get('success'):
        print(f"登录失败: {login_result}")
        return
    
    access_token = login_result['data']['access_token']
    print(f"登录成功，获取到access_token")
    
    # 2. 获取账单列表，查找JD账单
    print("\n获取账单列表...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    bills_url = "http://localhost:8000/api/v1/bills?page=1&page_size=50&source_type=jd"
    response = requests.get(bills_url, headers=headers)
    
    if response.status_code != 200:
        print(f"获取账单列表失败: {response.status_code} - {response.text}")
        return
    
    bills_result = response.json()
    print(f"账单API响应: {json.dumps(bills_result, indent=2, ensure_ascii=False)}")
    
    if not bills_result.get('success'):
        print(f"获取账单列表失败: {bills_result}")
        return
    
    # 检查响应数据结构
    data = bills_result.get('data', {})
    if 'bills' in data:
        bills = data['bills']
    elif 'items' in data:
        bills = data['items']
    else:
        bills = data if isinstance(data, list) else []
    if not bills:
        print("没有找到JD账单")
        return
    
    print(f"找到 {len(bills)} 个JD账单")
    
    # 取最新的3个账单进行测试
    test_bills = bills[:3]
    bill_ids = [bill['id'] for bill in test_bills]
    
    print("测试账单信息:")
    for bill in test_bills:
        print(f"  账单ID: {bill['id']}")
        print(f"  交易描述: {bill['transaction_desc']}")
        print(f"  当前分类: {bill.get('category_name', 'None')}")
        print()
    
    # 3. 测试批量AI分类
    print("测试批量AI分类...")
    classify_url = "http://localhost:8000/api/v1/bills/ai-classify-batch"
    
    print(f"调用AI分类接口，账单IDs: {bill_ids}")
    response = requests.post(classify_url, json=bill_ids, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"AI分类成功: {result['message']}")
        
        # 显示分类结果
        if result.get('data') and result['data'].get('results'):
            for item in result['data']['results']:
                print(f"  账单ID {item['bill_id']}: {item.get('suggested_category', 'N/A')}")
    else:
        print(f"AI分类失败: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_jd_import_ai_classification()