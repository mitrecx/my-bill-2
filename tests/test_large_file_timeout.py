#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试大文件上传的超时问题
"""

import requests
import time
import os

def test_large_file_upload():
    """测试大文件上传"""
    print("=== 测试大文件支付宝账单上传 ===")
    
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # 登录获取token
    login_data = {
        "username": "testuser_large",
        "password": "test123456"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json()["data"]["access_token"]
            print("✅ 登录成功")
        else:
            print("❌ 登录失败，尝试注册...")
            register_data = {
                "username": "testuser_large",
                "password": "test123456",
                "email": "testlarge@example.com",
                "full_name": "Test User Large"
            }
            response = requests.post(f"{base_url}/auth/register", json=register_data)
            if response.status_code == 200:
                token = response.json()["data"]["access_token"]
                print("✅ 注册并登录成功")
            else:
                print(f"❌ 注册失败: {response.status_code}")
                return
        
        # 准备上传大文件
        file_path = "tests/large_alipay_bills.csv"
        if not os.path.exists(file_path):
            print(f"❌ 测试文件不存在: {file_path}")
            return
        
        print(f"📁 文件大小: {os.path.getsize(file_path)} bytes")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 测试开启AI分类的上传（可能超时）
        print("\n🚀 开始上传大文件（开启AI分类）...")
        start_time = time.time()
        
        with open(file_path, 'rb') as f:
            files = {"file": ("large_alipay_bills.csv", f, "text/csv")}
            data = {
                "source_type": "alipay",
                "auto_categorize": "true"  # 开启AI分类
            }
            
            try:
                # 设置较长的超时时间
                response = requests.post(
                    f"{base_url}/upload/", 
                    headers=headers, 
                    files=files, 
                    data=data,
                    timeout=120  # 2分钟超时
                )
                
                end_time = time.time()
                upload_time = end_time - start_time
                
                print(f"⏱️  上传耗时: {upload_time:.2f}秒")
                print(f"📊 响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 上传成功: {result.get('message', '')}")
                    if 'data' in result:
                        data = result['data']
                        print(f"   成功记录数: {data.get('success_count', 0)}")
                        print(f"   失败记录数: {data.get('failed_count', 0)}")
                        if 'ai_classification_count' in data:
                            print(f"   AI分类数: {data.get('ai_classification_count', 0)}")
                else:
                    print(f"❌ 上传失败: {response.status_code}")
                    try:
                        error_info = response.json()
                        print(f"   错误信息: {error_info.get('message', '')}")
                    except:
                        print(f"   错误信息: {response.text}")
                        
            except requests.exceptions.Timeout:
                end_time = time.time()
                upload_time = end_time - start_time
                print(f"⏱️  上传超时: {upload_time:.2f}秒")
                print("❌ 请求超时 - 这就是504 Gateway Timeout的原因！")
                
            except Exception as e:
                end_time = time.time()
                upload_time = end_time - start_time
                print(f"⏱️  上传耗时: {upload_time:.2f}秒")
                print(f"❌ 上传过程中发生错误: {str(e)}")
        
        # 测试关闭AI分类的上传（应该更快）
        print("\n🚀 开始上传大文件（关闭AI分类）...")
        start_time = time.time()
        
        with open(file_path, 'rb') as f:
            files = {"file": ("large_alipay_bills.csv", f, "text/csv")}
            data = {
                "source_type": "alipay",
                "auto_categorize": "false"  # 关闭AI分类
            }
            
            try:
                response = requests.post(
                    f"{base_url}/upload/", 
                    headers=headers, 
                    files=files, 
                    data=data,
                    timeout=60  # 1分钟超时
                )
                
                end_time = time.time()
                upload_time = end_time - start_time
                
                print(f"⏱️  上传耗时: {upload_time:.2f}秒")
                print(f"📊 响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 上传成功: {result.get('message', '')}")
                    if 'data' in result:
                        data = result['data']
                        print(f"   成功记录数: {data.get('success_count', 0)}")
                        print(f"   失败记录数: {data.get('failed_count', 0)}")
                else:
                    print(f"❌ 上传失败: {response.status_code}")
                    try:
                        error_info = response.json()
                        print(f"   错误信息: {error_info.get('message', '')}")
                    except:
                        print(f"   错误信息: {response.text}")
                        
            except requests.exceptions.Timeout:
                end_time = time.time()
                upload_time = end_time - start_time
                print(f"⏱️  上传超时: {upload_time:.2f}秒")
                print("❌ 即使关闭AI分类也超时了！")
                
            except Exception as e:
                end_time = time.time()
                upload_time = end_time - start_time
                print(f"⏱️  上传耗时: {upload_time:.2f}秒")
                print(f"❌ 上传过程中发生错误: {str(e)}")
                
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    test_large_file_upload()