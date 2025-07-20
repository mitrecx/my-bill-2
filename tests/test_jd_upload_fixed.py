#!/usr/bin/env python3
"""
测试京东账单上传修复后的效果
"""

import requests
import json
import os

# 配置
API_BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{API_BASE_URL}/api/v1/auth/login"
UPLOAD_URL = f"{API_BASE_URL}/api/v1/upload/"

# 测试用户凭据
USERNAME = "testuser"
PASSWORD = "password123"

def login():
    """登录获取访问令牌"""
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(LOGIN_URL, json=login_data, headers=headers)
    if response.status_code == 200:
        token_data = response.json()
        return token_data["data"]["access_token"]
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

def upload_jd_bills(token):
    """上传京东账单文件"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 京东账单文件路径
    file_path = "/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return None
    
    # 准备文件上传
    with open(file_path, 'rb') as f:
        files = {
            'file': (os.path.basename(file_path), f, 'text/csv')
        }
        data = {
            'source_type': 'jd',
            'auto_categorize': 'true'
        }
        
        print(f"正在上传京东账单文件: {os.path.basename(file_path)}")
        response = requests.post(UPLOAD_URL, files=files, data=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("上传成功!")
            print(f"文件名: {result['filename']}")
            print(f"总记录数: {result['total_records']}")
            print(f"成功记录数: {result['success_count']}")
            print(f"新增记录数: {result['created_count']}")
            print(f"更新记录数: {result['updated_count']}")
            print(f"失败记录数: {result['failed_count']}")
            print(f"状态: {result['status']}")
            
            if result.get('warnings'):
                print(f"警告: {result['warnings']}")
            
            if result.get('errors'):
                print(f"错误: {result['errors']}")
            
            return result
        else:
            print(f"上传失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None

def main():
    print("=== 测试京东账单上传修复效果 ===")
    
    # 登录
    print("1. 正在登录...")
    token = login()
    if not token:
        print("登录失败，测试终止")
        return
    
    print("登录成功!")
    
    # 上传京东账单
    print("\n2. 正在上传京东账单...")
    result = upload_jd_bills(token)
    
    if result:
        print("\n=== 测试结果 ===")
        total_processed = result['success_count']
        expected_total = 123  # 预期的总记录数
        
        if total_processed == expected_total:
            print(f"✅ 成功！所有 {expected_total} 条记录都已处理")
        else:
            print(f"❌ 问题：只处理了 {total_processed} 条记录，预期 {expected_total} 条")
            
        if result['failed_count'] == 0:
            print("✅ 没有失败记录")
        else:
            print(f"❌ 有 {result['failed_count']} 条记录失败")

if __name__ == "__main__":
    main()