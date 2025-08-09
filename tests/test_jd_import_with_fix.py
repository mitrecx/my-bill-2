#!/usr/bin/env python3
"""
测试JD账单导入修复是否生效
"""

import requests
import json
import tempfile
import os

def create_test_jd_csv():
    """创建测试用的JD账单CSV文件"""
    csv_content = """交易时间,商户名称,交易说明,金额,收/付款方式,交易状态,收/支,交易分类,交易订单号,商家订单号,备注
2025-01-10 14:30:20,京东超市,牛奶 蒙牛特仑苏,25.80,京东支付,交易成功,支出,食品酒饮,20250110001234567890,JD20250110001234567890,
2025-01-09 09:15:30,京东数码,苹果数据线,39.90,京东支付,交易成功,支出,电脑办公,20250109001234567891,JD20250109001234567891,
2025-01-08 16:45:10,京东小金库,京东小金库收益,0.15,京东小金库,交易成功,收入,小金库,20250108001234567892,JD20250108001234567892,"""
    
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
    temp_file.write(csv_content)
    temp_file.close()
    
    return temp_file.name

def test_jd_import_with_fix():
    """测试JD账单导入修复"""
    
    # 1. 登录获取token
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {
        "username": "test",
        "password": "test123"
    }
    
    print("正在登录...")
    response = requests.post(login_url, json=login_data)
    if response.status_code != 200:
        print(f"登录失败: {response.status_code} - {response.text}")
        return
    
    login_result = response.json()
    if not login_result.get('success'):
        print(f"登录失败: {login_result}")
        return
    
    access_token = login_result['data']['access_token']
    print(f"登录成功，获取到access_token")
    
    # 2. 使用已创建的测试CSV文件
    csv_file_path = "test_jd_bills.csv"
    
    try:
        # 3. 上传JD账单文件
        upload_url = "http://localhost:8000/api/v1/upload/"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        with open(csv_file_path, 'rb') as f:
            files = {
                'file': ('test_jd_bills.csv', f, 'text/csv')
            }
            data = {
                'source_type': 'jd'
            }
            
            print("正在上传JD账单文件...")
            response = requests.post(upload_url, headers=headers, files=files, data=data)
        
        print(f"上传响应状态码: {response.status_code}")
        result = response.json()
        print(f"上传响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print(f"上传成功: {result.get('message', 'N/A')}")
            
            data = result.get('data', {})
            print(f"创建账单数: {data.get('created_count', 0)}")
            print(f"AI分类数: {data.get('ai_classified_count', 0)}")
            
            # 获取创建的账单ID
            created_bills = data.get('created_bills', [])
            if created_bills:
                print(f"创建的账单IDs: {created_bills}")
                
                # 4. 查看创建的账单详情
                print("\n查看创建的账单详情...")
                for bill_id in created_bills:
                    bill_url = f"http://localhost:8000/api/v1/bills/{bill_id}"
                    response = requests.get(bill_url, headers=headers)
                    
                    if response.status_code == 200:
                        bill_result = response.json()
                        bill_data = bill_result['data']
                        print(f"账单ID {bill_id}:")
                        print(f"  交易描述: {bill_data['transaction_desc']}")
                        print(f"  原始数据: {json.dumps(bill_data.get('raw_data', {}), ensure_ascii=False)}")
                        print(f"  分类: {bill_data.get('category_name', 'None')}")
                        print()
        else:
            print(f"上传失败: {response.status_code}")
            print(f"错误信息: {result.get('message', 'N/A')}")
            
    finally:
        # 清理临时文件
        if os.path.exists(csv_file_path):
            os.unlink(csv_file_path)
            print(f"清理临时文件: {csv_file_path}")

if __name__ == "__main__":
    test_jd_import_with_fix()