#!/usr/bin/env python3
"""
检查数据库中的用户数据
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database import get_db
from models.user import User

def check_users():
    """检查用户数据"""
    db = next(get_db())
    
    # 查找最近的测试用户
    users = db.query(User).filter(User.username.like('%1753080381%')).all()
    
    print("最近创建的测试用户:")
    for user in users:
        print(f"用户名: {user.username}")
        print(f"全名: {user.full_name}")
        print(f"邮箱: {user.email}")
        print("-" * 30)
    
    # 测试搜索功能
    print("\n测试搜索 'Johnson':")
    johnson_users = db.query(User).filter(User.full_name.ilike('%Johnson%')).all()
    for user in johnson_users:
        print(f"找到: {user.username} - {user.full_name}")
    
    print(f"\n搜索 'Johnson' 找到 {len(johnson_users)} 个用户")

if __name__ == "__main__":
    check_users()