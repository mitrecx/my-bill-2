#!/usr/bin/env python3
"""
直接测试搜索API
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8000/api/v1"

def test_search_api():
    """测试搜索API"""
    # 先登录获取token
    login_data = {
        "username": "alice_1753080381",
        "password": "password123"
    }
    
    print("🔐 登录用户...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code}")
        print(f"   响应: {login_response.text}")
        return
    
    token = login_response.json()["data"]["access_token"]
    print("✅ 登录成功")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试搜索
    search_queries = ["Johnson", "Bob", "bob", "Brown", "搜索"]
    
    for query in search_queries:
        print(f"\n🔍 搜索: '{query}'")
        response = requests.get(
            f"{BASE_URL}/families/search-users",
            headers=headers,
            params={"q": query}
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            users = result.get("data", [])
            print(f"找到 {len(users)} 个用户")
            for user in users:
                print(f"  - {user['username']} ({user.get('full_name', '无姓名')})")

if __name__ == "__main__":
    test_search_api()