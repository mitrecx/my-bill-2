#!/usr/bin/env python3
"""
测试家庭管理页面添加成员功能
"""

import requests
import json

# 配置
BASE_URL = "http://127.0.0.1:8000/api/v1"
USERNAME = "test_user"
PASSWORD = "test123"

def login():
    """登录并获取token"""
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

def test_search_users(token):
    """测试用户搜索功能"""
    print("\n🔍 测试用户搜索功能...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试搜索用户
    search_query = "test"
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
        else:
            print("⚠️  响应中没有'data'字段")
    else:
        print(f"❌ 用户搜索失败: {response.status_code}")
        print(f"错误信息: {response.text}")

def test_get_families(token):
    """测试获取家庭列表"""
    print("\n🏠 测试获取家庭列表...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{BASE_URL}/families/", headers=headers)
    
    print(f"请求: GET {BASE_URL}/families/")
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 获取家庭列表成功")
        print(f"📊 响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if "data" in result:
            families = result["data"]
            print(f"📋 找到 {len(families)} 个家庭")
            if families:
                family = families[0]
                print(f"当前家庭: {family['family_name']} (ID: {family['id']})")
                return family['id']
        else:
            print("⚠️  响应中没有'data'字段")
    else:
        print(f"❌ 获取家庭列表失败: {response.status_code}")
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

def test_create_family_with_invite(token):
    """测试创建家庭并邀请成员"""
    print("\n🏗️  测试创建家庭并邀请成员...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 先搜索可邀请的用户
    search_response = requests.get(f"{BASE_URL}/families/search-users", 
                                 headers=headers, 
                                 params={"q": "test"})
    
    invite_usernames = []
    if search_response.status_code == 200:
        search_result = search_response.json()
        if "data" in search_result and search_result["data"]:
            # 取第一个搜索到的用户
            first_user = search_result["data"][0]
            invite_usernames = [first_user["username"]]
            print(f"准备邀请用户: {first_user['username']}")
    
    # 创建家庭数据
    family_data = {
        "family_name": "测试家庭_添加成员",
        "description": "用于测试添加成员功能的家庭",
        "invite_usernames": invite_usernames
    }
    
    response = requests.post(f"{BASE_URL}/families/", 
                           headers=headers, 
                           json=family_data)
    
    print(f"请求: POST {BASE_URL}/families/")
    print(f"请求数据: {json.dumps(family_data, indent=2, ensure_ascii=False)}")
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200 or response.status_code == 201:
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

def main():
    """主测试函数"""
    print("🧪 家庭管理添加成员功能测试")
    print("=" * 50)
    
    # 1. 登录
    token = login()
    if not token:
        return
    
    # 2. 测试用户搜索功能
    test_search_users(token)
    
    # 3. 获取现有家庭
    family_id = test_get_families(token)
    
    # 4. 如果有家庭，获取成员列表
    if family_id:
        test_get_family_members(token, family_id)
    
    # 5. 测试创建家庭并邀请成员
    new_family_id = test_create_family_with_invite(token)
    if new_family_id:
        test_get_family_members(token, new_family_id)
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    main()