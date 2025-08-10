#!/usr/bin/env python3
"""
测试AI分类批次大小更改
验证批次大小从10个改为20个是否生效
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.ai_classification_service import AIClassificationService
from config.database import SessionLocal
import inspect

def test_batch_size_change():
    """测试批次大小更改"""
    print("=== 测试AI分类批次大小更改 ===")
    
    # 创建AI分类服务实例
    ai_service = AIClassificationService()
    
    # 检查方法签名中的默认参数
    method = ai_service.classify_bills_batch_optimized
    signature = inspect.signature(method)
    
    batch_size_param = signature.parameters.get('batch_size')
    if batch_size_param:
        default_value = batch_size_param.default
        print(f"✓ 找到batch_size参数，默认值: {default_value}")
        
        if default_value == 20:
            print("✅ 批次大小已成功更改为20")
            return True
        elif default_value == 10:
            print("❌ 批次大小仍然是10，更改未生效")
            return False
        else:
            print(f"⚠️  批次大小是意外的值: {default_value}")
            return False
    else:
        print("❌ 未找到batch_size参数")
        return False

def test_method_docstring():
    """测试方法文档字符串是否已更新"""
    print("\n=== 测试方法文档字符串 ===")
    
    ai_service = AIClassificationService()
    method = ai_service.classify_bills_batch_optimized
    
    docstring = method.__doc__
    if docstring:
        if "默认20个" in docstring:
            print("✅ 方法文档字符串已更新为20个")
            return True
        elif "默认10个" in docstring:
            print("❌ 方法文档字符串仍然显示10个")
            return False
        else:
            print("⚠️  文档字符串中未找到批次大小描述")
            return False
    else:
        print("❌ 方法没有文档字符串")
        return False

def test_single_request_docstring():
    """测试单次请求方法的文档字符串"""
    print("\n=== 测试单次请求方法文档字符串 ===")
    
    ai_service = AIClassificationService()
    method = ai_service._classify_bills_batch_single_request
    
    docstring = method.__doc__
    if docstring:
        if "最多20个" in docstring:
            print("✅ 单次请求方法文档字符串已更新为20个")
            return True
        elif "最多10个" in docstring:
            print("❌ 单次请求方法文档字符串仍然显示10个")
            return False
        else:
            print("⚠️  文档字符串中未找到批次大小描述")
            return False
    else:
        print("❌ 方法没有文档字符串")
        return False

if __name__ == "__main__":
    print("开始测试AI分类批次大小更改...")
    
    success_count = 0
    total_tests = 3
    
    # 测试默认参数
    if test_batch_size_change():
        success_count += 1
    
    # 测试文档字符串
    if test_method_docstring():
        success_count += 1
        
    if test_single_request_docstring():
        success_count += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过测试: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！AI分类批次大小已成功更改为20个")
    else:
        print("⚠️  部分测试未通过，请检查代码更改")