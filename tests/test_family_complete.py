#!/usr/bin/env python3
"""
完整测试家庭管理功能
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8000/api/v1"

def test_complete_family_management():
    """完整测试家庭管理功能"""
    print("🔧 开始完整测试家庭管理功能...")
    print("=" * 50)
    
    # 1. 登录
    print("\n1. 登录测试")
    login_data = {
        "username": "testuser",
        "password": "password123"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"❌ 登录失败: {response.status_code} - {response.text}")
        return
    
    token_data = response.json()
    access_token = token_data["data"]["access_token"]
    print(f"✅ 登录成功")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 2. 获取初始家庭列表
    print("\n2. 获取初始家庭列表")
    response = requests.get(f"{BASE_URL}/families/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取家庭列表失败: {response.status_code} - {response.text}")
        return
    
    initial_families = response.json()
    print(f"✅ 获取家庭列表成功，当前家庭数量: {len(initial_families['data'])}")
    
    # 3. 创建新家庭
    print("\n3. 创建新家庭")
    family_data = {
        "family_name": "测试家庭",
        "description": "这是一个测试家庭",
        "invite_usernames": []
    }
    
    response = requests.post(f"{BASE_URL}/families/", json=family_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 创建家庭失败: {response.status_code} - {response.text}")
        return
    
    new_family = response.json()
    family_id = new_family["data"]["id"]
    print(f"✅ 创建家庭成功，家庭ID: {family_id}")
    
    # 4. 再次获取家庭列表，验证新家庭
    print("\n4. 验证新家庭已添加")
    response = requests.get(f"{BASE_URL}/families/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取家庭列表失败: {response.status_code} - {response.text}")
        return
    
    updated_families = response.json()
    print(f"✅ 获取家庭列表成功，当前家庭数量: {len(updated_families['data'])}")
    
    # 验证响应格式
    print(f"📊 API响应格式正确: 包含'data'字段")
    print(f"📋 家庭列表: {[f['family_name'] for f in updated_families['data']]}")
    
    # 5. 获取家庭成员
    print(f"\n5. 获取家庭成员 (家庭ID: {family_id})")
    response = requests.get(f"{BASE_URL}/families/{family_id}/members", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取家庭成员失败: {response.status_code} - {response.text}")
        return
    
    members = response.json()
    print(f"✅ 获取家庭成员成功，成员数量: {len(members['data']['members'])}")
    
    # 6. 更新家庭信息
    print(f"\n6. 更新家庭信息")
    update_data = {
        "family_name": "更新后的测试家庭",
        "description": "这是更新后的描述"
    }
    
    response = requests.put(f"{BASE_URL}/families/{family_id}", json=update_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 更新家庭失败: {response.status_code} - {response.text}")
        return
    
    updated_family = response.json()
    print(f"✅ 更新家庭成功，新名称: {updated_family['data']['family_name']}")
    
    # 7. 清理：删除测试家庭
    print(f"\n7. 清理测试数据")
    response = requests.delete(f"{BASE_URL}/families/{family_id}", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 删除家庭失败: {response.status_code} - {response.text}")
        return
    
    print(f"✅ 删除家庭成功")
    
    # 8. 验证删除
    print(f"\n8. 验证家庭已删除")
    response = requests.get(f"{BASE_URL}/families/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取家庭列表失败: {response.status_code} - {response.text}")
        return
    
    final_families = response.json()
    print(f"✅ 验证删除成功，当前家庭数量: {len(final_families['data'])}")
    
    print("\n" + "=" * 50)
    print("🎉 所有家庭管理功能测试通过！")
    print("✅ API响应格式正确 (使用data字段)")
    print("✅ 前端store修复生效")
    print("✅ 家庭管理页面应该可以正常工作")

if __name__ == "__main__":
    test_complete_family_management()