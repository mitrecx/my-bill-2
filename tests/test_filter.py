#!/usr/bin/env python3
"""
测试交易类型筛选功能
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def login():
    """登录获取token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "test", "password": "test123"}
    )
    if response.status_code == 200:
        data = response.json()
        return data["data"]["access_token"]
    else:
        print(f"登录失败: {response.text}")
        return None

def test_filter(token, transaction_type):
    """测试筛选功能"""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"transaction_type": transaction_type}
    
    response = requests.get(
        f"{BASE_URL}/bills/",
        headers=headers,
        params=params
    )
    
    if response.status_code == 200:
        data = response.json()
        bills = data["data"]["items"]
        print(f"\n筛选 {transaction_type} 类型:")
        print(f"  找到 {len(bills)} 条记录")
        if bills:
            print(f"  第一条记录: {bills[0]['transaction_desc']} - {bills[0]['amount']} - {bills[0]['transaction_type']}")
        return len(bills)
    else:
        print(f"筛选失败: {response.text}")
        return 0

def main():
    print("开始测试交易类型筛选功能...")
    
    # 登录
    token = login()
    if not token:
        return
    
    print("登录成功!")
    
    # 测试不筛选
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/bills/", headers=headers)
    if response.status_code == 200:
        total_bills = response.json()["data"]["total"]
        print(f"总账单数: {total_bills}")
    
    # 测试筛选收入
    income_count = test_filter(token, "income")
    
    # 测试筛选支出
    expense_count = test_filter(token, "expense")
    
    print(f"\n总结:")
    print(f"  收入记录: {income_count} 条")
    print(f"  支出记录: {expense_count} 条")
    print(f"  总计: {income_count + expense_count} 条")
    
    if income_count > 0 and expense_count > 0:
        print("✅ 筛选功能正常工作!")
    else:
        print("❌ 筛选功能可能存在问题")

if __name__ == "__main__":
    main()