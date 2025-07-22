#!/usr/bin/env python3
"""
创建测试用户并测试家庭创建功能
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "testuser_family"
PASSWORD = "testpass123"
EMAIL = "testuser_family@example.com"

def create_test_user():
    """创建测试用户"""
    print("🔧 创建测试用户...")
    
    user_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "email": EMAIL,
        "full_name": "测试用户_家庭"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        print(f"注册响应状态码: {response.status_code}")
        print(f"注册响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 测试用户创建成功")
            return True
        elif response.status_code == 400 and ("已存在" in response.text or "已被注册" in response.text):
            print("✅ 测试用户已存在")
            return True
        else:
            print(f"❌ 创建测试用户失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 创建测试用户异常: {e}")
        return False

def test_family_creation_with_user():
    """测试家庭创建功能"""
    print("\n🔧 开始家庭创建测试...")
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
    
    login_result = response.json()
    print(f"登录响应: {login_result}")
    
    # 检查响应格式
    if "access_token" in login_result:
        token = login_result["access_token"]
    elif "data" in login_result and "access_token" in login_result["data"]:
        token = login_result["data"]["access_token"]
    else:
        print(f"❌ 无法获取访问令牌: {login_result}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登录成功")
    
    # 2. 检查是否已在家庭中
    print("\n2. 检查现有家庭")
    try:
        response = requests.get(f"{BASE_URL}/families/", headers=headers)
        if response.status_code == 200:
            families_result = response.json()
            if families_result.get("success") and families_result.get("data"):
                families = families_result["data"]
                print(f"用户当前在 {len(families)} 个家庭中")
                
                # 如果用户在家庭中，尝试退出
                for family in families:
                    family_id = family["id"]
                    print(f"尝试退出家庭: {family['family_name']} (ID: {family_id})")
                    
                    leave_response = requests.delete(f"{BASE_URL}/families/{family_id}/leave", headers=headers)
                    if leave_response.status_code == 200:
                        print(f"✅ 成功退出家庭: {family['family_name']}")
                    else:
                        print(f"❌ 退出家庭失败: {leave_response.status_code} - {leave_response.text}")
                        # 如果是管理员无法退出，尝试删除家庭
                        if "管理员" in leave_response.text or "管理权限" in leave_response.text:
                            print(f"尝试删除家庭: {family['family_name']}")
                            delete_response = requests.delete(f"{BASE_URL}/families/{family_id}", headers=headers)
                            if delete_response.status_code == 200:
                                print(f"✅ 成功删除家庭: {family['family_name']}")
                            else:
                                print(f"❌ 删除家庭失败: {delete_response.status_code} - {delete_response.text}")
            else:
                print("用户当前不在任何家庭中")
    except Exception as e:
        print(f"❌ 检查家庭状态异常: {e}")
    
    # 3. 创建家庭（不邀请任何人）
    print("\n3. 创建家庭（无邀请）")
    family_data = {
        "family_name": "测试家庭_新用户",
        "description": "这是一个新用户的测试家庭",
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
    # 先创建测试用户
    if create_test_user():
        # 然后测试家庭创建
        test_family_creation_with_user()
    else:
        print("❌ 无法创建测试用户，跳过家庭创建测试")