#!/usr/bin/env python3
"""
测试改进后的用户搜索功能
"""

import requests
import json
import time
import random
import string

# 配置
BASE_URL = "http://localhost:8000/api/v1"
timestamp = int(time.time())

def generate_random_string(length=8):
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def register_user(username, email, password, full_name=None):
    """注册用户"""
    user_data = {
        "username": username,
        "email": email,
        "password": password
    }
    if full_name:
        user_data["full_name"] = full_name
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    return response

def login_user(username, password):
    """用户登录"""
    login_data = {
        "username": username,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    return response

def search_users(token, query):
    """搜索用户"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{BASE_URL}/families/search-users", 
                          headers=headers, 
                          params={"q": query})
    return response

def test_user_search_functionality():
    """测试用户搜索功能"""
    print("🔍 测试改进后的用户搜索功能")
    print("=" * 50)
    
    # 创建测试用户
    test_users = [
        {
            "username": f"alice_{timestamp}",
            "email": f"alice_{timestamp}@example.com",
            "password": "password123",
            "full_name": "Alice Smith"
        },
        {
            "username": f"bob_{timestamp}",
            "email": f"bob_{timestamp}@example.com", 
            "password": "password123",
            "full_name": "Bob Johnson"
        },
        {
            "username": f"charlie_{timestamp}",
            "email": f"charlie_{timestamp}@example.com",
            "password": "password123",
            "full_name": "Charlie Brown"
        },
        {
            "username": f"david_{timestamp}",
            "email": f"david_{timestamp}@example.com",
            "password": "password123",
            "full_name": "David Wilson"
        },
        {
            "username": f"search_test_{timestamp}",
            "email": f"search_test_{timestamp}@example.com",
            "password": "password123",
            "full_name": "搜索测试用户"
        }
    ]
    
    # 注册测试用户
    print("\n📝 注册测试用户...")
    for user in test_users:
        response = register_user(user["username"], user["email"], user["password"], user["full_name"])
        if response.status_code == 200:
            print(f"✅ 用户 {user['username']} ({user['full_name']}) 注册成功")
        else:
            print(f"❌ 用户 {user['username']} 注册失败: {response.status_code}")
            print(f"   响应: {response.text}")
    
    # 登录第一个用户进行搜索测试
    print(f"\n🔐 登录用户 {test_users[0]['username']} 进行搜索测试...")
    login_response = login_user(test_users[0]["username"], test_users[0]["password"])
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code}")
        print(f"   响应: {login_response.text}")
        return
    
    token = login_response.json()["data"]["access_token"]
    print("✅ 登录成功")
    
    # 测试各种搜索场景
    search_tests = [
        {
            "query": "bob",
            "description": "按用户名搜索 'bob'"
        },
        {
            "query": "Bob",
            "description": "按用户名搜索 'Bob' (大小写)"
        },
        {
            "query": "Johnson",
            "description": "按全名搜索 'Johnson'"
        },
        {
            "query": "charlie",
            "description": "按用户名搜索 'charlie'"
        },
        {
            "query": "Brown",
            "description": "按全名搜索 'Brown'"
        },
        {
            "query": "David",
            "description": "按全名搜索 'David'"
        },
        {
            "query": "Wilson",
            "description": "按姓氏搜索 'Wilson'"
        },
        {
            "query": "搜索",
            "description": "按中文全名搜索 '搜索'"
        },
        {
            "query": "test",
            "description": "按用户名部分搜索 'test'"
        },
        {
            "query": "xyz",
            "description": "搜索不存在的用户 'xyz'"
        }
    ]
    
    print("\n🔍 开始搜索测试...")
    for test in search_tests:
        print(f"\n📋 {test['description']}")
        response = search_users(token, test["query"])
        
        if response.status_code == 200:
            result = response.json()
            users = result.get("data", [])
            print(f"✅ 搜索成功，找到 {len(users)} 个用户")
            
            for user in users:
                print(f"   - {user['username']} ({user.get('full_name', '无姓名')})")
        else:
            print(f"❌ 搜索失败: {response.status_code}")
            print(f"   响应: {response.text}")
    
    print("\n🎯 测试搜索结果排序...")
    # 测试搜索结果排序（用户名匹配优先）
    response = search_users(token, timestamp)
    if response.status_code == 200:
        result = response.json()
        users = result.get("data", [])
        print(f"✅ 按时间戳搜索，找到 {len(users)} 个用户")
        print("📊 搜索结果排序:")
        for i, user in enumerate(users, 1):
            print(f"   {i}. {user['username']} ({user.get('full_name', '无姓名')})")
    
    print("\n✨ 用户搜索功能测试完成!")

if __name__ == "__main__":
    test_user_search_functionality()