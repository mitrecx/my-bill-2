#!/usr/bin/env python3
import os
import sys

# 添加backend目录到Python路径
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_dir)

from database import get_db
from models.user import User

def main():
    db = next(get_db())
    users = db.query(User).all()
    
    print("数据库中的用户信息:")
    print("=" * 50)
    
    for user in users:
        print(f'用户名: {user.username}')
        print(f'邮箱: {user.email}')
        print(f'密码哈希: {user.password_hash[:50]}...')
        print(f'是否激活: {user.is_active}')
        print(f'创建时间: {user.created_at}')
        print("-" * 30)

if __name__ == "__main__":
    main()