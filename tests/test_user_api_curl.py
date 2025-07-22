#!/usr/bin/env python3
"""
简单的用户管理API测试脚本
使用curl命令测试API
"""

import subprocess
import json
import sys

def run_curl(method, url, headers=None, data=None):
    """运行curl命令"""
    cmd = ["curl", "-s", "-X", method]
    
    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])
    
    if data:
        cmd.extend(["-d", json.dumps(data)])
    
    cmd.append(url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def main():
    base_url = "http://127.0.0.1:8000"
    
    print("🚀 开始用户管理API测试")
    print("=" * 50)
    
    # 1. 登录获取token
    print("\n1. 登录测试")
    login_data = {"username": "test", "password": "test123"}
    headers = {"Content-Type": "application/json"}
    
    code, response, error = run_curl("POST", f"{base_url}/api/v1/auth/login", headers, login_data)
    
    if code != 0:
        print(f"❌ 登录请求失败: {error}")
        sys.exit(1)
    
    try:
        login_result = json.loads(response)
        if login_result.get("success"):
            token = login_result["data"]["access_token"]
            print(f"✅ 登录成功，获得token: {token[:50]}...")
        else:
            print(f"❌ 登录失败: {login_result.get('message')}")
            sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ 登录响应解析失败: {response}")
        sys.exit(1)
    
    # 2. 获取用户列表
    print("\n2. 获取用户列表")
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    code, response, error = run_curl("GET", f"{base_url}/api/v1/users?page=1&size=10", auth_headers)
    
    if code != 0:
        print(f"❌ 获取用户列表请求失败: {error}")
    else:
        try:
            users_result = json.loads(response)
            if users_result.get("success"):
                users_data = users_result["data"]
                print(f"✅ 成功获取用户列表")
                print(f"总用户数: {users_data['total']}")
                print(f"当前页用户数: {len(users_data['items'])}")
                
                for user in users_data['items']:
                    admin_status = "👑 管理员" if user.get('is_admin') else "👤 普通用户"
                    print(f"  - {user['username']} ({user['full_name']}) - {admin_status}")
            else:
                print(f"❌ 获取用户列表失败: {users_result.get('message')}")
        except json.JSONDecodeError:
            print(f"❌ 用户列表响应解析失败: {response}")
    
    # 3. 搜索用户
    print("\n3. 搜索用户")
    code, response, error = run_curl("GET", f"{base_url}/api/v1/users/search?keyword=test", auth_headers)
    
    if code != 0:
        print(f"❌ 搜索用户请求失败: {error}")
    else:
        try:
            search_result = json.loads(response)
            if search_result.get("success"):
                users = search_result["data"]
                print(f"✅ 搜索成功，找到 {len(users)} 个用户")
                
                for user in users:
                    admin_status = "👑 管理员" if user.get('is_admin') else "👤 普通用户"
                    print(f"  - {user['username']} ({user['full_name']}) - {admin_status}")
            else:
                print(f"❌ 搜索用户失败: {search_result.get('message')}")
        except json.JSONDecodeError:
            print(f"❌ 搜索响应解析失败: {response}")
    
    # 4. 创建新用户
    print("\n4. 创建新用户")
    new_user_data = {
        "username": "testuser002",
        "password": "password123",
        "email": "testuser002@example.com",
        "full_name": "测试用户002",
        "is_admin": False
    }
    
    code, response, error = run_curl("POST", f"{base_url}/api/v1/users", auth_headers, new_user_data)
    
    if code != 0:
        print(f"❌ 创建用户请求失败: {error}")
    else:
        try:
            create_result = json.loads(response)
            if create_result.get("success"):
                user = create_result["data"]
                admin_status = "👑 管理员" if user.get('is_admin') else "👤 普通用户"
                print(f"✅ 用户创建成功: {user['username']} ({user['full_name']}) - {admin_status}")
                new_user_id = user['id']
                
                # 5. 更新用户
                print("\n5. 更新用户")
                update_data = {
                    "full_name": "更新后的测试用户002",
                    "is_admin": True
                }
                
                code, response, error = run_curl("PUT", f"{base_url}/api/v1/users/{new_user_id}", auth_headers, update_data)
                
                if code != 0:
                    print(f"❌ 更新用户请求失败: {error}")
                else:
                    try:
                        update_result = json.loads(response)
                        if update_result.get("success"):
                            updated_user = update_result["data"]
                            admin_status = "👑 管理员" if updated_user.get('is_admin') else "👤 普通用户"
                            print(f"✅ 用户更新成功: {updated_user['username']} ({updated_user['full_name']}) - {admin_status}")
                        else:
                            print(f"❌ 更新用户失败: {update_result.get('message')}")
                    except json.JSONDecodeError:
                        print(f"❌ 更新响应解析失败: {response}")
                
                # 6. 删除用户
                print("\n6. 删除用户")
                code, response, error = run_curl("DELETE", f"{base_url}/api/v1/users/{new_user_id}", auth_headers)
                
                if code != 0:
                    print(f"❌ 删除用户请求失败: {error}")
                else:
                    try:
                        delete_result = json.loads(response)
                        if delete_result.get("success"):
                            print(f"✅ 用户删除成功")
                        else:
                            print(f"❌ 删除用户失败: {delete_result.get('message')}")
                    except json.JSONDecodeError:
                        print(f"❌ 删除响应解析失败: {response}")
                        
            else:
                print(f"❌ 创建用户失败: {create_result.get('message')}")
        except json.JSONDecodeError:
            print(f"❌ 创建响应解析失败: {response}")
    
    print("\n🎉 用户管理API测试完成")

if __name__ == "__main__":
    main()