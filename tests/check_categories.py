#!/usr/bin/env python3
"""
查询数据库中的分类信息
"""

import requests

def main():
    # 登录获取token
    login_data = {'username': 'testuser123', 'password': 'testpass123'}
    response = requests.post('http://127.0.0.1:8000/api/v1/auth/login', json=login_data)
    
    if response.status_code != 200:
        print("登录失败")
        return
    
    token = response.json()['data']['access_token']
    print("✅ 登录成功")

    # 获取分类列表
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get('http://127.0.0.1:8000/api/v1/bills/categories', headers=headers)
    
    print(f'分类API状态码: {response.status_code}')
    
    if response.status_code == 200:
        categories_data = response.json()
        categories = categories_data.get('data', [])
        
        print(f'分类总数: {len(categories)}')
        
        income_categories = []
        expense_categories = []
        
        for cat in categories:
            if cat.get('category_type') == 'income':
                income_categories.append(cat)
            else:
                expense_categories.append(cat)
        
        print(f"\n📊 收入类别 ({len(income_categories)}个):")
        for cat in income_categories:
            print(f"   - {cat.get('name', cat.get('category_name'))}: {cat.get('description', 'N/A')}")
        
        print(f"\n💰 支出类别 ({len(expense_categories)}个):")
        for cat in expense_categories:
            print(f"   - {cat.get('name', cat.get('category_name'))}: {cat.get('description', 'N/A')}")
    else:
        print(f'错误: {response.text}')

if __name__ == "__main__":
    main()