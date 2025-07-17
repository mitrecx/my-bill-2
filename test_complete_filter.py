#!/usr/bin/env python3
"""
测试完整的交易类型筛选功能（包括不计收支）
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
    params = {"transaction_type": transaction_type, "page_size": 200}  # 增加页面大小
    
    response = requests.get(
        f"{BASE_URL}/bills/",
        headers=headers,
        params=params
    )
    
    if response.status_code == 200:
        data = response.json()
        bills = data["data"]["items"]
        total = data["data"]["total"]
        print(f"\n筛选 {transaction_type} 类型:")
        print(f"  找到 {len(bills)} 条记录 (总计: {total})")
        if bills:
            print(f"  第一条记录: {bills[0]['transaction_desc']} - {bills[0]['amount']} - {bills[0]['transaction_type']}")
        return total  # 返回总数而不是当前页数量
    else:
        print(f"筛选失败: {response.text}")
        return 0

def main():
    print("开始测试完整的交易类型筛选功能...")
    
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
    
    # 测试筛选各种类型
    income_count = test_filter(token, "income")
    expense_count = test_filter(token, "expense")
    transfer_count = test_filter(token, "transfer")
    
    print(f"\n总结:")
    print(f"  收入记录: {income_count} 条")
    print(f"  支出记录: {expense_count} 条")
    print(f"  不计收支记录: {transfer_count} 条")
    print(f"  三种类型总计: {income_count + expense_count + transfer_count} 条")
    print(f"  数据库总记录: {total_bills} 条")
    
    if income_count + expense_count + transfer_count == total_bills:
        print("✅ 筛选功能完全正常！所有类型记录数之和等于总记录数")
    else:
        print("❌ 筛选功能可能存在问题，记录数不匹配")

if __name__ == "__main__":
    main()