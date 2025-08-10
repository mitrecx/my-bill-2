#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试支付宝账单上传超时问题
分析AI分类服务是否导致504 Gateway Timeout
"""

import sys
import os
import time
import requests
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_alipay_upload_without_ai():
    """测试关闭AI分类的支付宝账单上传"""
    print("=== 测试支付宝账单上传（关闭AI分类）===")
    
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # 1. 获取可用解析器
    try:
        response = requests.get(f"{base_url}/upload/parsers")
        if response.status_code == 200:
            parsers = response.json()
            print(f"可用解析器: {parsers}")
            if 'alipay' not in parsers.get('parsers', []):
                print("支付宝解析器未注册")
                return
        else:
            print(f"获取解析器失败: {response.status_code}")
            return
    except Exception as e:
        print(f"获取解析器失败: {e}")
        return
    
    # 2. 获取认证token
    token = None
    try:
        # 尝试登录
        login_data = {
            "username": "test_user_alipay_timeout",
            "password": "test123456"
        }
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("data", {}).get("access_token")
            print("登录成功")
        else:
            # 登录失败，尝试注册
            print("登录失败，尝试注册新用户...")
            register_data = {
                "username": "test_user_alipay_timeout",
                "email": "test_alipay_timeout@example.com",
                "password": "test123456"
            }
            response = requests.post(f"{base_url}/auth/register", json=register_data)
            
            if response.status_code == 200:
                print("注册成功，重新登录...")
                response = requests.post(f"{base_url}/auth/login", json=login_data)
                if response.status_code == 200:
                    result = response.json()
                    token = result.get("data", {}).get("access_token")
                    print("登录成功")
                else:
                    print(f"重新登录失败: {response.status_code}")
                    return
            else:
                print(f"注册失败: {response.status_code}")
                return
    except Exception as e:
        print(f"认证失败: {e}")
        return
    
    if not token:
        print("无法获取认证token")
        return
    
    # 3. 测试支付宝账单上传（关闭AI分类）
    try:
        # 检查测试文件是否存在
        test_file_path = "/Users/chenxing/projects/my-bills-2/tests/test_alipay_bills.csv"
        if not os.path.exists(test_file_path):
            print(f"测试文件不存在: {test_file_path}")
            return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 记录开始时间
        start_time = time.time()
        
        with open(test_file_path, 'rb') as f:
            files = {"file": ("test_alipay_bills.csv", f, "text/csv")}
            data = {
                "source_type": "alipay",
                "auto_categorize": "false"  # 关闭AI分类
            }
            
            print("开始上传支付宝账单（关闭AI分类）...")
            response = requests.post(
                f"{base_url}/upload/",
                headers=headers,
                files=files,
                data=data,
                timeout=30  # 30秒超时
            )
        
        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"上传耗时: {duration:.2f}秒")
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"上传成功: 成功记录数={result.get('success_count', 0)}, 失败记录数={result.get('failed_count', 0)}")
        else:
            print(f"上传失败: {response.text}")
            
    except requests.exceptions.Timeout:
        print("上传超时（30秒）")
    except Exception as e:
        print(f"上传失败: {e}")


def test_alipay_upload_with_ai():
    """测试开启AI分类的支付宝账单上传"""
    print("\n=== 测试支付宝账单上传（开启AI分类）===")
    
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # 获取认证token（复用之前的用户）
    token = None
    try:
        login_data = {
            "username": "test_user_alipay_timeout",
            "password": "test123456"
        }
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("data", {}).get("access_token")
            print("登录成功")
        else:
            print(f"登录失败: {response.status_code}")
            return
    except Exception as e:
        print(f"认证失败: {e}")
        return
    
    if not token:
        print("无法获取认证token")
        return
    
    # 测试支付宝账单上传（开启AI分类）
    try:
        test_file_path = "/Users/chenxing/projects/my-bills-2/tests/test_alipay_bills.csv"
        if not os.path.exists(test_file_path):
            print(f"测试文件不存在: {test_file_path}")
            return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 记录开始时间
        start_time = time.time()
        
        with open(test_file_path, 'rb') as f:
            files = {"file": ("test_alipay_bills.csv", f, "text/csv")}
            data = {
                "source_type": "alipay",
                "auto_categorize": "true"  # 开启AI分类
            }
            
            print("开始上传支付宝账单（开启AI分类）...")
            response = requests.post(
                f"{base_url}/upload/",
                headers=headers,
                files=files,
                data=data,
                timeout=120  # 120秒超时
            )
        
        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"上传耗时: {duration:.2f}秒")
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"上传成功: 成功记录数={result.get('success_count', 0)}, 失败记录数={result.get('failed_count', 0)}, AI分类数={result.get('ai_classified_count', 0)}")
        else:
            print(f"上传失败: {response.text}")
            
    except requests.exceptions.Timeout:
        print("上传超时（120秒）")
    except Exception as e:
        print(f"上传失败: {e}")


if __name__ == "__main__":
    print("开始测试支付宝账单上传超时问题...")
    
    # 先测试关闭AI分类的情况
    test_alipay_upload_without_ai()
    
    # 再测试开启AI分类的情况
    test_alipay_upload_with_ai()
    
    print("\n测试完成")