#!/usr/bin/env python3
"""
查看数据库中的用户，用于测试
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.orm import Session
from config.database import get_db
from models.user import User

def check_users():
    """查看数据库中的用户"""
    db = next(get_db())
    
    try:
        users = db.query(User).all()
        print(f"数据库中共有 {len(users)} 个用户:")
        
        for user in users:
            print(f"  ID: {user.id}")
            print(f"  用户名: {user.username}")
            print(f"  邮箱: {user.email}")
            print(f"  全名: {user.full_name}")
            print(f"  是否管理员: {user.is_admin}")
            print(f"  创建时间: {user.created_at}")
            print("  ---")
            
    except Exception as e:
        print(f"查询用户失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()