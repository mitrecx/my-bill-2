#!/usr/bin/env python3
"""
测试分类规则API的调试脚本
"""

import requests
import json

# API基础URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_login():
    """测试登录并获取token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"登录响应状态: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"登录成功: {data}")
        return data.get("data", {}).get("access_token")
    else:
        print(f"登录失败: {response.text}")
        return None

def test_get_source_types(token):
    """测试获取来源类型选项"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/classification-rules/source-types/options", headers=headers)
    print(f"\n获取来源类型选项响应状态: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    return response.json() if response.status_code == 200 else None

def test_get_rules(token):
    """测试获取分类规则列表"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/classification-rules/", headers=headers)
    print(f"\n获取分类规则列表响应状态: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    return response.json() if response.status_code == 200 else None

def test_create_rule(token):
    """测试创建分类规则"""
    headers = {"Authorization": f"Bearer {token}"}
    
    rule_data = {
        "rule_text": "测试规则",
        "source_type": "alipay",
        "target_category": "工资收入",
        "priority": 1,
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/classification-rules/", json=rule_data, headers=headers)
    print(f"\n创建分类规则响应状态: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    return response.json() if response.status_code == 200 else None

if __name__ == "__main__":
    print("开始测试分类规则API...")
    
    # 1. 登录获取token
    token = test_login()
    if not token:
        print("登录失败，无法继续测试")
        exit(1)
    
    # 2. 测试获取来源类型选项
    source_types = test_get_source_types(token)
    
    # 3. 测试获取分类规则列表
    rules = test_get_rules(token)
    
    # 4. 测试创建分类规则
    new_rule = test_create_rule(token)
    
    print("\n测试完成!")