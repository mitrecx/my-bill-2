#!/usr/bin/env python3
"""
验证JD账单导入修复是否生效
检查新创建的账单是否正确包含了category信息
"""

import requests
import json

def main():
    # 1. 登录获取token
    print("正在登录...")
    login_data = {
        "username": "chenxing",
        "password": "123456"
    }
    
    login_response = requests.post("http://localhost:8000/api/v1/auth/login", json=login_data)
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("登录成功")
    
    # 2. 获取最新创建的JD账单
    print("\n正在获取最新的JD账单...")
    bills_response = requests.get(
        "http://localhost:8000/api/v1/bills?source_type=jd&page=1&size=10&sort_by=created_at&sort_order=desc",
        headers=headers
    )
    
    if bills_response.status_code != 200:
        print(f"获取账单失败: {bills_response.status_code}")
        return
    
    bills_data = bills_response.json()
    bills = bills_data.get("data", [])
    
    if not bills:
        print("没有找到JD账单")
        return
    
    print(f"找到 {len(bills)} 个JD账单")
    
    # 3. 检查最新的3个账单（刚刚创建的）
    target_ids = [13597, 13598, 13599]
    
    for bill in bills[:3]:  # 检查最新的3个账单
        bill_id = bill.get("id")
        if bill_id in target_ids:
            print(f"\n=== 账单 ID: {bill_id} ===")
            print(f"交易描述: {bill.get('transaction_desc')}")
            print(f"金额: {bill.get('amount')}")
            print(f"AI分类: {bill.get('ai_category')}")
            print(f"原始数据: {json.dumps(bill.get('raw_data', {}), ensure_ascii=False, indent=2)}")
            
            # 检查raw_data中是否包含category信息
            raw_data = bill.get('raw_data', {})
            if 'category' in raw_data:
                print(f"✅ 原始分类信息已保存: {raw_data['category']}")
            else:
                print("❌ 原始分类信息缺失")

if __name__ == "__main__":
    main()