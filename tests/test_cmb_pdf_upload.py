#!/usr/bin/env python3
"""
测试招商银行PDF文件上传功能
"""

import os
import sys
import requests
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_cmb_pdf_upload():
    """测试招商银行PDF文件上传"""
    
    # 测试文件路径
    test_file_path = "/Users/chenxing/projects/my-bills-2/bills/招商银行交易流水(申请时间2025年07月05日10时27分05秒).pdf"
    
    print("=== 招商银行PDF上传测试 ===")
    print(f"测试文件: {test_file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(test_file_path):
        print(f"❌ 测试文件不存在: {test_file_path}")
        return False
    
    file_size = os.path.getsize(test_file_path)
    print(f"文件大小: {file_size / 1024 / 1024:.2f} MB")
    
    # 检查文件是否为PDF
    with open(test_file_path, 'rb') as f:
        header = f.read(10)
        if header.startswith(b'%PDF'):
            print("✅ 确认为PDF文件格式")
        else:
            print("❌ 不是有效的PDF文件")
            return False
    
    # 测试后端API
    api_base_url = "http://127.0.0.1:8000/api/v1"
    
    # 0. 先尝试注册用户（如果用户不存在）
    print("\n--- 步骤0: 用户注册 ---")
    register_data = {
        "username": "cmbtest",
        "email": "cmbtest@example.com",
        "password": "testpass123",
        "full_name": "CMB Test User"
    }
    
    try:
        register_response = requests.post(
            f"{api_base_url}/auth/register",
            json=register_data,
            headers={"Content-Type": "application/json"}
        )
        if register_response.status_code == 200:
            print("✅ 用户注册成功")
        elif register_response.status_code == 400:
            print("ℹ️ 用户已存在，跳过注册")
        else:
            print(f"⚠️ 注册响应: {register_response.status_code} - {register_response.text}")
    except Exception as e:
        print(f"⚠️ 注册请求失败: {e}")
    
    # 1. 测试登录
    print("\n--- 步骤1: 用户登录 ---")
    login_data = {
        "username": "cmbtest",
        "password": "testpass123"
    }
    
    try:
        login_response = requests.post(
            f"{api_base_url}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"登录响应状态码: {login_response.status_code}")
        print(f"登录响应内容: {login_response.text}")
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            # 从嵌套的data字段中获取access_token
            data = token_data.get("data", {})
            access_token = data.get("access_token")
            if access_token:
                print(f"✅ 登录成功，获取到token")
            else:
                print(f"❌ 登录响应中没有access_token: {token_data}")
                return False
        else:
            print(f"❌ 登录失败: {login_response.status_code} - {login_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return False
    
    # 2. 获取家庭列表
    print("\n--- 步骤2: 获取家庭列表 ---")
    headers = {"Authorization": f"Bearer {access_token}"}
    print(f"使用的token: {access_token[:20]}...")
    
    try:
        families_response = requests.get(
            f"{api_base_url}/families/",
            headers=headers
        )
        
        print(f"家庭列表响应状态码: {families_response.status_code}")
        print(f"家庭列表响应内容: {families_response.text}")
        
        if families_response.status_code == 200:
            families_data = families_response.json()
            if families_data.get("data") and len(families_data["data"]) > 0:
                family_id = families_data["data"][0]["id"]
                family_name = families_data["data"][0]["family_name"]
                print(f"✅ 获取到家庭: {family_name} (ID: {family_id})")
            else:
                print("ℹ️ 没有找到家庭，创建新家庭...")
                # 创建新家庭
                create_family_data = {
                    "family_name": "测试家庭",
                    "description": "用于测试招商银行PDF上传的家庭"
                }
                
                create_response = requests.post(
                    f"{api_base_url}/families/",
                    json=create_family_data,
                    headers=headers
                )
                
                print(f"创建家庭响应状态码: {create_response.status_code}")
                print(f"创建家庭响应内容: {create_response.text}")
                
                if create_response.status_code == 200:
                    family_data = create_response.json()
                    family_id = family_data["id"]
                    family_name = family_data["family_name"]
                    print(f"✅ 创建家庭成功: {family_name} (ID: {family_id})")
                else:
                    print(f"❌ 创建家庭失败: {create_response.status_code} - {create_response.text}")
                    return False
        else:
            print(f"❌ 获取家庭列表失败: {families_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 获取家庭列表请求失败: {e}")
        return False
    
    # 3. 测试文件上传
    print("\n--- 步骤3: 上传PDF文件 ---")
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {
                'file': ('招商银行交易流水.pdf', f, 'application/pdf')
            }
            data = {
                'family_id': family_id,
                'source_type': 'cmb',
                'auto_categorize': True
            }
            
            upload_response = requests.post(
                f"{api_base_url}/upload/",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            print(f"上传响应状态码: {upload_response.status_code}")
            print(f"上传响应内容: {upload_response.text}")
            
            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                success_count = upload_data.get("success_count", 0)
                total_records = upload_data.get("total_records", 0)
                print(f"✅ 上传成功！处理了 {success_count}/{total_records} 条记录")
                return True
            else:
                print(f"❌ 上传失败: {upload_response.status_code}")
                try:
                    error_data = upload_response.json()
                    print(f"错误详情: {error_data}")
                except:
                    print(f"错误详情: {upload_response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 上传请求失败: {e}")
        return False

def test_file_validation():
    """测试文件格式验证"""
    print("\n=== 文件格式验证测试 ===")
    
    # 测试后端配置
    try:
        from backend.config.settings import settings
        allowed_extensions = settings.allowed_extensions
        print(f"后端允许的文件格式: {allowed_extensions}")
        
        if '.pdf' in allowed_extensions:
            print("✅ 后端配置支持PDF格式")
        else:
            print("❌ 后端配置不支持PDF格式")
            return False
            
    except Exception as e:
        print(f"❌ 无法检查后端配置: {e}")
        return False
    
    # 测试解析器
    try:
        from backend.parsers import get_parser, get_available_parsers
        
        available_parsers = get_available_parsers()
        print(f"可用解析器: {available_parsers}")
        
        cmb_parser = get_parser("cmb")
        if cmb_parser:
            print("✅ 招商银行解析器可用")
        else:
            print("❌ 招商银行解析器不可用")
            return False
            
    except Exception as e:
        print(f"❌ 无法检查解析器: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("开始测试招商银行PDF上传功能...")
    
    # 先测试配置
    if not test_file_validation():
        print("\n❌ 配置验证失败")
        sys.exit(1)
    
    # 再测试上传
    if test_cmb_pdf_upload():
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 测试失败")
        sys.exit(1)