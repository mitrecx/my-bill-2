#!/usr/bin/env python3
"""
测试搜索API的序列化过程
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from pydantic import BaseModel
from typing import List, Optional
from schemas.common import ApiResponse
import json

# 复制UserSearchResponse模型定义
class UserSearchResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    email: str  # 移除Optional，确保email字段总是被包含
    
    class Config:
        from_attributes = True

# 模拟用户数据
class MockUser:
    def __init__(self, id, username, full_name, email):
        self.id = id
        self.username = username
        self.full_name = full_name
        self.email = email

def test_serialization():
    print("=== 测试序列化过程 ===")
    
    # 创建模拟用户
    user = MockUser(1, "bob", "Bob Smith", "bob@example.com")
    
    # 测试UserSearchResponse序列化
    print("1. 测试UserSearchResponse序列化:")
    user_response = UserSearchResponse.model_validate(user)
    print(f"   序列化结果: {user_response.model_dump()}")
    print(f"   JSON: {user_response.model_dump_json()}")
    
    # 测试ApiResponse序列化
    print("\n2. 测试ApiResponse序列化:")
    api_response = ApiResponse[List[UserSearchResponse]](
        success=True,
        data=[user_response],
        message="找到 1 个用户"
    )
    print(f"   序列化结果: {api_response.model_dump()}")
    print(f"   JSON: {api_response.model_dump_json()}")
    
    # 测试exclude_none参数
    print("\n3. 测试exclude_none参数:")
    print(f"   exclude_none=False: {api_response.model_dump(exclude_none=False)}")
    print(f"   exclude_none=True: {api_response.model_dump(exclude_none=True)}")
    
    # 测试None值的情况
    print("\n4. 测试None值情况:")
    user_with_none = MockUser(2, "alice", None, "alice@example.com")
    user_response_none = UserSearchResponse.model_validate(user_with_none)
    print(f"   有None值的序列化: {user_response_none.model_dump()}")
    print(f"   exclude_none=True: {user_response_none.model_dump(exclude_none=True)}")

if __name__ == "__main__":
    test_serialization()