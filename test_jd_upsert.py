#!/usr/bin/env python3
"""
测试京东账单的插入和更新功能
"""

import requests
import json
import os

# 配置
BASE_URL = "http://localhost:8000"
USERNAME = "test"
PASSWORD = "123456"
JD_FILE_PATH = "/Users/chenxing/projects/my-bills-2/bills/京东交易流水(申请时间2025年07月05日10时04分27秒)_739.csv"

def login():
    """登录获取token"""
    print("1. 登录获取token...")
    
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            token = result["data"]["access_token"]
            print(f"登录成功，获取token: {token[:20]}...")
            return token
        else:
            print(f"登录失败: {result}")
            return None
    else:
        print(f"登录请求失败: {response.status_code}")
        return None

def create_family(token):
    """创建测试家庭"""
    print("2. 创建测试家庭...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    family_data = {
        "family_name": "测试家庭",
        "description": "用于测试京东账单上传的家庭"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/families/", headers=headers, json=family_data)
    
    if response.status_code == 200:
        result = response.json()
        family_id = result["id"]
        print(f"家庭创建成功，ID: {family_id}")
        return family_id
    else:
        print(f"家庭创建失败: {response.status_code} - {response.text}")
        return None

def get_families(token):
    """获取用户家庭列表"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/api/v1/families/", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        families = result.get("data", [])
        if families:
            print(f"找到 {len(families)} 个家庭")
            return families[0]["id"]  # 返回第一个家庭的ID
        else:
            print("用户没有加入任何家庭")
            return None
    else:
        print(f"获取家庭列表失败: {response.status_code}")
        return None

def upload_file(token, file_path, test_name, family_id):
    """上传文件"""
    print(f"\n{test_name}")
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return None
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(file_path, 'rb') as f:
        files = {
            "file": (os.path.basename(file_path), f, "text/csv")
        }
        data = {
            "family_id": family_id,
            "source_type": "jd",
            "auto_categorize": False
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/upload/", headers=headers, files=files, data=data)
    
    print(f"上传响应状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"上传结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return result
    else:
        print(f"上传失败: {response.text}")
        return None

def get_bill_count(token):
    """获取账单总数"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/api/v1/bills/", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        return len(result.get("bills", []))
    else:
        print(f"获取账单失败: {response.status_code}")
        return 0

def main():
    print("=== 测试京东账单的插入和更新功能 ===")
    
    # 登录
    token = login()
    if not token:
        return
    
    # 获取或创建家庭
    family_id = get_families(token)
    if not family_id:
        family_id = create_family(token)
        if not family_id:
            print("无法创建家庭，测试终止")
            return
    else:
        print(f"使用现有家庭，ID: {family_id}")
    
    # 获取初始账单数量
    initial_count = get_bill_count(token)
    print(f"\n初始账单数量: {initial_count}")
    
    # 第一次上传 - 应该插入新记录
    result1 = upload_file(token, JD_FILE_PATH, "3. 第一次上传京东账单（应该插入新记录）...", family_id)
    if not result1:
        return
    
    # 获取第一次上传后的账单数量
    count_after_first = get_bill_count(token)
    print(f"\n第一次上传后账单数量: {count_after_first}")
    print(f"新增记录数: {count_after_first - initial_count}")
    
    # 第二次上传 - 应该更新已存在的记录
    result2 = upload_file(token, JD_FILE_PATH, "4. 第二次上传相同京东账单（应该更新已存在记录）...", family_id)
    if not result2:
        return
    
    # 获取第二次上传后的账单数量
    count_after_second = get_bill_count(token)
    print(f"\n第二次上传后账单数量: {count_after_second}")
    print(f"第二次上传新增记录数: {count_after_second - count_after_first}")
    
    # 分析结果
    print("\n=== 测试结果分析 ===")
    print(f"第一次上传:")
    print(f"  - total_records: {result1.get('total_records')}")
    print(f"  - success_count: {result1.get('success_count')}")
    print(f"  - warnings: {result1.get('warnings', [])}")
    
    print(f"\n第二次上传:")
    print(f"  - total_records: {result2.get('total_records')}")
    print(f"  - success_count: {result2.get('success_count')}")
    print(f"  - warnings: {result2.get('warnings', [])}")
    
    # 验证功能是否正常
    if count_after_second == count_after_first:
        print("\n✅ 测试成功！第二次上传没有新增记录，说明更新功能正常工作")
        
        # 检查是否有更新记录的提示
        warnings = result2.get('warnings', [])
        update_warning = any('更新已存在记录数' in str(w) for w in warnings)
        if update_warning:
            print("✅ 更新记录统计正常")
        else:
            print("⚠️  没有找到更新记录的统计信息")
    else:
        print(f"\n❌ 测试失败！第二次上传仍然新增了 {count_after_second - count_after_first} 条记录")

if __name__ == "__main__":
    main()