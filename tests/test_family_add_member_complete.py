#!/usr/bin/env python3
"""
创建测试用户并测试家庭管理功能
"""

import requests
import json

# 配置
BASE_URL = "http://127.0.0.1:8000/api/v1"
USERNAME = "test_user_family"
PASSWORD = "test123"
EMAIL = "test_family@example.com"

def register_user():
    """注册测试用户"""
    print("📝 注册测试用户...")
    
    user_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "email": EMAIL,
        "full_name": "测试用户"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    
    print(f"注册请求: POST {BASE_URL}/auth/register")
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200 or response.status_code == 201:
        result = response.json()
        print(f"✅ 用户注册成功")
        print(f"📊 响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return True
    elif response.status_code == 400:
        result = response.json()
        if "已存在" in result.get("message", ""):
            print(f"ℹ️  用户已存在，继续使用现有用户")
            return True
        else:
            print(f"❌ 用户注册失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
    else:
        print(f"❌ 用户注册失败: {response.status_code}")
        print(f"错误信息: {response.text}")
        return False

def login():
    """登录并获取token"""
    print("🔐 用户登录...")
    
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        if "data" in result and "access_token" in result["data"]:
            token = result["data"]["access_token"]
            print(f"✅ 登录成功，获取到token")
            return token
        else:
            print(f"❌ 登录响应格式异常: {result}")
            return None
    else:
        print(f"❌ 登录失败: {response.status_code} - {response.text}")
        return None

def register_additional_users():
    """注册额外的测试用户用于邀请"""
    print("\n👥 注册额外的测试用户...")
    
    additional_users = [
        {
            "username": "test_user_2",
            "password": "test123",
            "email": "test2@example.com",
            "full_name": "测试用户2"
        },
        {
            "username": "test_user_3", 
            "password": "test123",
            "email": "test3@example.com",
            "full_name": "测试用户3"
        }
    ]
    
    for user_data in additional_users:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code in [200, 201]:
            print(f"✅ 用户 {user_data['username']} 注册成功")
        elif response.status_code == 400:
            result = response.json()
            if "已存在" in result.get("message", ""):
                print(f"ℹ️  用户 {user_data['username']} 已存在")
            else:
                print(f"❌ 用户 {user_data['username']} 注册失败: {response.text}")
        else:
            print(f"❌ 用户 {user_data['username']} 注册失败: {response.status_code}")

def test_search_users(token):
    """测试用户搜索功能"""
    print("\n🔍 测试用户搜索功能...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试搜索用户
    search_query = "test_user"
    response = requests.get(f"{BASE_URL}/families/search-users", 
                          headers=headers, 
                          params={"q": search_query})
    
    print(f"搜索请求: GET {BASE_URL}/families/search-users?q={search_query}")
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 用户搜索成功")
        print(f"📊 响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if "data" in result:
            users = result["data"]
            print(f"📋 找到 {len(users)} 个用户")
            for user in users:
                print(f"  - {user.get('username')} ({user.get('full_name', '无姓名')})")
            return users
        else:
            print("⚠️  响应中没有'data'字段")
    else:
        print(f"❌ 用户搜索失败: {response.status_code}")
        print(f"错误信息: {response.text}")
    
    return []

def test_create_family_with_invite(token, invite_users):
    """测试创建家庭并邀请成员"""
    print("\n🏗️  测试创建家庭并邀请成员...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 准备邀请用户名列表
    invite_usernames = [user["username"] for user in invite_users[:2]]  # 邀请前两个用户
    
    # 创建家庭数据
    family_data = {
        "family_name": "测试家庭_添加成员功能",
        "description": "用于测试添加成员功能的家庭",
        "invite_usernames": invite_usernames
    }
    
    response = requests.post(f"{BASE_URL}/families/", 
                           headers=headers, 
                           json=family_data)
    
    print(f"请求: POST {BASE_URL}/families/")
    print(f"请求数据: {json.dumps(family_data, indent=2, ensure_ascii=False)}")
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ 创建家庭成功")
        print(f"📊 响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if "data" in result:
            family = result["data"]
            print(f"新家庭: {family['family_name']} (ID: {family['id']})")
            return family['id']
    else:
        print(f"❌ 创建家庭失败: {response.status_code}")
        print(f"错误信息: {response.text}")
    
    return None

def test_get_family_members(token, family_id):
    """测试获取家庭成员"""
    print(f"\n👥 测试获取家庭成员 (家庭ID: {family_id})...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{BASE_URL}/families/{family_id}/members", headers=headers)
    
    print(f"请求: GET {BASE_URL}/families/{family_id}/members")
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 获取家庭成员成功")
        print(f"📊 响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if "data" in result:
            members = result["data"]
            print(f"📋 家庭有 {len(members)} 个成员")
            for member in members:
                user = member.get('user', {})
                print(f"  - {user.get('username')} ({member.get('role')}) - {user.get('full_name', '无姓名')}")
        else:
            print("⚠️  响应中没有'data'字段")
    else:
        print(f"❌ 获取家庭成员失败: {response.status_code}")
        print(f"错误信息: {response.text}")

def main():
    """主测试函数"""
    print("🧪 家庭管理添加成员功能完整测试")
    print("=" * 60)
    
    # 1. 注册主测试用户
    if not register_user():
        return
    
    # 2. 注册额外的测试用户
    register_additional_users()
    
    # 3. 登录主测试用户
    token = login()
    if not token:
        return
    
    # 4. 测试用户搜索功能
    available_users = test_search_users(token)
    
    # 5. 测试创建家庭并邀请成员
    if available_users:
        family_id = test_create_family_with_invite(token, available_users)
        if family_id:
            # 6. 获取家庭成员列表
            test_get_family_members(token, family_id)
    else:
        print("⚠️  没有可邀请的用户，跳过创建家庭测试")
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    main()