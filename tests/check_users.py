#!/usr/bin/env python3
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from backend.database import get_db
from backend.models.user import User

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