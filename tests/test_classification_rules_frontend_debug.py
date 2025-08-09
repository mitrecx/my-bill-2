#!/usr/bin/env python3
"""
测试分类规则前端API调用问题
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login():
    """登录获取token"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"登录响应状态码: {response.status_code}")
    print(f"登录响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and data.get("data"):
            access_token = data["data"].get("access_token")
            if access_token:
                print("✅ 登录成功")
                return access_token
    
    print("❌ 登录失败")
    return None

def test_source_type_options(token):
    """测试获取来源类型选项"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== 测试获取来源类型选项 ===")
    response = requests.get(f"{BASE_URL}/classification-rules/source-types/options", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            source_types = data.get("data", {}).get("source_types", [])
            print(f"✅ 获取来源类型选项成功，共 {len(source_types)} 个选项:")
            for option in source_types:
                print(f"  - {option.get('value')}: {option.get('label')}")
            return source_types
        else:
            print(f"❌ API返回失败: {data.get('message')}")
    else:
        print(f"❌ 请求失败")
    
    return []

def test_get_rules(token):
    """测试获取分类规则列表"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== 测试获取分类规则列表 ===")
    response = requests.get(f"{BASE_URL}/classification-rules/", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            rules_data = data.get("data", {})
            rules = rules_data.get("rules", [])
            total = rules_data.get("total", 0)
            print(f"✅ 获取分类规则列表成功，共 {total} 条规则:")
            for rule in rules[:5]:  # 只显示前5条
                print(f"  - ID: {rule.get('id')}, 规则: {rule.get('rule_text')}, 来源: {rule.get('source_type')}")
            return rules
        else:
            print(f"❌ API返回失败: {data.get('message')}")
    else:
        print(f"❌ 请求失败")
    
    return []

def test_get_categories(token):
    """测试获取账单分类"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== 测试获取账单分类 ===")
    response = requests.get(f"{BASE_URL}/bills/categories", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            categories = data.get("data", [])
            print(f"✅ 获取账单分类成功，共 {len(categories)} 个分类:")
            for category in categories[:5]:  # 只显示前5个
                print(f"  - {category.get('name')} ({category.get('category_type')})")
            return categories
        else:
            print(f"❌ API返回失败: {data.get('message')}")
    else:
        print(f"❌ 请求失败")
    
    return []

def test_create_rule(token, categories):
    """测试创建分类规则"""
    if not categories:
        print("\n❌ 没有可用的分类，跳过创建规则测试")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 选择第一个支出分类
    target_category = None
    for cat in categories:
        if cat.get('category_type') == 'expense':
            target_category = cat.get('name')
            break
    
    if not target_category:
        print("\n❌ 没有找到支出分类，跳过创建规则测试")
        return
    
    import time
    timestamp = int(time.time())
    rule_data = {
        "rule_text": f"测试规则文本_{timestamp}",
        "source_type": "all",
        "target_category": target_category,
        "priority": 1,
        "is_active": True
    }
    
    print(f"\n=== 测试创建分类规则 ===")
    print(f"规则数据: {json.dumps(rule_data, ensure_ascii=False, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/classification-rules/", json=rule_data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            rule = data.get("data")
            print(f"✅ 创建分类规则成功，ID: {rule.get('id')}")
            return rule
        else:
            print(f"❌ API返回失败: {data.get('message')}")
    else:
        print(f"❌ 请求失败")
    
    return None

def main():
    print("开始测试分类规则API...")
    
    # 1. 登录
    token = login()
    if not token:
        return
    
    # 2. 测试获取来源类型选项
    source_types = test_source_type_options(token)
    
    # 3. 测试获取分类规则列表
    rules = test_get_rules(token)
    
    # 4. 测试获取账单分类
    categories = test_get_categories(token)
    
    # 5. 测试创建分类规则
    new_rule = test_create_rule(token, categories)
    
    print("\n=== 测试总结 ===")
    print(f"来源类型选项数量: {len(source_types)}")
    print(f"现有规则数量: {len(rules)}")
    print(f"账单分类数量: {len(categories)}")
    print(f"创建新规则: {'成功' if new_rule else '失败'}")

if __name__ == "__main__":
    main()