#!/usr/bin/env python3
"""
用户管理API完整测试脚本
测试所有用户管理相关的API端点
"""

import requests
import json
import sys
from typing import Optional

class UserManagementTester:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.headers = {"Content-Type": "application/json"}
    
    def login(self, username: str, password: str) -> bool:
        """登录并获取访问令牌"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": username, "password": password},
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["data"]["access_token"]
                self.headers["Authorization"] = f"Bearer {self.access_token}"
                print(f"✅ 登录成功: {data['message']}")
                print(f"🔑 访问令牌: {self.access_token[:50]}...")
                return True
            else:
                print(f"❌ 登录失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False
    
    def get_users(self, page: int = 1, size: int = 10) -> bool:
        """获取用户列表"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/users",
                params={"page": page, "size": size},
                headers=self.headers
            )
            
            print(f"\n📋 获取用户列表 (页码: {page}, 大小: {size})")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功获取用户列表")
                print(f"总用户数: {data['data']['total']}")
                print(f"当前页用户数: {len(data['data']['items'])}")
                
                for user in data['data']['items']:
                    admin_status = "👑 管理员" if user.get('is_admin') else "👤 普通用户"
                    print(f"  - {user['username']} ({user['full_name']}) - {admin_status}")
                
                return True
            else:
                print(f"❌ 获取用户列表失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 获取用户列表异常: {e}")
            return False
    
    def search_users(self, keyword: str) -> bool:
        """搜索用户"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/users/search",
                params={"keyword": keyword},
                headers=self.headers
            )
            
            print(f"\n🔍 搜索用户 (关键词: '{keyword}')")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 搜索成功，找到 {len(data['data'])} 个用户")
                
                for user in data['data']:
                    admin_status = "👑 管理员" if user.get('is_admin') else "👤 普通用户"
                    print(f"  - {user['username']} ({user['full_name']}) - {admin_status}")
                
                return True
            else:
                print(f"❌ 搜索用户失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 搜索用户异常: {e}")
            return False
    
    def create_user(self, username: str, password: str, email: str, full_name: str, is_admin: bool = False) -> bool:
        """创建新用户"""
        try:
            user_data = {
                "username": username,
                "password": password,
                "email": email,
                "full_name": full_name,
                "is_admin": is_admin
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/users",
                json=user_data,
                headers=self.headers
            )
            
            print(f"\n➕ 创建用户 '{username}'")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                print(f"✅ 用户创建成功")
                user = data['data']
                admin_status = "👑 管理员" if user.get('is_admin') else "👤 普通用户"
                print(f"用户信息: {user['username']} ({user['full_name']}) - {admin_status}")
                return True
            else:
                print(f"❌ 创建用户失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 创建用户异常: {e}")
            return False
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """更新用户信息"""
        try:
            response = requests.put(
                f"{self.base_url}/api/v1/users/{user_id}",
                json=kwargs,
                headers=self.headers
            )
            
            print(f"\n✏️ 更新用户 ID: {user_id}")
            print(f"更新数据: {kwargs}")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 用户更新成功")
                user = data['data']
                admin_status = "👑 管理员" if user.get('is_admin') else "👤 普通用户"
                print(f"更新后信息: {user['username']} ({user['full_name']}) - {admin_status}")
                return True
            else:
                print(f"❌ 更新用户失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 更新用户异常: {e}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/v1/users/{user_id}",
                headers=self.headers
            )
            
            print(f"\n🗑️ 删除用户 ID: {user_id}")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ 用户删除成功")
                return True
            else:
                print(f"❌ 删除用户失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 删除用户异常: {e}")
            return False

def main():
    print("🚀 开始用户管理API完整测试")
    print("=" * 50)
    
    tester = UserManagementTester()
    
    # 1. 登录测试
    if not tester.login("test", "test123"):
        print("❌ 登录失败，测试终止")
        sys.exit(1)
    
    # 2. 获取用户列表
    tester.get_users()
    
    # 3. 搜索用户
    tester.search_users("test")
    
    # 4. 创建新用户
    test_user_created = tester.create_user(
        username="testuser001",
        password="password123",
        email="testuser001@example.com",
        full_name="测试用户001",
        is_admin=False
    )
    
    if test_user_created:
        # 5. 再次获取用户列表，查看新用户
        tester.get_users()
        
        # 6. 搜索新创建的用户
        tester.search_users("testuser001")
        
        # 7. 更新用户信息
        # 注意：这里假设新用户的ID是12，实际应该从创建响应中获取
        tester.update_user(12, full_name="更新后的测试用户001", is_admin=True)
        
        # 8. 再次搜索确认更新
        tester.search_users("testuser001")
        
        # 9. 删除测试用户
        tester.delete_user(12)
        
        # 10. 最终用户列表
        tester.get_users()
    
    print("\n🎉 用户管理API测试完成")

if __name__ == "__main__":
    main()