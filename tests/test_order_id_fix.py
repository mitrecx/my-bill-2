#!/usr/bin/env python3
"""
测试京东账单order_id字段修复
"""

import requests
import json
import os

BASE_URL = "http://localhost:8000"

def login():
    """登录获取token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"登录响应状态: {response.status_code}")
    print(f"登录响应内容: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success") and "data" in result:
            return result["data"].get("access_token")
        elif "access_token" in result:
            return result["access_token"]
    
    raise Exception(f"登录失败: {response.text}")

def get_or_create_family(token):
    """获取或创建家庭"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 先尝试获取现有家庭
    response = requests.get(f"{BASE_URL}/api/v1/families", headers=headers)
    if response.status_code == 200:
        families = response.json()
        if families and len(families) > 0:
            family_id = families[0]["id"]
            print(f"使用现有家庭ID: {family_id}")
            return family_id
    
    # 创建新家庭
    family_data = {
        "family_name": "测试家庭",
        "description": "用于测试的家庭"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/families", json=family_data, headers=headers)
    if response.status_code == 200:
        family = response.json()
        family_id = family["id"]
        print(f"创建新家庭ID: {family_id}")
        return family_id
    
    raise Exception(f"创建家庭失败: {response.text}")

def upload_jd_bill(token, family_id):
    """上传京东账单"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 查找京东账单文件
    jd_file = None
    bills_dir = "/Users/chenxing/projects/my-bills-2/bills"
    
    if os.path.exists(bills_dir):
        for file in os.listdir(bills_dir):
            if "京东" in file and file.endswith('.csv'):
                jd_file = os.path.join(bills_dir, file)
                break
    
    if not jd_file or not os.path.exists(jd_file):
        print("未找到京东账单文件")
        return False
    
    print(f"上传京东账单文件: {jd_file}")
    
    with open(jd_file, 'rb') as f:
        files = {'file': f}
        data = {
            'family_id': family_id,
            'source_type': 'jd'
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/upload", files=files, data=data, headers=headers)
        print(f"上传响应状态: {response.status_code}")
        print(f"上传响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"上传成功: {result}")
            return True
        else:
            print(f"上传失败: {response.text}")
            return False

def verify_order_id_fields(token, family_id):
    """验证order_id字段"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取京东账单记录
    response = requests.get(f"{BASE_URL}/api/v1/bills?family_id={family_id}&source_type=jd&limit=10", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        # 处理分页响应格式
        if isinstance(result, dict) and 'data' in result:
            bills = result['data']
        else:
            bills = result
            
        print(f"获取到 {len(bills)} 条京东账单记录")
        
        if bills:
            # 检查前几条记录的order_id字段
            for i, bill in enumerate(bills[:5]):
                order_id = bill.get('order_id')
                print(f"记录 {i+1}: order_id = {order_id}")
                if order_id:
                    print(f"  ✓ order_id字段存在且有值")
                else:
                    print(f"  ✗ order_id字段为空")
            
            # 统计有order_id的记录数量
            with_order_id = sum(1 for bill in bills if bill.get('order_id'))
            print(f"\n总计: {with_order_id}/{len(bills)} 条记录有order_id字段")
            
            return with_order_id > 0
        else:
            print("没有找到京东账单记录")
            return False
    else:
        print(f"获取账单失败: {response.text}")
        return False

def main():
    try:
        print("=== 测试京东账单order_id字段修复 ===")
        
        # 1. 登录
        print("\n1. 登录...")
        token = login()
        print("登录成功")
        
        # 2. 获取或创建家庭
        print("\n2. 获取或创建家庭...")
        family_id = get_or_create_family(token)
        
        # 3. 上传京东账单
        print("\n3. 上传京东账单...")
        upload_success = upload_jd_bill(token, family_id)
        
        if upload_success:
            # 4. 验证order_id字段
            print("\n4. 验证order_id字段...")
            verification_success = verify_order_id_fields(token, family_id)
            
            if verification_success:
                print("\n✓ 测试成功: order_id字段修复正常")
            else:
                print("\n✗ 测试失败: order_id字段仍有问题")
        else:
            print("\n✗ 测试失败: 上传京东账单失败")
            
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")

if __name__ == "__main__":
    main()