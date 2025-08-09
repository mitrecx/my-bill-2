#!/usr/bin/env python3
"""
检查账单列表和AI分类结果
"""

import requests
import json

def main():
    # 登录获取token
    login_data = {'username': 'testuser123', 'password': 'testpass123'}
    response = requests.post('http://127.0.0.1:8000/api/v1/auth/login', json=login_data)
    
    if response.status_code != 200:
        print("登录失败")
        return
    
    token = response.json()['data']['access_token']
    print("✅ 登录成功")

    # 获取账单列表
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get('http://127.0.0.1:8000/api/v1/bills/', headers=headers)
    
    print(f'账单列表API状态码: {response.status_code}')
    
    if response.status_code == 200:
        bills_data = response.json()
        
        # 从正确的字段获取账单列表
        bills = bills_data.get('data', {}).get('items', [])
        total = bills_data.get('data', {}).get('total', 0)
        
        print(f'账单总数: {total}')
        print(f'当前页账单数量: {len(bills)}')
        
        if bills:
            print("\n📊 最近的账单和AI分类结果:")
            for i, bill in enumerate(bills):
                category_name = '未分类'
                if bill.get('category'):
                    if isinstance(bill['category'], dict):
                        category_name = bill['category'].get('name', '未分类')
                    else:
                        category_name = str(bill['category'])
                
                print(f"   {i+1}. 账单ID: {bill.get('id')}")
                print(f"      描述: {bill.get('transaction_desc', 'N/A')}")
                print(f"      金额: {bill.get('amount', 'N/A')}")
                print(f"      类型: {bill.get('transaction_type', 'N/A')}")
                print(f"      分类: {category_name}")
                print(f"      时间: {bill.get('transaction_date', 'N/A')}")
                print()
        else:
            print("没有找到账单")
    else:
        print(f'错误: {response.text}')

if __name__ == "__main__":
    main()