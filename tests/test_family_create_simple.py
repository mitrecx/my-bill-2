#!/usr/bin/env python3
"""
简化的家庭创建测试
专门测试创建家庭功能，不包含邀请用户
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "testuser"
PASSWORD = "testpass123"

def test_simple_family_creation():
    """简化的家庭创建测试"""
    print("🔧 开始简化家庭创建测试...")
    print("=" * 50)
    
    # 1. 登录
    print("\n1. 登录测试")
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ 登录失败: {response.status_code} - {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登录成功")
    
    # 2. 创建家庭（不邀请任何人）
    print("\n2. 创建家庭（无邀请）")
    family_data = {
        "family_name": "测试家庭_简化版",
        "description": "这是一个简化测试家庭",
        "invite_usernames": []  # 空的邀请列表
    }
    
    try:
        response = requests.post(f"{BASE_URL}/families/", json=family_data, headers=headers)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                family = result.get("data")
                print(f"✅ 创建家庭成功: {family.get('family_name')} (ID: {family.get('id')})")
                return family.get('id')
            else:
                print(f"❌ 创建家庭失败: {result.get('message')}")
        else:
            print(f"❌ 创建家庭失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 创建家庭异常: {e}")
    
    return None

if __name__ == "__main__":
    test_simple_family_creation()