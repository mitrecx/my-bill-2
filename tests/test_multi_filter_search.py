#!/usr/bin/env python3
"""
测试分类规则多条件搜索功能
"""

import requests
import json

# API 基础URL
BASE_URL = "http://localhost:8000/api/v1"

def login():
    """登录获取token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result["data"]["access_token"]
    
    raise Exception(f"登录失败: {response.text}")

def test_multi_filter_search():
    """测试多条件搜索功能"""
    # 获取token
    token = login()
    headers = {"Authorization": f"Bearer {token}"}
    
    print("=== 测试分类规则多条件搜索功能 ===")
    
    # 1. 测试单一条件搜索
    print("\n1. 测试单一条件搜索:")
    
    # 只按来源类型搜索
    response = requests.get(f"{BASE_URL}/classification-rules/?page=1&page_size=10&source_type=alipay", headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"   支付宝规则数: {result['data']['total']}")
        else:
            print(f"   搜索失败: {result.get('message')}")
    else:
        print(f"   请求失败: {response.status_code}")
    
    # 只按状态搜索
    response = requests.get(f"{BASE_URL}/classification-rules/?page=1&page_size=10&is_active=true", headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"   启用规则数: {result['data']['total']}")
        else:
            print(f"   搜索失败: {result.get('message')}")
    else:
        print(f"   请求失败: {response.status_code}")
    
    # 2. 测试多条件组合搜索
    print("\n2. 测试多条件组合搜索:")
    
    # 搜索文本 + 来源类型
    response = requests.get(
        f"{BASE_URL}/classification-rules/?page=1&page_size=10&search=银行&source_type=cmb", 
        headers=headers
    )
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"   包含'银行'且来源为招商银行的规则数: {result['data']['total']}")
            for rule in result["data"]["rules"]:
                print(f"   - {rule['rule_text']} (来源: {rule['source_type']})")
        else:
            print(f"   搜索失败: {result.get('message')}")
    else:
        print(f"   请求失败: {response.status_code}")
    
    # 搜索文本 + 状态
    response = requests.get(
        f"{BASE_URL}/classification-rules/?page=1&page_size=10&search=支付&is_active=true", 
        headers=headers
    )
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"   包含'支付'且状态为启用的规则数: {result['data']['total']}")
            for rule in result["data"]["rules"]:
                print(f"   - {rule['rule_text']} (状态: {'启用' if rule['is_active'] else '禁用'})")
        else:
            print(f"   搜索失败: {result.get('message')}")
    else:
        print(f"   请求失败: {response.status_code}")
    
    # 来源类型 + 状态
    response = requests.get(
        f"{BASE_URL}/classification-rules/?page=1&page_size=10&source_type=jd&is_active=true", 
        headers=headers
    )
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"   京东来源且状态为启用的规则数: {result['data']['total']}")
            for rule in result["data"]["rules"]:
                print(f"   - {rule['rule_text']} (来源: {rule['source_type']}, 状态: {'启用' if rule['is_active'] else '禁用'})")
        else:
            print(f"   搜索失败: {result.get('message')}")
    else:
        print(f"   请求失败: {response.status_code}")
    
    # 3. 测试三条件组合搜索
    print("\n3. 测试三条件组合搜索:")
    
    # 搜索文本 + 来源类型 + 状态
    response = requests.get(
        f"{BASE_URL}/classification-rules/?page=1&page_size=10&search=京东&source_type=jd&is_active=true", 
        headers=headers
    )
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"   包含'京东'且来源为京东且状态为启用的规则数: {result['data']['total']}")
            for rule in result["data"]["rules"]:
                print(f"   - {rule['rule_text']} (来源: {rule['source_type']}, 状态: {'启用' if rule['is_active'] else '禁用'})")
        else:
            print(f"   搜索失败: {result.get('message')}")
    else:
        print(f"   请求失败: {response.status_code}")
    
    # 4. 测试目标分类筛选
    print("\n4. 测试目标分类筛选:")
    
    # 按目标分类搜索
    response = requests.get(
        f"{BASE_URL}/classification-rules/?page=1&page_size=10&target_category=工资收入", 
        headers=headers
    )
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"   目标分类为'工资收入'的规则数: {result['data']['total']}")
            for rule in result["data"]["rules"]:
                print(f"   - {rule['rule_text']} (目标分类: {rule['target_category']})")
        else:
            print(f"   搜索失败: {result.get('message')}")
    else:
        print(f"   请求失败: {response.status_code}")

if __name__ == "__main__":
    try:
        test_multi_filter_search()
        print("\n=== 多条件搜索功能测试完成 ===")
    except Exception as e:
        print(f"测试失败: {e}")