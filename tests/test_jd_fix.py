#!/usr/bin/env python3
"""
测试京东账单修复
验证order_id字段是否正确保存
"""

import os
import sys
import requests
import json
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_jd_upload_fix():
    """测试京东账单上传修复"""
    print("=" * 60)
    print("测试京东账单上传修复")
    print("=" * 60)
    
    # 配置
    base_url = "http://localhost:8000"
    
    # 查找京东账单文件
    bills_dir = Path(__file__).parent / "bills"
    jd_files = list(bills_dir.glob("*京东交易流水*.csv"))
    
    if not jd_files:
        print("❌ 未找到京东账单文件")
        return False
    
    jd_file = jd_files[0]
    print(f"使用文件: {jd_file.name}")
    
    try:
        # 1. 登录获取token
        print("\n步骤1: 登录获取token")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        login_response = requests.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            print(f"响应: {login_response.text}")
            return False
        
        token_data = login_response.json()
        print(f"登录响应: {token_data}")
        
        if not token_data.get("success"):
            print(f"❌ 登录失败: {token_data.get('message', '未知错误')}")
            return False
            
        token = token_data["data"]["access_token"]
        print("✅ 登录成功")
        
        # 2. 上传京东账单
        print("\n步骤2: 上传京东账单")
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        with open(jd_file, 'rb') as f:
            files = {
                "file": (jd_file.name, f, "text/csv")
            }
            data = {
                "family_id": 1,
                "auto_categorize": True
            }
            
            upload_response = requests.post(
                f"{base_url}/api/v1/upload/",
                headers=headers,
                files=files,
                data=data
            )
        
        if upload_response.status_code != 200:
            print(f"❌ 上传失败: {upload_response.status_code}")
            print(f"响应: {upload_response.text}")
            return False
        
        upload_result = upload_response.json()
        print("✅ 上传成功")
        print(f"总记录数: {upload_result['total_records']}")
        print(f"成功数: {upload_result['success_count']}")
        print(f"创建数: {upload_result['created_count']}")
        print(f"更新数: {upload_result['updated_count']}")
        print(f"失败数: {upload_result['failed_count']}")
        
        # 3. 验证数据库中的记录
        print("\n步骤3: 验证数据库记录")
        
        # 使用psql查询数据库
        import subprocess
        
        # 查询总记录数和order_id字段
        query = """
        SELECT 
            COUNT(*) as total_count,
            COUNT(order_id) as order_id_count,
            COUNT(DISTINCT order_id) as unique_order_count,
            COUNT(raw_data->>'order_id') as raw_order_id_count
        FROM bills 
        WHERE source_type = 'jd' AND source_filename = '%s';
        """ % jd_file.name
        
        cmd = [
            "psql", 
            "-h", "localhost", 
            "-U", "josie", 
            "-d", "bills_db", 
            "-c", query
        ]
        
        env = os.environ.copy()
        env["PGPASSWORD"] = "bills_password_2024"
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode != 0:
            print(f"❌ 数据库查询失败: {result.stderr}")
            return False
        
        print("数据库验证结果:")
        print(result.stdout)
        
        # 4. 查看几条记录的详细信息
        print("\n步骤4: 查看记录详细信息")
        
        detail_query = """
        SELECT 
            id,
            order_id,
            amount,
            transaction_desc,
            raw_data->>'order_id' as raw_order_id
        FROM bills 
        WHERE source_type = 'jd' AND source_filename = '%s'
        LIMIT 5;
        """ % jd_file.name
        
        cmd = [
            "psql", 
            "-h", "localhost", 
            "-U", "josie", 
            "-d", "bills_db", 
            "-c", detail_query
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            print("前5条记录详情:")
            print(result.stdout)
        else:
            print(f"❌ 详细查询失败: {result.stderr}")
        
        print("\n✅ 测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        return False

if __name__ == "__main__":
    success = test_jd_upload_fix()
    sys.exit(0 if success else 1)