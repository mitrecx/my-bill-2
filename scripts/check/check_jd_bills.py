#!/usr/bin/env python3
"""
检查数据库中的京东账单记录
"""

import sys
import os

# 添加backend目录到Python路径
sys.path.append('/Users/chenxing/projects/my-bills-2/backend')

from config.database import SessionLocal
from models.bill import Bill

def check_jd_bills():
    """检查数据库中的京东账单"""
    
    print("=== 数据库京东账单检查 ===")
    
    try:
        db = SessionLocal()
        
        # 查看所有source_type的值
        print("1. 所有source_type值:")
        source_types = db.query(Bill.source_type).distinct().all()
        for st in source_types:
            count = db.query(Bill).filter(Bill.source_type == st[0]).count()
            print(f"   {st[0]}: {count}条")
        
        # 查看所有source_filename包含"京东"的记录
        print("\n2. 包含'京东'的source_filename:")
        jd_files = db.query(Bill.source_filename).filter(
            Bill.source_filename.like('%京东%')
        ).distinct().all()
        
        for jf in jd_files:
            if jf[0]:
                count = db.query(Bill).filter(Bill.source_filename == jf[0]).count()
                source_type = db.query(Bill.source_type).filter(Bill.source_filename == jf[0]).first()
                print(f"   文件: {jf[0]}")
                print(f"   记录数: {count}")
                print(f"   source_type: {source_type[0] if source_type else 'None'}")
                print()
        
        # 查看最近的几条记录
        print("3. 最近的5条记录:")
        recent_bills = db.query(Bill).order_by(Bill.created_at.desc()).limit(5).all()
        for bill in recent_bills:
            print(f"   ID: {bill.id}, source_type: {bill.source_type}, filename: {bill.source_filename}")
        
        db.close()
        
    except Exception as e:
        print(f"数据库查询错误: {e}")

if __name__ == "__main__":
    check_jd_bills()