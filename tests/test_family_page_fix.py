#!/usr/bin/env python3
"""
测试家庭管理页面修复
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:5173"

def test_login():
    """测试登录"""
    login_data = {
        "username": "testuser",
        "password": "password123"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["data"]["access_token"]
        print(f"✅ 登录成功，获取到token: {access_token[:20]}...")
        return access_token
    else:
        print(f"❌ 登录失败: {response.status_code} - {response.text}")
        return None

def test_get_families(access_token):
    """测试获取家庭列表API"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{BASE_URL}/families/", headers=headers)
    
    if response.status_code == 200:
        families_data = response.json()
        print(f"✅ 获取家庭列表成功")
        print(f"📊 响应格式: {json.dumps(families_data, indent=2, ensure_ascii=False)}")
        
        # 检查响应格式
        if "data" in families_data:
            families = families_data["data"]
            print(f"📋 家庭数量: {len(families)}")
            if families:
                print(f"📝 第一个家庭: {families[0]['family_name']}")
        else:
            print("⚠️  响应中没有'data'字段")
            
        return families_data
    else:
        print(f"❌ 获取家庭列表失败: {response.status_code} - {response.text}")
        return None

def test_frontend_accessibility():
    """测试前端可访问性"""
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print(f"✅ 前端服务正常运行在 {FRONTEND_URL}")
            return True
        else:
            print(f"❌ 前端服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到前端服务: {e}")
        return False

def main():
    print("🔧 开始测试家庭管理页面修复...")
    print("=" * 50)
    
    # 测试前端服务
    print("\n1. 测试前端服务可访问性")
    test_frontend_accessibility()
    
    # 测试后端API
    print("\n2. 测试后端登录")
    access_token = test_login()
    
    if access_token:
        print("\n3. 测试家庭列表API")
        families_data = test_get_families(access_token)
        
        if families_data:
            print("\n✅ 所有API测试通过！")
            print("🎯 修复说明:")
            print("   - 修复了store中fetchFamilies方法的API响应处理")
            print("   - 将response.families改为response.data")
            print("   - 确保与ApiResponse<Family[]>格式一致")
            print(f"\n🌐 请在浏览器中访问: {FRONTEND_URL}")
            print("   然后导航到家庭管理页面进行测试")
        else:
            print("\n❌ API测试失败")
    else:
        print("\n❌ 登录失败，无法继续测试")

if __name__ == "__main__":
    main()