#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的支付宝账单导入测试
直接测试上传功能，不需要认证
"""

import subprocess
import os
import json

def test_alipay_upload():
    """使用curl测试支付宝账单上传"""
    
    # 切换到tests目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 测试文件路径
    test_file = "test_alipay_bills.csv"
    
    print(f"开始测试支付宝账单上传...")
    
    # 检查测试文件是否存在
    if not os.path.exists(test_file):
        print(f"错误: 测试文件 {test_file} 不存在")
        return False
    
    try:
        # 使用curl上传文件（跳过认证）
        curl_cmd = [
            'curl', '-X', 'POST',
            'http://localhost:8000/api/v1/upload/',
            '-F', f'file=@{test_file}',
            '-F', 'source_type=alipay',
            '-F', 'auto_categorize=true',
            '-H', 'Authorization: Bearer fake_token_for_test'  # 使用假token测试
        ]
        
        print(f"执行命令: {' '.join(curl_cmd)}")
        result = subprocess.run(curl_cmd, capture_output=True, text=True)
        
        print(f"返回码: {result.returncode}")
        print(f"响应内容: {result.stdout}")
        
        if result.stderr:
            print(f"错误信息: {result.stderr}")
        
        # 尝试解析JSON响应
        try:
            response_data = json.loads(result.stdout)
            print(f"解析后的响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            
            if response_data.get('success'):
                print("✅ 上传成功!")
                return True
            else:
                print(f"❌ 上传失败: {response_data.get('message')}")
                return False
                
        except json.JSONDecodeError:
            print("❌ 响应不是有效的JSON格式")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_alipay_upload()
    if success:
        print("\n🎉 支付宝账单上传测试通过!")
    else:
        print("\n💥 支付宝账单上传测试失败!")