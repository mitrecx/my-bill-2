#!/usr/bin/env python3
"""
测试CMB解析器清理后的端到端流程
验证：CMB解析 -> 上传 -> AI分类的完整流程
"""

import requests
import json
import tempfile
import os

# API配置
BASE_URL = "http://127.0.0.1:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login"
UPLOAD_URL = f"{BASE_URL}/upload/"
AI_CLASSIFY_URL = f"{BASE_URL}/bills/ai-classification/batch"
AI_STATUS_URL = f"{BASE_URL}/bills/ai-classification/status"
BILLS_URL = f"{BASE_URL}/bills"

def login():
    """登录获取token"""
    login_data = {
        "username": "test",
        "password": "test123"
    }
    
    response = requests.post(LOGIN_URL, json=login_data)
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            return result['data']['access_token']
    
    print(f"❌ 登录失败: {response.status_code} - {response.text}")
    return None

def create_test_cmb_file():
    """创建测试用的CMB账单文件"""
    # 创建一个简单的PDF文件用于测试
    # 由于创建真实PDF比较复杂，我们使用txt文件模拟
    cmb_content = """招商银行账单

2024-01-15
CNY
-500.00
10000.00
午餐-麦当劳
麦当劳餐厅

2024-01-16
CNY
3000.00
13000.00
工资发放
信雅达系统工程股份有限公司

2024-01-17
CNY
-1200.00
11800.00
基金购买
天弘基金管理有限公司

2024-01-18
CNY
800.00
12600.00
基金赎回
天弘基金管理有限公司

2024-01-19
CNY
-50.00
12550.00
打车费用
滴滴出行

2024-01-20
CNY
-200.00
12350.00
房租
房东张三
"""
    
    # 创建临时文件，使用PDF扩展名
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pdf', encoding='utf-8') as f:
        f.write(cmb_content)
        return f.name

def upload_cmb_file(token, file_path):
    """上传CMB账单文件"""
    headers = {"Authorization": f"Bearer {token}"}
    upload_url = UPLOAD_URL
    
    with open(file_path, 'rb') as f:
        files = {"file": ("cmb_test.txt", f, "text/plain")}
        data = {"source_type": "cmb"}
        
        response = requests.post(upload_url, files=files, data=data, headers=headers)
    
    return response

def get_ai_status(token):
    """获取AI服务状态"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(AI_STATUS_URL, headers=headers)
    return response

def classify_bills_batch(token, bill_ids):
    """批量AI分类"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(AI_CLASSIFY_URL, json=bill_ids, headers=headers)
    return response

def get_bill_details(token, bill_id):
    """获取账单详情"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BILLS_URL}/{bill_id}", headers=headers)
    return response

def delete_bill(token, bill_id):
    """删除账单"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{BILLS_URL}/{bill_id}", headers=headers)
    return response

def main():
    """主测试流程"""
    print("🧪 测试CMB解析器清理后的端到端流程...")
    
    # 1. 登录
    print("\n🔐 登录...")
    token = login()
    if not token:
        return
    print("✅ 登录成功")
    
    # 2. 创建测试文件
    print("\n📄 创建测试CMB文件...")
    test_file = create_test_cmb_file()
    print(f"✅ 创建测试文件: {test_file}")
    
    try:
        # 3. 上传文件
        print("\n📤 上传CMB账单文件...")
        upload_response = upload_cmb_file(token, test_file)
        
        if upload_response.status_code == 200:
            upload_result = upload_response.json()
            if upload_result.get('success'):
                print("✅ 文件上传成功")
                print(f"📊 上传结果: {upload_result['message']}")
                
                # 提取账单ID
                bill_ids = []
                if 'data' in upload_result and 'bills' in upload_result['data']:
                    bill_ids = [bill['id'] for bill in upload_result['data']['bills']]
                    print(f"📋 创建了 {len(bill_ids)} 个账单: {bill_ids}")
                    
                    # 检查账单是否没有预设分类
                    print("\n🔍 检查账单分类状态...")
                    for bill_id in bill_ids:
                        detail_response = get_bill_details(token, bill_id)
                        if detail_response.status_code == 200:
                            detail_result = detail_response.json()
                            if detail_result.get('success'):
                                bill = detail_result['data']
                                category = bill.get('category_name', '未分类')
                                print(f"   账单{bill_id}: {bill['transaction_desc']} → {category}")
                    
                    # 4. 检查AI服务状态
                    print("\n🤖 检查AI服务状态...")
                    ai_status_response = get_ai_status(token)
                    if ai_status_response.status_code == 200:
                        ai_status = ai_status_response.json()
                        if ai_status.get('success') and ai_status['data']['available']:
                            print("✅ AI服务可用")
                            
                            # 5. 执行批量AI分类
                            print("\n🎯 执行批量AI分类...")
                            classify_response = classify_bills_batch(token, bill_ids)
                            
                            if classify_response.status_code == 200:
                                classify_result = classify_response.json()
                                if classify_result.get('success'):
                                    print("✅ 批量AI分类成功")
                                    print(f"📊 分类结果: {classify_result['message']}")
                                    
                                    # 显示分类结果
                                    results = classify_result['data']['results']
                                    successful_count = classify_result['data']['successful_count']
                                    total_count = classify_result['data']['total_bills']
                                    
                                    print(f"\n📈 分类统计: {successful_count}/{total_count} 成功")
                                    for result in results:
                                        bill_id = result['bill_id']
                                        status = result['status']
                                        if status == 'success':
                                            suggested_category = result['suggested_category']
                                            print(f"   ✅ 账单{bill_id}: {suggested_category}")
                                        else:
                                            error = result.get('error', '未知错误')
                                            print(f"   ❌ 账单{bill_id}: {error}")
                                    
                                    # 6. 验证分类结果
                                    print("\n🔍 验证AI分类结果...")
                                    for bill_id in bill_ids:
                                        detail_response = get_bill_details(token, bill_id)
                                        if detail_response.status_code == 200:
                                            detail_result = detail_response.json()
                                            if detail_result.get('success'):
                                                bill = detail_result['data']
                                                category = bill.get('category_name', '未分类')
                                                desc = bill['transaction_desc']
                                                print(f"   账单{bill_id}: {desc} → {category}")
                                
                                else:
                                    print(f"❌ 批量AI分类失败: {classify_result.get('message', '未知错误')}")
                            else:
                                print(f"❌ 批量AI分类请求失败: {classify_response.status_code} - {classify_response.text}")
                        else:
                            print("❌ AI服务不可用")
                    else:
                        print(f"❌ 获取AI服务状态失败: {ai_status_response.status_code}")
                    
                    # 7. 清理测试数据
                    print("\n🧹 清理测试数据...")
                    for bill_id in bill_ids:
                        delete_response = delete_bill(token, bill_id)
                        if delete_response.status_code == 200:
                            print(f"✅ 删除账单{bill_id}")
                        else:
                            print(f"❌ 删除账单{bill_id}失败")
                
                else:
                    print("❌ 上传结果中没有账单数据")
            else:
                print(f"❌ 文件上传失败: {upload_result.get('message', '未知错误')}")
        else:
            print(f"❌ 文件上传请求失败: {upload_response.status_code} - {upload_response.text}")
    
    finally:
        # 清理临时文件
        if os.path.exists(test_file):
            os.unlink(test_file)
            print(f"🗑️ 清理临时文件: {test_file}")
    
    print("\n✨ CMB解析器端到端测试完成！")

if __name__ == "__main__":
    main()