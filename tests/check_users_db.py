#!/usr/bin/env python3
"""
检查数据库中的用户
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import User

# 数据库连接
DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_users():
    """检查数据库中的用户"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"数据库中的用户数量: {len(users)}")
        
        for user in users:
            print(f"用户ID: {user.id}")
            print(f"用户名: {user.username}")
            print(f"邮箱: {user.email}")
            print(f"是否激活: {user.is_active}")
            print(f"创建时间: {user.created_at}")
            print("-" * 40)
            
    finally:
        db.close()

if __name__ == "__main__":
    check_users()