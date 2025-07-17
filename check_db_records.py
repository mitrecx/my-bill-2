#!/usr/bin/env python3
"""
检查数据库中京东账单记录的脚本
"""

import sys
import os
sys.path.append('/Users/chenxing/projects/my-bills-2/backend')

from config.database import get_db
from models.bill import Bill
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_records():
    """检查数据库中的记录"""
    db = next(get_db())
    
    try:
        # 查询所有账单记录
        total_bills = db.query(Bill).count()
        print(f"数据库中总账单数: {total_bills}")
        
        # 按来源类型统计
        source_stats = db.query(
            Bill.source_type, 
            func.count(Bill.id).label('count')
        ).group_by(Bill.source_type).all()
        
        print("\n按来源类型统计:")
        for source, count in source_stats:
            print(f"  {source}: {count}条")
        
        # 查询京东账单
        jd_bills = db.query(Bill).filter(Bill.source_type == 'jd').all()
        print(f"\n京东账单数: {len(jd_bills)}")
        
        if jd_bills:
            # 按交易类型统计京东账单
            jd_type_stats = db.query(
                Bill.transaction_type,
                func.count(Bill.id).label('count')
            ).filter(Bill.source_type == 'jd').group_by(Bill.transaction_type).all()
            
            print("\n京东账单按交易类型统计:")
            for trans_type, count in jd_type_stats:
                print(f"  {trans_type}: {count}条")
            
            # 显示最近的几条京东账单
            recent_jd_bills = db.query(Bill).filter(
                Bill.source_type == 'jd'
            ).order_by(Bill.transaction_time.desc()).limit(5).all()
            
            print("\n最近5条京东账单:")
            for i, bill in enumerate(recent_jd_bills, 1):
                print(f"  {i}. ID: {bill.id}, 时间: {bill.transaction_time}, "
                      f"金额: {bill.amount}, 类型: {bill.transaction_type}, "
                      f"描述: {bill.transaction_desc[:50]}...")
            
            # 检查是否有重复记录
            duplicate_check = db.query(
                Bill.transaction_time,
                Bill.amount,
                Bill.transaction_desc,
                func.count(Bill.id).label('count')
            ).filter(
                Bill.source_type == 'jd'
            ).group_by(
                Bill.transaction_time,
                Bill.amount,
                Bill.transaction_desc
            ).having(func.count(Bill.id) > 1).all()
            
            if duplicate_check:
                print(f"\n发现重复记录: {len(duplicate_check)}组")
                for dup in duplicate_check[:3]:
                    print(f"  时间: {dup[0]}, 金额: {dup[1]}, 描述: {dup[2][:30]}..., 重复次数: {dup[3]}")
            else:
                print("\n未发现重复记录")
        
        # 检查是否有无效记录（缺少必需字段）
        invalid_bills = db.query(Bill).filter(
            (Bill.amount.is_(None)) |
            (Bill.transaction_time.is_(None)) |
            (Bill.transaction_type.is_(None))
        ).count()
        
        print(f"\n无效记录数（缺少必需字段）: {invalid_bills}")
        
    finally:
        db.close()

def main():
    check_database_records()

if __name__ == "__main__":
    main()