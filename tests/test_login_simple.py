#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_register_and_login():
    """测试注册和登录功能"""
    
    # 测试用户信息
    test_user = {
        "username": "testuser123",
        "email": "testuser123@test.com", 
        "password": "testpass123",
        "full_name": "Test User"
    }
    
    print("🚀 开始测试注册和登录功能")
    print("=" * 50)
    
    # 1. 尝试注册
    print("1. 尝试注册新用户...")
    register_response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
    print(f"   注册响应状态码: {register_response.status_code}")
    
    if register_response.status_code == 200:
        register_result = register_response.json()
        print(f"   注册结果: {register_result}")
        if register_result.get("success"):
            print("   ✅ 注册成功")
        else:
            print(f"   ❌ 注册失败: {register_result.get('message')}")
    else:
        print(f"   ❌ 注册请求失败: {register_response.status_code}")
        try:
            error_detail = register_response.json()
            print(f"   错误详情: {error_detail}")
        except:
            print(f"   错误内容: {register_response.text}")
    
    # 2. 尝试登录
    print("\n2. 尝试登录...")
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]
    }
    
    login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"   登录响应状态码: {login_response.status_code}")
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        print(f"   登录结果: {login_result}")
        if login_result.get("success"):
            token = login_result["data"]["access_token"]
            print("   ✅ 登录成功")
            print(f"   Token: {token[:50]}...")
            return token
        else:
            print(f"   ❌ 登录失败: {login_result.get('message')}")
    else:
        print(f"   ❌ 登录请求失败: {login_response.status_code}")
        try:
            error_detail = login_response.json()
            print(f"   错误详情: {error_detail}")
        except:
            print(f"   错误内容: {login_response.text}")
    
    return None

def test_authenticated_request(token):
    """测试认证请求"""
    if not token:
        print("❌ 没有有效的token，跳过认证测试")
        return
    
    print("\n3. 测试认证请求...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试获取用户信息
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"   获取用户信息响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        user_info = response.json()
        print(f"   ✅ 获取用户信息成功: {user_info}")
    else:
        print(f"   ❌ 获取用户信息失败: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"   错误详情: {error_detail}")
        except:
            print(f"   错误内容: {response.text}")

if __name__ == "__main__":
    token = test_register_and_login()
    test_authenticated_request(token)
    print("\n测试完成！")