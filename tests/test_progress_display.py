#!/usr/bin/env python3
"""
测试进度显示功能
"""

import requests
import time
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_progress_display():
    """测试进度显示功能"""
    
    # API配置
    base_url = "http://127.0.0.1:8000"
    
    # 测试用户信息
    test_user = {
        "username": "progress_test_user",
        "email": "progress_test@example.com",
        "password": "test123456"
    }
    
    print("🚀 开始测试进度显示功能")
    
    try:
        # 1. 用户注册
        print("\n📝 步骤1: 用户注册")
        register_response = requests.post(
            f"{base_url}/api/v1/auth/register",
            json=test_user,
            timeout=30
        )
        
        if register_response.status_code in [200, 201]:
            print("✓ 用户注册成功")
        elif register_response.status_code == 400 and ("已被注册" in register_response.text or "already exists" in register_response.text):
            print("✓ 用户已存在，继续测试")
        else:
            print(f"❌ 用户注册失败: {register_response.status_code} - {register_response.text}")
            return False
        
        # 2. 用户登录
        print("\n🔑 步骤2: 用户登录")
        login_response = requests.post(
            f"{base_url}/api/v1/auth/login",
            json={"username": test_user["username"], "password": test_user["password"]},
            timeout=30
        )
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code} - {login_response.text}")
            return False
        
        login_data = login_response.json()
        token = login_data["data"]["access_token"]
        print("✓ 登录成功")
        
        # 3. 准备测试文件
        print("\n📄 步骤3: 准备测试文件")
        test_file_path = "/Users/chenxing/projects/my-bills-2/test_progress.csv"
        
        if not os.path.exists(test_file_path):
            print(f"❌ 测试文件不存在: {test_file_path}")
            return False
        
        print(f"✓ 测试文件准备完成: {test_file_path}")
        
        # 4. 上传文件测试
        print("\n📤 步骤4: 上传文件测试")
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        with open(test_file_path, 'rb') as f:
            files = {
                'file': ('test_progress.csv', f, 'text/csv')
            }
            data = {
                'auto_categorize': 'true',
                'source_type': 'alipay'  # 指定为支付宝账单类型
            }
            
            print("正在上传文件...")
            start_time = time.time()
            
            upload_response = requests.post(
                f"{base_url}/api/v1/upload/",
                files=files,
                data=data,
                headers=headers,
                timeout=300
            )
            
            end_time = time.time()
            upload_duration = end_time - start_time
        
        if upload_response.status_code == 200:
            result = upload_response.json()
            print(f"✓ 上传成功 - 耗时: {upload_duration:.2f}秒")
            print(f"  - 成功处理: {result.get('data', {}).get('success_count', 0)} 条记录")
            print(f"  - AI分类: {result.get('data', {}).get('ai_classified_count', 0)} 条记录")
            return True
        else:
            print(f"❌ 上传失败: {upload_response.status_code} - {upload_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = test_progress_display()
    if success:
        print("\n🎉 进度显示功能测试完成！")
        print("\n💡 提示: 请在浏览器中访问 http://localhost:5173 查看前端进度显示效果")
    else:
        print("\n❌ 测试失败")
    
    sys.exit(0 if success else 1)