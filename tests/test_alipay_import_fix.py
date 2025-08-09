#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试支付宝账单导入修复
验证AI分类提示词中是否正确使用了"备注"和"分类"的组合
"""

import requests
import json
import os

def test_alipay_import():
    """测试支付宝账单导入"""
    
    # API基础URL
    base_url = "http://localhost:8000/api/v1"
    
    # 测试文件路径
    test_file = "test_alipay_bills.csv"
    
    print(f"开始测试支付宝账单导入...")
    
    # 检查测试文件是否存在
    if not os.path.exists(test_file):
        print(f"错误: 测试文件 {test_file} 不存在")
        return False
    
    try:
        # 先登录获取token
        login_data = {
            "username": "test",
            "password": "test123"
        }
        
        print("正在登录...")
        login_response = requests.post(f"{base_url}/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            print(f"登录错误信息: {login_response.text}")
            return False
        
        login_result = login_response.json()
        if not login_result.get('success'):
            print(f"❌ 登录失败: {login_result.get('message')}")
            return False
        
        token = login_result['data']['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print("✅ 登录成功")
        
        # 上传文件
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'text/csv')}
            data = {
                'source_type': 'alipay',
                'auto_categorize': 'true'
            }
            
            print(f"上传文件: {test_file}")
            response = requests.post(f"{base_url}/upload/", files=files, data=data, headers=headers)
            
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"上传成功!")
                print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 检查结果 - 直接从result中获取数据
                print(f"总记录数: {result.get('total_records', 0)}")
                print(f"成功记录数: {result.get('success_count', 0)}")
                print(f"创建的账单数: {result.get('created_count', 0)}")
                print(f"更新的账单数: {result.get('updated_count', 0)}")
                print(f"失败记录数: {result.get('failed_count', 0)}")
                print(f"AI分类数: {result.get('ai_classified_count', 0)}")
                
                created_bills = result.get('created_bills', [])
                if created_bills:
                    print(f"创建的账单IDs: {created_bills}")
                
                if result.get('created_count', 0) > 0:
                    print("✅ 支付宝账单导入成功!")
                    return True
                else:
                    print("❌ 没有创建新的账单")
                    return False
            else:
                print(f"❌ 上传失败: {response.status_code}")
                try:
                    error_info = response.json()
                    print(f"错误信息: {json.dumps(error_info, ensure_ascii=False, indent=2)}")
                except:
                    print(f"错误信息: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    # 切换到tests目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    success = test_alipay_import()
    if success:
        print("\n🎉 支付宝账单导入测试通过!")
    else:
        print("\n💥 支付宝账单导入测试失败!")