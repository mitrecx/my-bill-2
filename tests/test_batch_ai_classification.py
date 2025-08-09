#!/usr/bin/env python3
"""
测试批量AI分类接口
"""
import sys
import os
import requests
import json

# 添加backend目录到Python路径
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_dir)

def test_batch_ai_classification():
    """测试批量AI分类接口"""
    base_url = "http://localhost:8000"
    
    # 1. 登录获取token
    login_data = {
        "username": "test",
        "password": "test123"
    }
    
    print("=== 登录获取token ===")
    login_response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
    print(f"登录响应状态: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.text}")
        return
    
    login_result = login_response.json()
    
    # 检查登录是否成功
    if not login_result.get('success'):
        print(f"登录失败: {login_result}")
        return
    
    # 从data字段中获取access_token
    data = login_result.get('data', {})
    access_token = data.get('access_token')
    
    if not access_token:
        print(f"无法获取access_token: {login_result}")
        return
    
    print(f"获取到access_token: {access_token[:20]}...")
    
    # 2. 调用批量AI分类接口
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 测试账单ID列表（包含之前提到的JD账单）
    bill_ids = [13451, 13452, 13453]
    
    print(f"\n=== 调用批量AI分类接口 ===")
    print(f"测试账单ID: {bill_ids}")
    
    # 直接发送账单ID列表，不需要包装在对象中
    batch_response = requests.post(
        f"{base_url}/api/v1/bills/ai-classify-batch", 
        json=bill_ids, 
        headers=headers
    )
    
    print(f"批量分类响应状态: {batch_response.status_code}")
    
    if batch_response.status_code == 200:
        result = batch_response.json()
        print(f"批量分类结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"批量分类失败: {batch_response.text}")

if __name__ == "__main__":
    test_batch_ai_classification()