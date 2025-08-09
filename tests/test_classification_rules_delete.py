#!/usr/bin/env python3
"""
测试分类规则删除功能
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login():
    """登录获取token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            return data["data"]["access_token"]
    
    print(f"登录失败: {response.text}")
    return None

def test_create_and_delete_rule():
    """测试创建和删除分类规则"""
    token = login()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. 创建一个测试规则
    print("1. 创建测试规则...")
    rule_data = {
        "rule_text": "测试删除规则",
        "source_type": "alipay",
        "target_category": "餐饮美食",
        "priority": 1,
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/classification-rules/", json=rule_data, headers=headers)
    print(f"创建规则响应状态码: {response.status_code}")
    print(f"创建规则响应内容: {response.text}")
    
    if response.status_code != 200:
        print("创建规则失败，无法继续测试删除功能")
        return
    
    data = response.json()
    if not data.get("success"):
        print("创建规则失败，无法继续测试删除功能")
        return
    
    rule_id = data["data"]["id"]
    print(f"成功创建规则，ID: {rule_id}")
    
    # 2. 删除规则
    print(f"\n2. 删除规则 ID: {rule_id}...")
    response = requests.delete(f"{BASE_URL}/classification-rules/{rule_id}", headers=headers)
    print(f"删除规则响应状态码: {response.status_code}")
    print(f"删除规则响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print("✅ 删除规则成功！")
        else:
            print(f"❌ 删除规则失败: {data.get('message')}")
    else:
        print(f"❌ 删除规则失败，状态码: {response.status_code}")
    
    # 3. 验证规则已被删除
    print(f"\n3. 验证规则是否已被删除...")
    response = requests.get(f"{BASE_URL}/classification-rules/{rule_id}", headers=headers)
    print(f"获取已删除规则响应状态码: {response.status_code}")
    
    if response.status_code == 404:
        print("✅ 规则已成功删除（404 Not Found）")
    else:
        print(f"❌ 规则可能未被正确删除，状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

if __name__ == "__main__":
    test_create_and_delete_rule()