#!/usr/bin/env python3
"""
测试CMB文件上传时描述字段的组合
"""

import requests
import json
import os
import tempfile

BASE_URL = "http://127.0.0.1:8000/api/v1"

def login():
    """用户登录"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result["data"]["access_token"]
    
    print(f"登录失败: {response.status_code} - {response.text}")
    return None

def create_test_cmb_file():
    """创建测试用的CMB账单文件"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        # 创建临时PDF文件
        temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_file.close()
        
        # 创建PDF
        c = canvas.Canvas(temp_file.name, pagesize=letter)
        
        # 添加文本内容 - 使用CMB解析器期望的格式
        y_position = 750
        lines = [
            "2024-01-15",
            "CNY", 
            "-128.50",
            "5000.00",
            "快捷支付",
            "美团外卖",
            "2024-01-16",
            "CNY",
            "-89.90", 
            "4910.10",
            "网上支付",
            "京东商城",
            "2024-01-17",
            "CNY",
            "+2000.00",
            "6910.10", 
            "转账汇款",
            "工资发放",
            "2024-01-18",
            "CNY",
            "-45.60",
            "6864.50",
            "刷卡消费",
            "星巴克咖啡"
        ]
        
        for line in lines:
            c.drawString(100, y_position, line)
            y_position -= 20
        
        c.save()
        return temp_file.name
        
    except ImportError:
        # 如果没有reportlab，创建一个简单的文本文件
        print("警告: 未安装reportlab，使用文本文件代替PDF")
        cmb_content = """2024-01-15
CNY
-128.50
5000.00
快捷支付
美团外卖
2024-01-16
CNY
-89.90
4910.10
网上支付
京东商城
2024-01-17
CNY
+2000.00
6910.10
转账汇款
工资发放
2024-01-18
CNY
-45.60
6864.50
刷卡消费
星巴克咖啡
"""
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
        temp_file.write(cmb_content)
        temp_file.close()
        
        return temp_file.name

def upload_cmb_file(token, file_path):
    """上传CMB文件"""
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(file_path, 'rb') as f:
        files = {'file': ('cmb_test.csv', f, 'text/csv')}
        data = {'source_type': 'cmb'}
        
        response = requests.post(f"{BASE_URL}/upload/", files=files, data=data, headers=headers)
    
    return response

def get_recent_bills(token, limit=10):
    """获取最近的账单"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/bills?page=1&page_size={limit}", headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result["data"]["items"]
    
    return []

def delete_bill(token, bill_id):
    """删除账单"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.delete(f"{BASE_URL}/bills/{bill_id}", headers=headers)
    return response.status_code == 200

def main():
    print("=== 测试CMB文件上传描述字段组合 ===")
    
    # 登录
    token = login()
    if not token:
        print("登录失败，无法继续测试")
        return
    
    print("✓ 用户登录成功")
    
    # 创建测试文件
    test_file = create_test_cmb_file()
    print(f"✓ 创建测试文件: {test_file}")
    
    try:
        # 记录上传前的账单数量
        bills_before = get_recent_bills(token, 20)
        bills_before_ids = {bill['id'] for bill in bills_before}
        
        # 上传文件
        print("\n--- 上传CMB文件 ---")
        response = upload_cmb_file(token, test_file)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✓ 文件上传成功")
                print(f"上传结果: {result['data']}")
                
                # 获取新创建的账单
                bills_after = get_recent_bills(token, 20)
                new_bills = [bill for bill in bills_after if bill['id'] not in bills_before_ids]
                
                print(f"\n--- 检查新创建的账单 ({len(new_bills)}条) ---")
                
                expected_descriptions = [
                    "快捷支付-美团外卖",
                    "网上支付-京东商城", 
                    "转账汇款-工资发放",
                    "刷卡消费-星巴克咖啡"
                ]
                
                created_bill_ids = []
                
                for i, bill in enumerate(new_bills):
                    bill_id = bill['id']
                    created_bill_ids.append(bill_id)
                    
                    print(f"\n账单 {bill_id}:")
                    print(f"  金额: {bill['amount']}")
                    print(f"  类型: {bill['transaction_type']}")
                    print(f"  描述: {bill.get('transaction_desc', 'N/A')}")
                    print(f"  对手: {bill.get('counter_party', 'N/A')}")
                    print(f"  日期: {bill['transaction_date']}")
                    
                    # 检查描述字段是否正确组合
                    actual_desc = bill.get('transaction_desc', '')
                    if i < len(expected_descriptions):
                        expected_desc = expected_descriptions[i]
                        if expected_desc in actual_desc or actual_desc == expected_desc:
                            print(f"  ✓ 描述字段组合正确")
                        else:
                            print(f"  ✗ 描述字段组合错误，期望包含: {expected_desc}")
                    
                # 清理测试数据
                print(f"\n=== 清理测试数据 ===")
                for bill_id in created_bill_ids:
                    if delete_bill(token, bill_id):
                        print(f"✓ 删除账单 {bill_id}")
                    else:
                        print(f"✗ 删除账单 {bill_id} 失败")
                        
            else:
                print(f"✗ 文件上传失败: {result}")
        else:
            print(f"✗ 文件上传失败: {response.status_code} - {response.text}")
            
    finally:
        # 删除测试文件
        if os.path.exists(test_file):
            os.unlink(test_file)
            print(f"✓ 删除测试文件: {test_file}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()