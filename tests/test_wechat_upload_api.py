#!/usr/bin/env python3
"""
测试微信账单上传API
"""

import requests
import os
import json

def get_auth_token():
    """获取认证token"""
    base_url = "http://localhost:8000/api/v1"
    
    # 尝试登录获取token
    login_data = {
        "username": "test",  # 使用已存在的管理员用户
        "password": "123456"  # 尝试常见密码
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('data'):
                token = result['data'].get('access_token')
                print(f"✓ 登录成功，获取到token")
                return token
        
        # 如果登录失败，尝试注册
        print("登录失败，尝试注册新用户...")
        import time
        timestamp = int(time.time())
        register_data = {
            "username": f"wechat_test_{timestamp}",
            "password": "test123456",
            "email": f"wechat_test_{timestamp}@example.com",
            "full_name": "微信测试用户"
        }
        
        response = requests.post(f"{base_url}/auth/register", json=register_data)
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('data'):
                token = result['data'].get('access_token')
                print(f"✓ 注册成功，获取到token")
                return token
        
        print(f"认证失败: {response.status_code} - {response.text}")
        return None
        
    except Exception as e:
        print(f"认证请求失败: {e}")
        return None

def test_wechat_upload():
    """测试微信账单上传功能"""
    
    # API配置
    base_url = "http://localhost:8000/api/v1"
    
    # 测试文件路径
    test_file = "wechat_bills_test.xlsx"
    
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        print("请先运行 create_wechat_test_file.py 创建测试文件")
        return
    
    print("开始测试微信账单上传API...")
    
    # 1. 测试获取可用解析器
    print("\n1. 测试获取可用解析器...")
    try:
        response = requests.get(f"{base_url}/upload/parsers")
        if response.status_code == 200:
            result = response.json()
            parsers = result.get('parsers', {})
            print("可用解析器:")
            for parser_type, info in parsers.items():
                print(f"  {parser_type}: {info}")
            
            # 检查是否包含微信解析器
            if 'wechat' in parsers:
                print("✓ 微信解析器已注册")
            else:
                print("✗ 微信解析器未注册")
                return
        else:
            print(f"获取解析器失败: {response.status_code}")
            return
    except Exception as e:
        print(f"请求失败: {e}")
        return
    
    # 2. 获取认证token
    print("\n2. 获取认证token...")
    token = get_auth_token()
    if not token:
        print("✗ 无法获取认证token，跳过上传测试")
        return
    
    # 3. 测试文件上传
    print("\n3. 测试微信账单文件上传...")
    try:
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        with open(test_file, 'rb') as f:
            files = {
                'file': (test_file, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            }
            data = {
                'source_type': 'wechat',
                'auto_categorize': 'true'
            }
            
            response = requests.post(f"{base_url}/upload/", files=files, data=data, headers=headers)
            
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✓ 上传成功!")
                print(f"解析结果:")
                print(f"  成功记录数: {result.get('success_count', 0)}")
                print(f"  失败记录数: {result.get('failed_count', 0)}")
                print(f"  总记录数: {result.get('total_count', 0)}")
                
                if result.get('errors'):
                    print(f"  错误信息: {result['errors']}")
                
                # 显示部分成功记录
                if result.get('success_records'):
                    print(f"\n前3条成功记录:")
                    for i, record in enumerate(result['success_records'][:3], 1):
                        print(f"    记录 {i}:")
                        print(f"      时间: {record.get('transaction_time')}")
                        print(f"      描述: {record.get('transaction_desc')}")
                        print(f"      金额: {record.get('amount')}")
                        print(f"      类型: {record.get('transaction_type')}")
                        print(f"      来源: {record.get('source_type')}")
                
            else:
                print(f"✗ 上传失败: {response.status_code}")
                try:
                    error_info = response.json()
                    print(f"错误详情: {json.dumps(error_info, indent=2, ensure_ascii=False)}")
                except:
                    print(f"错误详情: {response.text}")
                    
    except Exception as e:
        print(f"上传请求失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n测试完成!")

if __name__ == "__main__":
    test_wechat_upload()