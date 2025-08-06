#!/usr/bin/env python3
"""
测试修改后的认证上传功能
"""

import requests
import json

def login():
    """登录获取token"""
    login_url = "http://localhost:8000/api/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(login_url, json=login_data)
    print(f"登录响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"登录成功，获取到token")
        return result.get("access_token")
    else:
        print(f"登录失败: {response.text}")
        return None

def upload_file(token):
    """上传文件"""
    upload_url = "http://localhost:8000/api/upload"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 上传京东账单文件
    with open("jd_test_unique.csv", "rb") as f:
        files = {"file": ("jd_test_unique.csv", f, "text/csv")}
        data = {"source_type": "jd"}
        
        response = requests.post(upload_url, headers=headers, files=files, data=data)
        print(f"文件上传响应状态码: {response.status_code}")
        print(f"文件上传响应内容: {response.text}")
        
        return response.status_code == 200

def main():
    print("=== 测试修改后的认证上传功能 ===")
    
    # 登录获取token
    token = login()
    if not token:
        print("登录失败，无法继续测试")
        return
    
    # 上传文件
    success = upload_file(token)
    if success:
        print("文件上传成功！")
    else:
        print("文件上传失败！")

if __name__ == "__main__":
    main()