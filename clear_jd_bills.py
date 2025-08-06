#!/usr/bin/env python3
"""
清空数据库中的京东账单，然后重新测试上传
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from config.database import SessionLocal
from models.bill import Bill

def clear_jd_bills():
    """清空数据库中的京东账单"""
    
    print("=== 清空京东账单数据 ===\n")
    
    db = SessionLocal()
    try:
        # 查询当前京东账单数量
        jd_bills = db.query(Bill).filter(Bill.source_type == "jd").all()
        count = len(jd_bills)
        
        print(f"当前数据库中京东账单数量: {count}")
        
        if count > 0:
            # 删除所有京东账单
            deleted = db.query(Bill).filter(Bill.source_type == "jd").delete()
            db.commit()
            
            print(f"已删除 {deleted} 条京东账单记录")
        else:
            print("数据库中没有京东账单记录")
        
        # 验证删除结果
        remaining = db.query(Bill).filter(Bill.source_type == "jd").count()
        print(f"删除后剩余京东账单数量: {remaining}")
        
    except Exception as e:
        print(f"❌ 删除失败: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("\n=== 清空完成 ===")

if __name__ == "__main__":
    clear_jd_bills()