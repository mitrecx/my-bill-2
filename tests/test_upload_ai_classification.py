#!/usr/bin/env python3
"""
测试账单上传时的AI批量分类功能
"""

import sys
import os
import requests
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试配置
BASE_URL = "http://127.0.0.1:8000/api/v1"
TEST_USERNAME = "testuser123"  # 使用刚才注册成功的用户
TEST_PASSWORD = "testpass123"  # 对应的密码

def register_test_user():
    """注册测试用户"""
    register_data = {
        "username": TEST_USERNAME,
        "email": f"{TEST_USERNAME}@test.com",
        "password": TEST_PASSWORD,
        "full_name": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"✅ 注册成功")
            return True
        else:
            print(f"❌ 注册失败: {result.get('message')}")
            return False
    else:
        print(f"❌ 注册请求失败: {response.status_code}")
        if response.status_code == 400:
            print("   用户可能已存在，尝试直接登录")
        return False

def login():
    """登录获取token"""
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            token = result["data"]["access_token"]
            print(f"✅ 登录成功，获取到token")
            return token
        else:
            print(f"❌ 登录失败: {result.get('message')}")
            return None
    else:
        print(f"❌ 登录请求失败: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"   错误详情: {error_detail}")
        except:
            print(f"   错误内容: {response.text}")
        return None

def create_test_csv_file():
    """创建测试用的CSV文件（支付宝格式）"""
    # 支付宝账单格式的CSV内容
    csv_content = """记录时间,分类,收支类型,金额,备注,账户,来源,标签
2024-01-15 10:30:00,转账,收入,8500.00,工资发放,招商银行储蓄卡(1234),,
2024-01-15 12:15:00,餐饮美食,支出,35.50,午餐-麦当劳,支付宝余额,,
2024-01-15 18:30:00,交通出行,支出,28.00,打车费用-滴滴出行,花呗,,
2024-01-16 09:00:00,购物消费,支出,156.80,日用品采购-天猫超市,支付宝余额,,
2024-01-16 14:20:00,医疗健康,支出,15.00,挂号费-人民医院,支付宝余额,,
"""
    
    test_file_path = "/tmp/test_bills.csv"
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(csv_content)
    
    print(f"✅ 创建测试CSV文件（支付宝格式）: {test_file_path}")
    return test_file_path

def upload_file_with_ai_classification(token, file_path):
    """上传文件并启用AI分类"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(file_path, "rb") as f:
        files = {
            "file": ("test_bills.csv", f, "text/csv")
        }
        data = {
            "auto_categorize": "true",  # 启用自动分类
            "source_type": "alipay"     # 指定为支付宝类型
        }
        
        print("📤 开始上传文件并启用AI分类...")
        response = requests.post(
            f"{BASE_URL}/upload/",
            headers=headers,
            files=files,
            data=data
        )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 文件上传成功!")
        print(f"📊 上传结果:")
        print(f"   - 文件名: {result.get('filename')}")
        print(f"   - 总记录数: {result.get('total_records')}")
        print(f"   - 成功处理: {result.get('success_count')}")
        print(f"   - 新增记录: {result.get('created_count', 0)}")
        print(f"   - 失败记录: {result.get('failed_count')}")
        print(f"   - AI分类成功: {result.get('ai_classified_count', 0)}")
        print(f"   - 状态: {result.get('status')}")
        
        if result.get('warnings'):
            print(f"⚠️  警告信息: {result['warnings']}")
        
        if result.get('errors'):
            print(f"❌ 错误信息: {result['errors']}")
        
        return result.get('created_bills', [])
    else:
        print(f"❌ 文件上传失败: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"   错误详情: {error_detail}")
        except:
            print(f"   错误内容: {response.text}")
        return []

def check_bill_categories(token, bill_ids):
    """检查账单的分类结果"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"\n🔍 检查 {len(bill_ids)} 个账单的分类结果...")
    
    for bill_id in bill_ids:
        response = requests.get(f"{BASE_URL}/bills/{bill_id}", headers=headers)
        if response.status_code == 200:
            bill = response.json()
            category_name = bill.get('category', {}).get('category_name', '未分类') if bill.get('category') else '未分类'
            print(f"   账单 {bill_id}: {bill.get('transaction_desc', '')} -> {category_name}")
        else:
            print(f"   ❌ 无法获取账单 {bill_id} 信息")

def main():
    """主测试函数"""
    print("🚀 开始测试账单上传时的AI批量分类功能")
    print("=" * 60)
    
    # 1. 尝试注册测试用户（如果已存在会失败，但不影响后续登录）
    register_test_user()
    
    # 2. 登录
    token = login()
    if not token:
        print("❌ 无法获取认证token，测试终止")
        return
    
    # 2. 创建测试文件
    test_file = create_test_csv_file()
    
    # 3. 上传文件并启用AI分类
    bill_ids = upload_file_with_ai_classification(token, test_file)
    
    # 4. 检查分类结果
    if bill_ids:
        check_bill_categories(token, bill_ids)
    
    # 5. 清理测试文件
    try:
        os.remove(test_file)
        print(f"\n🧹 清理测试文件: {test_file}")
    except:
        pass
    
    print("\n✅ 测试完成!")

if __name__ == "__main__":
    main()