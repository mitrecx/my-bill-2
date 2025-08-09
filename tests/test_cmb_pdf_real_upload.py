#!/usr/bin/env python3
"""
测试真实的招商银行PDF文件上传
"""

import requests
import json
import os

BASE_URL = "http://127.0.0.1:8000/api/v1"
PDF_FILE_PATH = "/Users/chenxing/projects/my-bills-2/bills/招商银行交易流水(申请时间2025年07月05日10时27分05秒).pdf"

def login():
    """用户登录"""
    login_data = {
        "username": "admin",
        "password": "123456"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("✓ 用户登录成功")
            return result["data"]["access_token"]
        else:
            print(f"✗ 登录失败: {result.get('message')}")
            return None
    else:
        print(f"✗ 登录请求失败: {response.status_code} - {response.text}")
        return None

def upload_cmb_pdf(token):
    """上传招商银行PDF文件"""
    if not os.path.exists(PDF_FILE_PATH):
        print(f"✗ PDF文件不存在: {PDF_FILE_PATH}")
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"正在上传文件: {PDF_FILE_PATH}")
    
    try:
        # 上传文件
        with open(PDF_FILE_PATH, 'rb') as f:
            files = {
                'file': ('招商银行交易流水.pdf', f, 'application/pdf')
            }
            data = {
                'parser_type': 'cmb'
            }
            
            response = requests.post(f"{BASE_URL}/upload/", files=files, data=data, headers=headers)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            # 检查是否有upload_id或者success_count字段
            if result.get("success_count") is not None or result.get("upload_id") is not None:
                print("✓ 文件上传成功")
                print(f"解析结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return result
            else:
                print(f"✗ 文件上传失败: {result.get('message')}")
                return None
        else:
            print(f"✗ 文件上传请求失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ 文件上传异常: {e}")
        return None

def get_recent_bills(token, limit=10):
    """获取最近的账单"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/bills?limit={limit}&offset=0", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            # 检查数据结构
            data = result.get("data", {})
            if isinstance(data, list):
                bills = data
            elif isinstance(data, dict) and "bills" in data:
                bills = data["bills"]
            elif isinstance(data, dict) and "items" in data:
                bills = data["items"]
            else:
                print(f"意外的数据结构: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return []
            
            print(f"\n=== 最近 {len(bills)} 条账单 ===")
            for bill in bills:
                # 打印账单的所有字段以便调试
                print(f"账单字段: {list(bill.keys())}")
                print(f"ID: {bill['id']}, 时间: {bill.get('transaction_time', bill.get('created_at', 'N/A'))}, "
                      f"金额: {bill.get('amount', 'N/A')}, 类型: {bill.get('transaction_type', 'N/A')}, "
                      f"描述: {bill.get('transaction_desc', 'N/A')}, 来源: {bill.get('source_type', 'N/A')}")
            return bills
        else:
            print(f"✗ 获取账单失败: {result.get('message')}")
            return []
    else:
        print(f"✗ 获取账单请求失败: {response.status_code} - {response.text}")
        return []

def main():
    print("=== 测试招商银行PDF文件上传 ===")
    
    # 1. 用户登录
    token = login()
    if not token:
        return
    
    # 2. 获取上传前的账单数量
    print("\n--- 上传前的账单 ---")
    bills_before = get_recent_bills(token, 5)
    
    # 3. 上传PDF文件
    print("\n--- 上传PDF文件 ---")
    upload_result = upload_cmb_pdf(token)
    
    if upload_result:
        # 4. 获取上传后的账单
        print("\n--- 上传后的账单 ---")
        bills_after = get_recent_bills(token, 20)
        
        # 5. 分析新增的账单
        if bills_after:
            new_bills = []
            before_ids = {bill['id'] for bill in bills_before}
            
            for bill in bills_after:
                if bill['id'] not in before_ids:
                    new_bills.append(bill)
            
            print(f"\n=== 新增了 {len(new_bills)} 条账单 ===")
            for bill in new_bills:
                print(f"ID: {bill['id']}")
                print(f"  时间: {bill.get('transaction_date', bill.get('created_at', 'N/A'))}")
                print(f"  金额: {bill.get('amount', 'N/A')}")
                print(f"  类型: {bill.get('transaction_type', 'N/A')}")
                print(f"  描述: {bill.get('transaction_desc', 'N/A')}")

                print(f"  来源: {bill.get('source_type', 'N/A')}")
                print(f"  分类: {bill.get('category', {}).get('category_name', '未分类') if isinstance(bill.get('category'), dict) else '未分类'}")
                print("---")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()