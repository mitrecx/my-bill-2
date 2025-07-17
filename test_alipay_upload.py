#!/usr/bin/env python3
"""
支付宝账单上传测试脚本
"""

import requests
import json
import os

# 配置
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"
FAMILY_ID = 1
FILE_PATH = "/Users/chenxing/projects/my-bills-2/bills/cashbook_record_20250705_095457.csv"

def login():
    """登录获取token"""
    login_url = f"{BASE_URL}/api/v1/auth/login"
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    print("正在登录...")
    response = requests.post(login_url, json=login_data)
    
    if response.status_code == 200:
        result = response.json()
        data = result.get("data", {})
        token = data.get("access_token")
        if token:
            print(f"登录成功，获取到token: {token[:20]}...")
            return token
        else:
            print(f"登录响应中没有access_token: {result}")
            return None
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

def upload_alipay_file(token):
    """上传支付宝文件"""
    upload_url = f"{BASE_URL}/api/v1/upload"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 检查文件是否存在
    if not os.path.exists(FILE_PATH):
        print(f"文件不存在: {FILE_PATH}")
        return None
    
    print(f"正在上传支付宝文件: {FILE_PATH}")
    
    with open(FILE_PATH, 'rb') as f:
        files = {
            'file': (os.path.basename(FILE_PATH), f, 'text/csv')
        }
        data = {
            'source_type': 'alipay',
            'family_id': FAMILY_ID
        }
        
        response = requests.post(upload_url, headers=headers, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print("文件上传成功!")
        print(f"上传ID: {result.get('upload_id')}")
        print(f"文件名: {result.get('filename')}")
        print(f"总记录数: {result.get('total_records')}")
        print(f"成功数: {result.get('success_count')}")
        print(f"创建数: {result.get('created_count')}")
        print(f"更新数: {result.get('updated_count')}")
        print(f"失败数: {result.get('failed_count')}")
        print(f"状态: {result.get('status')}")
        
        # 显示创建的账单
        created_bills = result.get('created_bills', [])
        if created_bills:
            print(f"\n创建了 {len(created_bills)} 条账单:")
            for i, bill_id in enumerate(created_bills[:5]):  # 只显示前5条
                print(f"  {i+1}. ID: {bill_id}")
            if len(created_bills) > 5:
                print(f"  ... 还有 {len(created_bills) - 5} 条账单")
        
        return result
    else:
        print(f"文件上传失败: {response.status_code}")
        print(f"错误信息: {response.text}")
        return None

def get_bills(token):
    """获取账单列表"""
    bills_url = f"{BASE_URL}/api/v1/bills"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    params = {
        "family_id": FAMILY_ID,
        "limit": 10
    }
    
    print("\n正在获取账单列表...")
    response = requests.get(bills_url, headers=headers, params=params)
    
    if response.status_code == 200:
        result = response.json()
        bills = result.get('bills', [])
        print(f"获取到 {len(bills)} 条账单:")
        
        for bill in bills:
            time_field = bill.get('transaction_time') or bill.get('created_at', 'N/A')
            desc = bill.get('description') or bill.get('transaction_desc', 'N/A')
            amount = bill.get('amount', 'N/A')
            category = bill.get('category', 'N/A')
            source = bill.get('source', 'N/A')
            
            print(f"  时间: {time_field}")
            print(f"  描述: {desc}")
            print(f"  金额: {amount}")
            print(f"  分类: {category}")
            print(f"  来源: {source}")
            print("  ---")
    else:
        print(f"获取账单失败: {response.status_code} - {response.text}")

def main():
    """主函数"""
    print("=== 支付宝账单上传测试 ===")
    
    # 1. 登录
    token = login()
    if not token:
        return
    
    # 2. 上传支付宝文件
    upload_result = upload_alipay_file(token)
    if not upload_result:
        return
    
    # 3. 查看账单
    get_bills(token)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()