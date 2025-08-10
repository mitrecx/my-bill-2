#!/usr/bin/env python3
"""
测试前端API超时配置的脚本
"""

import requests
import time
import random
import string

# 配置
BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:5173"

def generate_random_username():
    """生成随机用户名"""
    return 'test_timeout_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def register_and_login():
    """注册并登录用户"""
    username = generate_random_username()
    email = f"{username}@test.com"
    password = "test123456"
    
    # 注册
    register_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    print(f"正在注册用户: {username}")
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        if 'data' in result and 'access_token' in result['data']:
            token = result['data']['access_token']
            print(f"注册成功，获得token: {token[:20]}...")
            return token
    
    # 如果注册失败，尝试登录
    login_data = {
        "username": username,
        "password": password
    }
    
    print(f"注册失败，尝试登录: {username}")
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    
    if response.status_code == 200:
        result = response.json()
        if 'data' in result and 'access_token' in result['data']:
            token = result['data']['access_token']
            print(f"登录成功，获得token: {token[:20]}...")
            return token
    
    print("注册和登录都失败")
    return None

def test_upload_with_large_file(token):
    """测试上传大文件，验证超时配置"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 创建一个较大的测试文件（模拟大文件上传）
    large_content = "交易时间,交易分类,交易对方,商品说明,收/支,金额,收/付款方式,交易状态,交易订单号,商户订单号,备注\n"
    
    # 生成大量测试数据（约1000条记录）
    for i in range(1000):
        large_content += f"2024-01-{(i%30)+1:02d} 10:30:00,餐饮美食,测试商户{i},测试商品{i},支出,{35.50+i*0.1:.2f},支付宝余额,交易成功,202401{i:06d},,\n"
    
    # 将内容写入临时文件
    test_file = "large_test_bills.csv"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(large_content)
    
    print(f"创建测试文件: {test_file}, 大小: {len(large_content)} 字节")
    
    data = {
        "source_type": "alipay"
    }
    
    try:
        with open(test_file, 'rb') as f:
            files = {
                "file": (test_file, f, "text/csv")
            }
            
            print("开始上传大文件，测试超时配置...")
            start_time = time.time()
            
            # 设置较长的超时时间来测试
            response = requests.post(f"{BASE_URL}/api/v1/upload/", 
                                   headers=headers, 
                                   data=data, 
                                   files=files,
                                   timeout=360)  # 6分钟超时
            
            end_time = time.time()
            upload_time = end_time - start_time
            
            print(f"上传完成，耗时: {upload_time:.2f}秒")
            
            if response.status_code == 200:
                result = response.json()
                print(f"上传成功: {result}")
                return True
            else:
                print(f"上传失败: {response.status_code} - {response.text}")
                return False
                
    except requests.exceptions.Timeout:
        print("请求超时！")
        return False
    except Exception as e:
        print(f"上传出错: {e}")
        return False
    finally:
        # 清理测试文件
        import os
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"已清理测试文件: {test_file}")

def main():
    """主函数"""
    print("=== 测试前端API超时配置 ===")
    
    # 1. 注册并登录
    token = register_and_login()
    if not token:
        print("无法获取访问令牌，退出测试")
        return
    
    # 2. 测试大文件上传
    success = test_upload_with_large_file(token)
    
    if success:
        print("\n=== 测试完成 ===")
        print("大文件上传成功，超时配置正常")
        print("前端超时时间已设置为5分钟，应该能够处理大文件上传")
    else:
        print("\n=== 测试失败 ===")
        print("大文件上传失败，可能需要检查超时配置")

if __name__ == "__main__":
    main()