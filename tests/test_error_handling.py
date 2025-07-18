#!/usr/bin/env python3
"""
测试前端错误处理改进
验证上传重复支付宝文件时的错误提示是否友好
"""

import requests
import json
import os
import sys

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_frontend_error_handling():
    """测试前端错误处理改进"""
    print("开始测试前端错误处理改进...")
    
    # 1. 登录获取token
    print("1. 尝试登录...")
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    login_response = requests.post(login_url, json=login_data)
    if login_response.status_code == 200:
        print("登录成功!")
        token = login_response.json()["data"]["access_token"]
    else:
        print(f"登录失败: {login_response.text}")
        return
    
    # 2. 上传重复文件测试错误处理
    print("2. 上传重复文件测试错误处理...")
    upload_url = "http://localhost:8000/api/v1/upload"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 读取测试文件
    with open("test_alipay_duplicate.csv", "rb") as f:
        files = {
            "file": ("test_alipay_duplicate.csv", f, "text/csv")
        }
        data = {
            "family_id": "1",  # 添加必需的family_id参数
            "source_type": "alipay"
        }
        
        upload_response = requests.post(upload_url, files=files, data=data, headers=headers)
        print(f"上传状态码: {upload_response.status_code}")
        
        if upload_response.status_code == 400:
            error_data = upload_response.json()
            print(f"错误响应完整内容: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            
            # 检查错误信息格式
            if "message" in error_data:
                print(f"✅ 后端返回的错误信息 (message字段): {error_data['message']}")
                
                # 验证是否是友好的中文错误提示
                expected_message = "此账单已经上传, 支付宝账单不支持重复上传!"
                if error_data["message"] == expected_message:
                    print("✅ 错误信息完全匹配预期!")
                else:
                    print(f"⚠️ 错误信息不完全匹配，预期: {expected_message}")
            else:
                print("❌ 响应中没有找到message字段")
        else:
            print(f"意外的状态码: {upload_response.status_code}")
            print(f"响应内容: {upload_response.text}")
    
    print("测试完成!")

if __name__ == "__main__":
    test_frontend_error_handling()