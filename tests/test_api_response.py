#!/usr/bin/env python3
"""
简单测试API响应格式
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_api_response():
    """测试API响应格式"""
    print("🔍 测试API响应格式")
    print("=" * 50)
    
    # 登录
    login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "username": "alice_1753081212",
        "password": "password123"
    })
    
    print(f"登录响应状态: {login_response.status_code}")
    if login_response.status_code == 200:
        login_data = login_response.json()
        print(f"登录响应: {json.dumps(login_data, indent=2, ensure_ascii=False)}")
        
        token = login_data["data"]["access_token"]
        
        # 搜索用户
        search_response = requests.get(f"{BASE_URL}/api/v1/families/search-users", 
                                     headers={"Authorization": f"Bearer {token}"}, 
                                     params={"q": "Bob"})
        
        print(f"\n搜索响应状态: {search_response.status_code}")
        if search_response.status_code == 200:
            search_data = search_response.json()
            print(f"搜索响应: {json.dumps(search_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"搜索失败: {search_response.text}")
    else:
        print(f"登录失败: {login_response.text}")

if __name__ == "__main__":
    test_api_response()