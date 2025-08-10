#!/usr/bin/env python3
"""
测试优化后的支付宝账单上传性能
"""

import requests
import time
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000/api/v1"

def register_user(username, email, password):
    """注册用户"""
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    return response

def login_user(username, password):
    """用户登录"""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": password
    })
    return response

def upload_file(file_path, access_token, auto_categorize=True):
    """上传文件"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {'auto_categorize': auto_categorize}
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/upload/", 
                               headers=headers, 
                               files=files, 
                               data=data,
                               timeout=300)  # 300秒超时（5分钟）
        end_time = time.time()
        
        return response, end_time - start_time

def main():
    # 测试用户信息
    username = "testuser_optimized"
    email = "testoptimized@example.com"
    password = "testpassword123"
    
    print("=== 测试优化后的支付宝账单上传性能 ===")
    
    # 注册用户
    print("1. 注册用户...")
    register_response = register_user(username, email, password)
    if register_response.status_code == 200:
        print("✓ 用户注册成功")
        # 如果注册成功，直接使用返回的token
        access_token = register_response.json()["data"]["access_token"]
        print("✓ 直接使用注册返回的token")
    elif register_response.status_code == 400:
        print("⚠ 用户已存在，继续登录")
        # 登录用户
        print("2. 用户登录...")
        login_response = login_user(username, password)
        if login_response.status_code == 200:
            access_token = login_response.json()["data"]["access_token"]
            print("✓ 用户登录成功")
        else:
            print(f"✗ 用户登录失败: {login_response.status_code} - {login_response.text}")
            return
    else:
        print(f"✗ 用户注册失败: {register_response.status_code} - {register_response.text}")
        return
    
    # 检查大文件是否存在
    large_file_path = "large_alipay_bills.csv"
    if not os.path.exists(large_file_path):
        print(f"✗ 大文件 {large_file_path} 不存在，请先运行 test_large_alipay_bills.py 生成文件")
        return
    
    file_size = os.path.getsize(large_file_path)
    print(f"文件大小: {file_size} 字节")
    
    # 测试1: 上传大文件（开启AI分类）
    print("\n3. 测试上传大文件（开启AI分类）...")
    try:
        response1, duration1 = upload_file(large_file_path, access_token, auto_categorize=True)
        print(f"状态码: {response1.status_code}")
        print(f"耗时: {duration1:.2f} 秒")
        if response1.status_code == 200:
            result = response1.json()
            print(f"✓ 上传成功 - 处理了 {result.get('processed_count', 0)} 条记录")
        else:
            print(f"✗ 上传失败: {response1.text}")
    except requests.exceptions.Timeout:
        print("✗ 上传超时（300秒）")
    except Exception as e:
        print(f"✗ 上传出错: {e}")
    
    # 等待一下
    time.sleep(2)
    
    # 测试2: 再次上传同一文件（测试按日期覆盖逻辑的性能）
    print("\n4. 测试再次上传同一文件（测试按日期覆盖逻辑）...")
    try:
        response2, duration2 = upload_file(large_file_path, access_token, auto_categorize=False)
        print(f"状态码: {response2.status_code}")
        print(f"耗时: {duration2:.2f} 秒")
        if response2.status_code == 200:
            result = response2.json()
            print(f"✓ 上传成功 - 处理了 {result.get('processed_count', 0)} 条记录")
            print(f"删除了 {result.get('deleted_count', 0)} 条重复记录")
        else:
            print(f"✗ 上传失败: {response2.text}")
    except requests.exceptions.Timeout:
        print("✗ 上传超时（300秒）")
    except Exception as e:
        print(f"✗ 上传出错: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()