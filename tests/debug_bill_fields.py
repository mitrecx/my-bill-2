#!/usr/bin/env python3
"""
调试账单字段值的脚本
"""

import requests
import json
from datetime import datetime

# 配置
BASE_URL = "http://127.0.0.1:8000"
TEST_USERNAME = "testuser123"
TEST_PASSWORD = "testpass123"

def login():
    """登录并获取token"""
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        if "data" in result and "access_token" in result["data"]:
            return result["data"]["access_token"]
        elif "access_token" in result:
            return result["access_token"]
        else:
            print(f"❌ 登录响应格式错误: {result}")
            return None
    else:
        print(f"❌ 登录失败: {response.status_code}")
        print(f"响应: {response.text}")
        return None

def get_bills(token):
    """获取账单列表"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/bills", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        return result["data"]["items"]
    else:
        print(f"❌ 获取账单列表失败: {response.status_code}")
        return []

def debug_bill_object(bill_id, token):
    """直接查询数据库中的账单对象"""
    import sys
    import os
    
    # 添加项目根目录到Python路径
    project_root = "/Users/chenxing/projects/my-bills-2"
    backend_root = os.path.join(project_root, "backend")
    sys.path.insert(0, project_root)
    sys.path.insert(0, backend_root)
    
    from config.database import get_db
    from models.bill import Bill, BillCategory
    from sqlalchemy.orm import joinedload
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 查询账单
        bill = db.query(Bill).options(
            joinedload(Bill.category),
            joinedload(Bill.user)
        ).filter(Bill.id == bill_id).first()
        
        if not bill:
            print(f"❌ 账单 {bill_id} 不存在")
            return
        
        print(f"🔍 账单 {bill_id} 的字段值:")
        print(f"   id: {bill.id}")
        print(f"   amount: {bill.amount}")
        print(f"   transaction_time: {bill.transaction_time}")
        print(f"   transaction_type: {bill.transaction_type}")
        print(f"   transaction_desc: {bill.transaction_desc}")
        print(f"   source_type: {bill.source_type}")
        print(f"   created_at: {bill.created_at}")
        print(f"   updated_at: {bill.updated_at}")
        print(f"   category: {bill.category}")
        
        if bill.category:
            print(f"   category.id: {bill.category.id}")
            print(f"   category.category_name: {bill.category.category_name}")
            print(f"   category.category_type: {bill.category.category_type}")
            print(f"   category.description: {bill.category.description}")
            print(f"   category.icon: {bill.category.icon}")
            print(f"   category.color: {bill.category.color}")
        else:
            print("   category: None")
        
        if bill.user:
            print(f"   user.id: {bill.user.id}")
            print(f"   user.username: {bill.user.username}")
        else:
            print("   user: None")
        
        # 尝试创建BillResponse
        print("\n🔧 尝试创建BillResponse:")
        try:
            from schemas.bills import BillResponse
            bill_response = BillResponse.from_bill(bill)
            print("✅ BillResponse创建成功")
            print(f"   transaction_date: {bill_response.transaction_date}")
            print(f"   category: {bill_response.category}")
        except Exception as e:
            print(f"❌ BillResponse创建失败: {e}")
            import traceback
            traceback.print_exc()
        
    finally:
        db.close()

def main():
    print("🔍 开始调试账单字段值")
    print("=" * 50)
    
    # 登录
    token = login()
    if not token:
        return
    
    print("✅ 登录成功")
    
    # 获取账单列表
    bills = get_bills(token)
    print(f"📊 找到 {len(bills)} 个账单")
    
    if not bills:
        print("❌ 没有找到账单")
        return
    
    # 调试前3个账单
    for i, bill in enumerate(bills[:3]):
        print(f"\n🔍 调试账单 {i+1}/{min(3, len(bills))}")
        debug_bill_object(bill["id"], token)

if __name__ == "__main__":
    main()