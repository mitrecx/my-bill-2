#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证支付宝账单导入修复效果
检查新创建的账单是否正确包含分类信息
"""

import requests
import json

def verify_alipay_bills():
    """验证支付宝账单的修复效果"""
    
    # API基础URL
    base_url = "http://localhost:8000/api/v1"
    
    # 1. 登录获取token
    login_data = {
        "username": "test",
        "password": "test123"
    }
    
    print("正在登录...")
    response = requests.post(f"{base_url}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ 登录失败: {response.status_code}")
        return False
    
    login_result = response.json()
    if not login_result.get('success'):
        print(f"❌ 登录失败: {login_result.get('message')}")
        return False
    
    token = login_result['data']['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print("✅ 登录成功")
    
    # 2. 检查最新创建的支付宝账单 (IDs: 14216, 14217, 14218)
    bill_ids = [14216, 14217, 14218]
    
    print(f"\n检查支付宝账单 {bill_ids}...")
    
    for bill_id in bill_ids:
        try:
            # 获取账单详情
            response = requests.get(f"{base_url}/bills/{bill_id}", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    bill = result['data']
                    
                    print(f"\n账单ID: {bill_id}")
                    print(f"交易描述: {bill.get('transaction_desc', 'N/A')}")
                    print(f"分类: {bill.get('category_name', 'N/A')}")
                    print(f"AI分类: {bill.get('ai_category_name', 'N/A')}")
                    
                    # 检查raw_data中的分类信息
                    raw_data = bill.get('raw_data', {})
                    if raw_data:
                        print(f"原始数据:")
                        for key, value in raw_data.items():
                            print(f"  {key}: {value}")
                        
                        # 检查是否包含分类信息
                        if 'category' in raw_data:
                            print(f"✅ 包含分类信息: {raw_data['category']}")
                        else:
                            print("❌ 缺少分类信息")
                    else:
                        print("❌ 没有原始数据")
                        
                else:
                    print(f"❌ 获取账单 {bill_id} 失败: {result.get('message')}")
            else:
                print(f"❌ 请求账单 {bill_id} 失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 处理账单 {bill_id} 时出错: {str(e)}")
    
    return True

if __name__ == "__main__":
    verify_alipay_bills()