#!/usr/bin/env python3
"""
调试招商银行PDF上传失败记录的脚本
"""

import os
import sys
import requests
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from backend.parsers.cmb_parser import CMBParser
from backend.parsers.base_parser import BaseParser

def test_cmb_parser_directly():
    """直接测试CMB解析器，查看失败的记录"""
    print("=== 直接测试CMB解析器 ===")
    
    # 测试文件路径
    test_file = "/Users/chenxing/projects/my-bills-2/bills/招商银行交易流水(申请时间2025年07月05日10时27分05秒).pdf"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    print(f"测试文件: {test_file}")
    
    # 创建解析器实例
    parser = CMBParser()
    
    try:
        # 解析文件
        result = parser.parse_file(test_file)
        
        print(f"解析结果:")
        print(f"  成功记录数: {len(result.success_records)}")
        print(f"  失败记录数: {len(result.failed_records)}")
        print(f"  错误信息: {result.errors}")
        
        # 显示失败的记录
        if result.failed_records:
            print("\n=== 失败的记录 ===")
            for i, failed_record in enumerate(result.failed_records):
                print(f"失败记录 {i+1}:")
                if isinstance(failed_record, dict):
                    for key, value in failed_record.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {failed_record}")
                print()
        
        # 检查成功记录中是否有问题
        print("\n=== 检查成功记录的字段完整性 ===")
        required_fields = ["amount", "transaction_time", "transaction_type"]
        
        for i, record in enumerate(result.success_records):
            missing_fields = [field for field in required_fields if field not in record or record[field] is None]
            
            if missing_fields:
                print(f"记录 {i+1} 缺少必需字段: {missing_fields}")
                print(f"  记录内容: {record}")
                print()
            
            # 检查数据类型
            if "amount" in record and record["amount"] is not None:
                try:
                    float(record["amount"])
                except (ValueError, TypeError) as e:
                    print(f"记录 {i+1} 金额字段类型错误: {record['amount']}, 错误: {e}")
                    print(f"  记录内容: {record}")
                    print()
            
            # 检查交易时间
            if "transaction_time" in record and record["transaction_time"] is not None:
                if not hasattr(record["transaction_time"], 'isoformat'):
                    print(f"记录 {i+1} 交易时间字段类型错误: {record['transaction_time']}")
                    print(f"  记录内容: {record}")
                    print()
        
        print("=== 解析器测试完成 ===")
        
    except Exception as e:
        print(f"❌ 解析器测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_upload_with_debug():
    """测试上传并获取详细的错误信息"""
    print("\n=== 测试上传API ===")
    
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # 登录获取token
    login_data = {
        "username": "cmbtest",
        "password": "testpass123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/auth/login", data=login_data)
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            print(f"响应内容: {login_response.text}")
            return
        
        login_result = login_response.json()
        access_token = login_result["data"]["access_token"]
        print("✅ 登录成功")
        
        # 获取家庭列表
        headers = {"Authorization": f"Bearer {access_token}"}
        families_response = requests.get(f"{base_url}/families/", headers=headers)
        
        if families_response.status_code != 200:
            print(f"❌ 获取家庭列表失败: {families_response.status_code}")
            return
        
        families = families_response.json()["data"]
        if not families:
            print("❌ 没有找到家庭")
            return
        
        family_id = families[0]["id"]
        print(f"✅ 使用家庭ID: {family_id}")
        
        # 上传文件
        test_file = "/Users/chenxing/projects/my-bills-2/bills/招商银行交易流水(申请时间2025年07月05日10时27分05秒).pdf"
        
        with open(test_file, 'rb') as f:
            files = {'file': ('招商银行交易流水.pdf', f, 'application/pdf')}
            data = {
                'family_id': family_id,
                'source_type': 'cmb',
                'auto_categorize': True
            }
            
            upload_response = requests.post(
                f"{base_url}/upload/",
                files=files,
                data=data,
                headers=headers
            )
        
        print(f"上传响应状态码: {upload_response.status_code}")
        
        if upload_response.status_code == 200:
            result = upload_response.json()
            print("上传结果:")
            print(f"  总记录数: {result['total_records']}")
            print(f"  成功记录数: {result['success_count']}")
            print(f"  失败记录数: {result['failed_count']}")
            print(f"  状态: {result['status']}")
            
            if result.get('errors'):
                print("  错误信息:")
                for error in result['errors']:
                    print(f"    - {error}")
            
            if result.get('warnings'):
                print("  警告信息:")
                for warning in result['warnings']:
                    print(f"    - {warning}")
        else:
            print(f"❌ 上传失败: {upload_response.text}")
    
    except Exception as e:
        print(f"❌ 上传测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始调试招商银行PDF上传失败记录...")
    
    # 首先直接测试解析器
    test_cmb_parser_directly()
    
    # 然后测试上传API
    test_upload_with_debug()
    
    print("\n调试完成！")