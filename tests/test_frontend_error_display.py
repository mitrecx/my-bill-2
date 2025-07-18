#!/usr/bin/env python3
"""
测试前端错误处理显示
模拟前端的错误处理逻辑，验证是否能正确提取和显示后端返回的错误信息
"""

import requests
import json

def simulate_frontend_error_handling():
    """模拟前端错误处理逻辑"""
    print("🧪 模拟前端错误处理逻辑测试...")
    
    # 1. 登录获取token
    print("1. 登录...")
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    login_response = requests.post(login_url, json=login_data)
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.text}")
        return
    
    token = login_response.json()["data"]["access_token"]
    print("✅ 登录成功!")
    
    # 2. 模拟上传重复文件
    print("2. 模拟上传重复支付宝文件...")
    upload_url = "http://localhost:8000/api/v1/upload"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open("test_alipay_duplicate.csv", "rb") as f:
        files = {
            "file": ("test_alipay_duplicate.csv", f, "text/csv")
        }
        data = {
            "family_id": "1",
            "source_type": "alipay"
        }
        
        try:
            upload_response = requests.post(upload_url, files=files, data=data, headers=headers)
            
            # 模拟前端的错误处理逻辑
            if upload_response.status_code != 200:
                print(f"📤 收到错误响应，状态码: {upload_response.status_code}")
                
                # 这里模拟前端UploadPage.tsx中的错误处理逻辑
                error_data = upload_response.json()
                print(f"📋 完整错误响应: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
                
                # 模拟前端的错误信息提取逻辑
                # 后端使用ApiResponse格式，错误信息在message字段中
                error_message = (error_data.get('message') or 
                               error_data.get('detail') or 
                               '上传失败')
                
                print(f"💬 前端将显示的错误信息: '{error_message}'")
                
                # 验证错误信息是否友好
                expected_message = "此账单已经上传, 支付宝账单不支持重复上传!"
                if error_message == expected_message:
                    print("✅ 成功！前端将显示友好的中文错误提示")
                    print("✅ 错误处理改进验证通过！")
                else:
                    print(f"❌ 错误信息不匹配")
                    print(f"   期望: {expected_message}")
                    print(f"   实际: {error_message}")
            else:
                print(f"⚠️ 意外的成功响应: {upload_response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    simulate_frontend_error_handling()