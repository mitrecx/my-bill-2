#!/usr/bin/env python3
"""
测试支付宝账单记录级别不去重功能
"""

import requests
import json
import os
from datetime import datetime

# API配置
BASE_URL = "http://localhost:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login"
UPLOAD_URL = f"{BASE_URL}/upload/"

# 测试用户凭据
USERNAME = "admin"
PASSWORD = "admin123"

def login():
    """登录并获取token"""
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(LOGIN_URL, json=login_data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        data = result.get("data", {})
        token = data.get("access_token")
        if token:
            return token
        else:
            print(f"登录响应中没有access_token: {result}")
            return None
    else:
        print(f"登录失败: {response.status_code}")
        print(response.text)
        return None

def test_duplicate_records():
    """测试支付宝账单相同记录不去重"""
    print("=== 支付宝账单记录级别不去重测试 ===")
    
    # 登录
    print("正在登录...")
    token = login()
    if not token:
        return
    
    print(f"登录成功，获取到token: {token[:20]}...")
    
    # 准备请求头
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 创建测试CSV文件，包含两条完全相同的记录
    test_csv_content = """记录时间,分类,收支类型,金额,备注,账户,来源,标签,
2024-07-05 10:30:00,餐饮美食,支出,35.50,麦当劳-巨无霸套餐,支付宝余额,,,
2024-07-05 10:30:00,餐饮美食,支出,35.50,麦当劳-巨无霸套餐,支付宝余额,,,"""
    
    # 创建测试CSV文件（使用带时间戳的文件名避免文件级别重复检查）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_file_name = f"test_duplicate_records_{timestamp}.csv"
    test_file_path = f"/tmp/{test_file_name}"
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_csv_content)
    
    try:
        # 上传文件
        print(f"正在上传测试文件: {test_file_path}")
        
        with open(test_file_path, 'rb') as f:
            files = {
                'file': (test_file_name, f, 'text/csv')
            }
            data = {
                'family_id': 1,
                'source_type': 'alipay',
                'auto_categorize': True
            }
            
            response = requests.post(UPLOAD_URL, files=files, data=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("文件上传成功!")
            print(f"总记录数: {result['total_records']}")
            print(f"成功数: {result['success_count']}")
            print(f"创建数: {result['created_count']}")
            print(f"更新数: {result['updated_count']}")
            print(f"失败数: {result['failed_count']}")
            print(f"状态: {result['status']}")
            
            if result['success_count'] == 2:
                print("✓ 测试通过：支付宝账单相同记录被正确处理为两笔独立交易")
            else:
                print("✗ 测试失败：支付宝账单相同记录被错误去重")
                
        else:
            print(f"文件上传失败: {response.status_code}")
            print(response.text)
            
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    test_duplicate_records()