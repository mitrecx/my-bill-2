#!/usr/bin/env python3
"""
测试招商银行PDF上传功能，验证 raw_data 中的 counter_party 字段
"""

import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:8000"

def login():
    """登录获取token"""
    login_data = {
        "username": "chenxing@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

def create_test_cmb_file():
    """创建测试用的招商银行账单文件"""
    test_content = """2025-04-15
CNY
-4577.17
6522.51
掌上生活还款
陈兴
2025-04-16
CNY
100.00
6622.51
工资收入
公司财务部
2025-04-17
CNY
-50.00
6572.51
午餐费用
美团外卖"""
    
    test_file_path = "/tmp/test_cmb_bill.txt"
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    return test_file_path

def upload_cmb_file(token, file_path):
    """上传招商银行账单文件"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        with open(file_path, 'rb') as f:
            files = {
                'file': ('test_cmb_bill.txt', f, 'text/plain')
            }
            data = {
                'source_type': 'cmb'
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/upload/bills",
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
            
        return response
        
    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return None

def get_bills(token, limit=10):
    """获取账单列表"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/bills?limit={limit}",
            headers=headers,
            timeout=10
        )
        return response
    except Exception as e:
        print(f"❌ 获取账单异常: {e}")
        return None

def test_cmb_upload_with_counter_party():
    """测试招商银行上传功能，验证 counter_party 字段"""
    print("=== 测试招商银行PDF上传功能 - counter_party 字段验证 ===\n")
    
    # 1. 登录
    print("1. 登录系统...")
    token = login()
    if not token:
        print("❌ 登录失败，无法继续测试")
        return False
    print("✅ 登录成功")
    
    # 2. 创建测试文件
    print("\n2. 创建测试文件...")
    test_file = create_test_cmb_file()
    print(f"✅ 测试文件创建: {test_file}")
    
    # 3. 上传文件
    print("\n3. 上传招商银行账单...")
    upload_response = upload_cmb_file(token, test_file)
    
    if not upload_response:
        print("❌ 上传失败")
        return False
    
    if upload_response.status_code == 200:
        upload_data = upload_response.json()
        print("✅ 上传成功")
        print(f"   处理结果: {upload_data}")
        
        # 检查上传结果
        if upload_data.get('success_count', 0) > 0:
            print(f"✅ 成功处理 {upload_data['success_count']} 条记录")
        else:
            print("❌ 没有成功处理的记录")
            return False
    else:
        print(f"❌ 上传失败: {upload_response.status_code} - {upload_response.text}")
        return False
    
    # 4. 等待处理完成
    print("\n4. 等待数据处理...")
    time.sleep(3)
    
    # 5. 获取账单列表验证
    print("\n5. 验证账单数据...")
    bills_response = get_bills(token, 5)
    
    if not bills_response or bills_response.status_code != 200:
        print("❌ 获取账单失败")
        return False
    
    bills_data = bills_response.json()
    bills = bills_data.get('bills', [])
    
    if not bills:
        print("❌ 没有找到账单记录")
        return False
    
    print(f"✅ 找到 {len(bills)} 条账单记录")
    
    # 6. 验证 raw_data 中的 counter_party 字段
    print("\n6. 验证 raw_data 中的 counter_party 字段...")
    
    counter_party_found = False
    for i, bill in enumerate(bills[:3]):  # 检查前3条记录
        print(f"\n--- 账单 {i+1} ---")
        print(f"交易描述: {bill.get('transaction_desc', 'N/A')}")
        print(f"金额: {bill.get('amount', 'N/A')}")
        print(f"交易时间: {bill.get('transaction_time', 'N/A')}")
        
        raw_data = bill.get('raw_data')
        if raw_data:
            try:
                if isinstance(raw_data, str):
                    raw_data_dict = json.loads(raw_data)
                else:
                    raw_data_dict = raw_data
                
                print(f"raw_data: {json.dumps(raw_data_dict, ensure_ascii=False, indent=2)}")
                
                # 检查 counter_party 字段
                if 'counter_party' in raw_data_dict:
                    print(f"✅ 找到 counter_party 字段: {raw_data_dict['counter_party']}")
                    counter_party_found = True
                    
                    # 检查是否还有旧的 counterpart 字段
                    if 'counterpart' in raw_data_dict:
                        print("❌ 仍然存在旧的 counterpart 字段")
                        return False
                    
                    # 验证所有必需字段
                    required_fields = ['date', 'currency', 'amount', 'balance', 'description', 'counter_party']
                    missing_fields = [field for field in required_fields if field not in raw_data_dict]
                    
                    if missing_fields:
                        print(f"❌ raw_data 缺少字段: {missing_fields}")
                        return False
                    else:
                        print("✅ raw_data 包含所有必需字段")
                else:
                    print("❌ raw_data 中缺少 counter_party 字段")
            except json.JSONDecodeError as e:
                print(f"❌ raw_data JSON 解析失败: {e}")
        else:
            print("❌ 账单缺少 raw_data 字段")
    
    # 7. 清理测试文件
    try:
        os.remove(test_file)
        print(f"\n✅ 清理测试文件: {test_file}")
    except:
        pass
    
    if counter_party_found:
        print("\n✅ counter_party 字段验证成功")
        return True
    else:
        print("\n❌ 未找到 counter_party 字段")
        return False

def main():
    """主测试函数"""
    print("等待后端服务启动...")
    time.sleep(2)
    
    success = test_cmb_upload_with_counter_party()
    
    if success:
        print("\n🎉 所有测试通过！")
        print("✅ raw_data 中的 counter_party 字段命名修正成功")
        print("✅ 招商银行PDF上传功能正常")
    else:
        print("\n❌ 测试失败，需要检查问题")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)