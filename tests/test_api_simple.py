#!/usr/bin/env python3
"""
简单的API测试，验证后端服务是否正常工作
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_health_check():
    """测试健康检查接口"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 健康检查接口正常")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_login():
    """测试登录接口"""
    try:
        login_data = {
            "username": "test@example.com",
            "password": "testpassword"
        }
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", 
                               json=login_data, timeout=5)
        
        # 即使登录失败（用户不存在），只要接口能响应就说明服务正常
        if response.status_code in [200, 401, 422]:
            print("✅ 登录接口响应正常")
            return True
        else:
            print(f"❌ 登录接口异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 登录接口异常: {e}")
        return False

def test_docs():
    """测试API文档接口"""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API文档接口正常")
            return True
        else:
            print(f"❌ API文档接口失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API文档接口异常: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 简单API测试 ===\n")
    
    # 等待服务完全启动
    print("等待后端服务启动...")
    time.sleep(2)
    
    results = []
    
    # 测试健康检查
    results.append(test_health_check())
    
    # 测试登录接口
    results.append(test_login())
    
    # 测试API文档
    results.append(test_docs())
    
    print(f"\n=== 测试结果汇总 ===")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ 所有API测试通过 ({passed}/{total})")
        print("✅ 后端服务运行正常")
    else:
        print(f"❌ 部分API测试失败 ({passed}/{total})")
        print("❌ 后端服务可能存在问题")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)