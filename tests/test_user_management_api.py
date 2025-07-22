#!/usr/bin/env python3
"""
用户管理API测试脚本
测试用户列表、搜索、创建、更新和删除功能
"""
import requests
import json
import sys
from typing import Optional

BASE_URL = "http://127.0.0.1:8000/api/v1"

class UserManagementTester:
    def __init__(self):
        self.access_token: Optional[str] = None
        self.headers = {"Content-Type": "application/json"}
    
    def login(self, username: str = "test", password: str = "test123") -> bool:
        """登录获取访问令牌"""
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"username": username, "password": password},
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["data"]["access_token"]
                self.headers["Authorization"] = f"Bearer {self.access_token}"
                print(f"✅ 登录成功: {username}")
                return True
            else:
                print(f"❌ 登录失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False
    
    def list_users(self, page: int = 1, size: int = 10, search: Optional[str] = None) -> bool:
        """获取用户列表"""
        try:
            params = {"page": page, "size": size}
            if search:
                params["search"] = search
            
            response = requests.get(
                f"{BASE_URL}/users",
                params=params,
                headers=self.headers
            )
            
            print(f"\\n📋 用户列表 (页码: {page}, 大小: {size}" + (f", 搜索: {search}" if search else "") + ")")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                users_data = data["data"]
                print(f"总用户数: {users_data['total']}")
                print(f"当前页: {users_data['page']}/{users_data['pages']}")
                print("用户列表:")
                for user in users_data["items"]:
                    print(f"  - ID: {user['id']}, 用户名: {user['username']}, "
                          f"姓名: {user['full_name']}, 邮箱: {user['email']}, "
                          f"激活: {user['is_active']}")
                return True
            else:
                print(f"❌ 获取用户列表失败: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 获取用户列表异常: {e}")
            return False
    
    def search_users(self, search_term: str) -> bool:
        """搜索用户"""
        print(f"\\n🔍 搜索用户: '{search_term}'")
        return self.list_users(search=search_term)
    
    def create_user(self, username: str, password: str, full_name: str, email: str) -> bool:
        """创建新用户"""
        try:
            user_data = {
                "username": username,
                "password": password,
                "full_name": full_name,
                "email": email
            }
            
            response = requests.post(
                f"{BASE_URL}/users",
                json=user_data,
                headers=self.headers
            )
            
            print(f"\\n➕ 创建用户: {username}")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                user = data["data"]
                print(f"✅ 用户创建成功: ID {user['id']}, 用户名: {user['username']}")
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
                f"{BASE_URL}/users/{user_id}",
                json=kwargs,
                headers=self.headers
            )
            
            print(f"\\n✏️ 更新用户 ID {user_id}")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                user = data["data"]
                print(f"✅ 用户更新成功: {user['username']}")
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
                f"{BASE_URL}/users/{user_id}",
                headers=self.headers
            )
            
            print(f"\\n🗑️ 删除用户 ID {user_id}")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 用户删除成功: {data['data']}")
                return True
            else:
                print(f"❌ 删除用户失败: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 删除用户异常: {e}")
            return False
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 开始用户管理API综合测试")
        print("=" * 50)
        
        # 1. 登录
        if not self.login():
            print("❌ 登录失败，测试终止")
            return False
        
        # 2. 获取用户列表
        print("\\n" + "=" * 50)
        self.list_users()
        
        # 3. 搜索用户
        print("\\n" + "=" * 50)
        self.search_users("test")
        
        # 4. 创建新用户
        print("\\n" + "=" * 50)
        test_username = f"test_user_{int(__import__('time').time())}"
        created = self.create_user(
            username=test_username,
            password="password123",
            full_name="测试用户",
            email=f"{test_username}@example.com"
        )
        
        if created:
            # 5. 再次获取用户列表，查看新用户
            print("\\n" + "=" * 50)
            self.list_users()
            
            # 6. 搜索新创建的用户
            print("\\n" + "=" * 50)
            self.search_users(test_username)
        
        print("\\n" + "=" * 50)
        print("🎉 用户管理API测试完成")

def main():
    tester = UserManagementTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()