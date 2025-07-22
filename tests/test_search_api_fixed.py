#!/usr/bin/env python3
"""
测试搜索API修复后的效果
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def login_user(username, password):
    """用户登录"""
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["data"]["access_token"]
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

def test_search_api():
    """测试搜索API"""
    print("🔍 测试搜索API修复效果")
    print("=" * 50)
    
    # 登录用户
    token = login_user("alice_1753081212", "password123")
    if not token:
        print("❌ 登录失败")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试不同的搜索查询
    test_queries = [
        "Johnson",  # 全名搜索
        "Bob",      # 名字搜索
        "Brown",    # 姓氏搜索
        "搜索",     # 中文搜索
        "bob"       # 小写搜索
    ]
    
    for query in test_queries:
        print(f"\n📋 搜索 '{query}':")
        response = requests.get(f"{BASE_URL}/api/v1/families/search-users", 
                              headers=headers, 
                              params={"q": query})
        
        if response.status_code == 200:
            result = response.json()
            users = result.get("data", [])
            print(f"✅ 找到 {len(users)} 个用户")
            for user in users[:3]:  # 只显示前3个
                print(f"   - {user['username']} ({user.get('full_name', 'N/A')}) - {user.get('email', 'N/A')}")
        else:
            print(f"❌ 搜索失败: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_search_api()