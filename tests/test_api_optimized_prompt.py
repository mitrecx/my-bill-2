#!/usr/bin/env python3
"""
测试API中优化后的AI分类提示词
"""

import requests
import json
import time

# API配置
BASE_URL = "http://127.0.0.1:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login"
BILLS_URL = f"{BASE_URL}/bills"
AI_CLASSIFY_URL = f"{BASE_URL}/bills/ai-classify-batch"
AI_STATUS_URL = f"{BASE_URL}/bills/ai-classification/status"

def login():
    """登录获取token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(LOGIN_URL, json=login_data)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            token = result["data"]["access_token"]
            print("✅ 登录成功")
            return token
        else:
            print(f"❌ 登录失败: {result.get('message', '未知错误')}")
            return None
    else:
        print(f"❌ 登录失败: {response.text}")
        return None

def create_test_bills(token):
    """创建测试账单"""
    headers = {"Authorization": f"Bearer {token}"}
    
    test_bills = [
        {
            "amount": 1000.61,
            "transaction_type": "支出",
            "description": "打车费用-滴滴出行",
            "source_type": "cmb",
            "transaction_time": "2024-01-15T10:30:00"
        },
        {
            "amount": 3630.0,
            "transaction_type": "支出", 
            "description": "挂号费",
            "source_type": "cmb",
            "transaction_time": "2024-01-16T09:00:00"
        },
        {
            "amount": 29.66,
            "transaction_type": "收入",
            "description": "基金赎回",
            "source_type": "cmb",
            "transaction_time": "2024-01-17T14:20:00"
        },
        {
            "amount": 45.8,
            "transaction_type": "支出",
            "description": "午餐-麦当劳",
            "source_type": "alipay",
            "transaction_time": "2024-01-18T12:15:00"
        },
        {
            "amount": 2500.0,
            "transaction_type": "支出",
            "description": "房租",
            "source_type": "cmb",
            "transaction_time": "2024-01-19T16:00:00"
        },
        {
            "amount": 150.0,
            "transaction_type": "支出",
            "description": "加油费-中石化",
            "source_type": "cmb",
            "transaction_time": "2024-01-20T08:30:00"
        }
    ]
    
    created_bills = []
    for bill_data in test_bills:
        response = requests.post(BILLS_URL, json=bill_data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                bill = result["data"]
                created_bills.append(bill)
                print(f"✅ 创建账单: {bill_data['description']}")
            else:
                print(f"❌ 创建账单失败: {result.get('message', '未知错误')}")
        else:
            print(f"❌ 创建账单失败: {response.text}")
    
    return created_bills

def test_ai_classification(token, bill_ids):
    """测试AI批量分类"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 检查AI服务状态
    response = requests.get(AI_STATUS_URL, headers=headers)
    if response.status_code == 200:
        status = response.json()
        print(f"✅ AI服务状态: {status}")
    else:
        print(f"❌ 获取AI服务状态失败: {response.text}")
        return
    
    # 执行批量分类（直接发送账单ID列表）
    response = requests.post(AI_CLASSIFY_URL, json=bill_ids, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 批量分类请求成功")
        print(f"📊 分类结果: {result}")
        
        # 统计分类成功率
        success_count = result.get('success_count', 0)
        total_count = result.get('total_count', 0)
        if total_count > 0:
            success_rate = success_count / total_count * 100
            print(f"📈 分类成功率: {success_count}/{total_count} ({success_rate:.1f}%)")
        
        return result
    else:
        print(f"❌ 批量分类失败: {response.text}")
        return None

def get_bills_with_categories(token, bill_ids):
    """获取账单及其分类信息"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n📋 账单分类详情:")
    for bill_id in bill_ids:
        response = requests.get(f"{BILLS_URL}/{bill_id}", headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                bill = result["data"]
                category = bill.get('category_name', '未分类')
                status = "✅" if category != '未分类' else "❌"
                print(f"{status} 账单{bill_id}: {bill['transaction_desc']} → {category}")
            else:
                print(f"❌ 获取账单{bill_id}失败: {result.get('message', '未知错误')}")
        else:
            print(f"❌ 获取账单{bill_id}失败: {response.text}")

def cleanup_bills(token, bill_ids):
    """清理测试账单"""
    headers = {"Authorization": f"Bearer {token}"}
    
    for bill_id in bill_ids:
        response = requests.delete(f"{BILLS_URL}/{bill_id}", headers=headers)
        if response.status_code == 200:
            print(f"✅ 删除账单{bill_id}")
        else:
            print(f"❌ 删除账单{bill_id}失败")

def main():
    """主测试流程"""
    print("🧪 开始测试优化后的AI分类提示词...")
    
    # 登录
    token = login()
    if not token:
        return
    
    try:
        # 创建测试账单
        print(f"\n📝 创建测试账单...")
        bills = create_test_bills(token)
        if not bills:
            print("❌ 没有成功创建任何账单")
            return
        
        bill_ids = [bill['id'] for bill in bills]
        print(f"✅ 成功创建 {len(bills)} 个测试账单")
        
        # 等待一下确保账单创建完成
        time.sleep(1)
        
        # 测试AI分类
        print(f"\n🤖 测试AI批量分类...")
        result = test_ai_classification(token, bill_ids)
        
        # 等待分类完成
        time.sleep(2)
        
        # 获取分类结果详情
        get_bills_with_categories(token, bill_ids)
        
        print(f"\n✨ 优化后的提示词API测试完成！")
        
    finally:
        # 清理测试数据
        print(f"\n🧹 清理测试数据...")
        if 'bill_ids' in locals():
            cleanup_bills(token, bill_ids)

if __name__ == "__main__":
    main()