#!/usr/bin/env python3
"""
测试京东文件上传和分类功能的脚本
"""
import requests
import json
import sys
import os

# 配置
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
FAMILY_ID = 1
JD_FILE_PATH = "/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"

def login():
    """登录获取token"""
    url = f"{BASE_URL}/auth/login"
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        result = response.json()
        return result["data"]["access_token"]
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

def upload_file(token):
    """上传京东文件"""
    url = f"{BASE_URL}/upload/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    if not os.path.exists(JD_FILE_PATH):
        print(f"文件不存在: {JD_FILE_PATH}")
        return None
    
    with open(JD_FILE_PATH, 'rb') as f:
        files = {
            'file': (os.path.basename(JD_FILE_PATH), f, 'text/csv')
        }
        data = {
            'family_id': FAMILY_ID
        }
        
        response = requests.post(url, headers=headers, files=files, data=data)
        
    return response

def get_bills(token):
    """获取账单列表"""
    url = f"{BASE_URL}/bills"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "family_id": FAMILY_ID,
        "source_type": "jd",
        "page": 1,
        "size": 5
    }
    
    response = requests.get(url, headers=headers, params=params)
    return response

def main():
    print("开始测试京东文件上传和分类功能...")
    
    # 1. 登录
    print("1. 登录...")
    token = login()
    if not token:
        sys.exit(1)
    print("登录成功!")
    
    # 2. 上传文件
    print("2. 上传京东文件...")
    upload_response = upload_file(token)
    if upload_response.status_code == 200:
        result = upload_response.json()
        print("上传成功!")
        print(f"处理结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print(f"上传失败: {upload_response.status_code} - {upload_response.text}")
        return
    
    # 3. 查看账单
    print("3. 查看京东账单...")
    bills_response = get_bills(token)
    if bills_response.status_code == 200:
        bills_data = bills_response.json()
        print("账单查询成功!")
        
        if bills_data.get("data", {}).get("items"):
            for bill in bills_data["data"]["items"][:5]:  # 只显示前5条
                category_name = "未分类"
                if bill.get("category"):
                    category_name = bill["category"].get("category_name", "未分类")
                
                print(f"- 时间: {bill.get('transaction_time', bill.get('created_at', '未知'))}")
                print(f"- 描述: {bill.get('transaction_desc', bill.get('description', '无描述'))}")
                print(f"- 金额: {bill.get('amount', 0)}")
                print(f"- 分类: {category_name}")
                print(f"- 来源: {bill.get('source_type', '未知')}")
                print("---")
        else:
            print("没有找到京东账单")
    else:
        print(f"查询账单失败: {bills_response.status_code} - {bills_response.text}")

if __name__ == "__main__":
    main()