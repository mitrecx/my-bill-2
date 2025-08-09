#!/usr/bin/env python3
"""
测试分类规则API功能
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# API基础URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

# 测试用户凭据
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

class ClassificationRulesAPITester:
    def __init__(self):
        self.session = None
        self.token = None
        self.headers = {}
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login(self) -> bool:
        """登录获取token"""
        try:
            login_data = {
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
            
            async with self.session.post(
                f"{BASE_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.token = result["data"]["access_token"]
                    self.headers = {"Authorization": f"Bearer {self.token}"}
                    print("✅ 登录成功")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 登录失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False
    
    async def test_get_source_types(self):
        """测试获取来源类型选项"""
        print("\n🔍 测试获取来源类型选项...")
        
        try:
            async with self.session.get(
                f"{BASE_URL}/classification-rules/source-types/options",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 获取来源类型选项成功:")
                    for source_type in result["source_types"]:
                        print(f"   - {source_type['value']}: {source_type['label']}")
                    return True
                else:
                    print(f"❌ 获取来源类型选项失败: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 获取来源类型选项异常: {e}")
            return False
    
    async def test_create_rule(self) -> Dict[str, Any]:
        """测试创建分类规则"""
        print("\n🔍 测试创建分类规则...")
        
        rule_data = {
            "rule_text": "测试规则：支付宝账单中描述包含'测试'的收入是'其他收入'",
            "source_type": "alipay",
            "target_category": "其他收入",
            "priority": 5,
            "is_active": True
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/classification-rules/",
                headers=self.headers,
                json=rule_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 创建分类规则成功:")
                    print(f"   ID: {result['id']}")
                    print(f"   规则: {result['rule_text']}")
                    print(f"   来源: {result['source_type']}")
                    print(f"   目标分类: {result['target_category']}")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ 创建分类规则失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return None
        except Exception as e:
            print(f"❌ 创建分类规则异常: {e}")
            return None
    
    async def test_get_rules(self):
        """测试获取分类规则列表"""
        print("\n🔍 测试获取分类规则列表...")
        
        try:
            async with self.session.get(
                f"{BASE_URL}/classification-rules/",
                headers=self.headers,
                params={"page": 1, "page_size": 10}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 获取分类规则列表成功:")
                    print(f"   总数: {result['total']}")
                    print(f"   当前页: {result['page']}")
                    print(f"   每页数量: {result['page_size']}")
                    print("   规则列表:")
                    for rule in result['rules']:
                        status = "✅ 启用" if rule['is_active'] else "❌ 禁用"
                        print(f"   - ID {rule['id']}: {rule['rule_text'][:50]}... ({rule['source_type']}) {status}")
                    return result
                else:
                    print(f"❌ 获取分类规则列表失败: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ 获取分类规则列表异常: {e}")
            return None
    
    async def test_update_rule(self, rule_id: int):
        """测试更新分类规则"""
        print(f"\n🔍 测试更新分类规则 (ID: {rule_id})...")
        
        update_data = {
            "priority": 10,
            "is_active": False
        }
        
        try:
            async with self.session.put(
                f"{BASE_URL}/classification-rules/{rule_id}",
                headers=self.headers,
                json=update_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 更新分类规则成功:")
                    print(f"   优先级: {result['priority']}")
                    print(f"   状态: {'✅ 启用' if result['is_active'] else '❌ 禁用'}")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ 更新分类规则失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return None
        except Exception as e:
            print(f"❌ 更新分类规则异常: {e}")
            return None
    
    async def test_toggle_rule(self, rule_id: int):
        """测试切换分类规则状态"""
        print(f"\n🔍 测试切换分类规则状态 (ID: {rule_id})...")
        
        try:
            async with self.session.post(
                f"{BASE_URL}/classification-rules/{rule_id}/toggle",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 切换分类规则状态成功:")
                    print(f"   消息: {result['message']}")
                    print(f"   当前状态: {'✅ 启用' if result['is_active'] else '❌ 禁用'}")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ 切换分类规则状态失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return None
        except Exception as e:
            print(f"❌ 切换分类规则状态异常: {e}")
            return None
    
    async def test_delete_rule(self, rule_id: int):
        """测试删除分类规则"""
        print(f"\n🔍 测试删除分类规则 (ID: {rule_id})...")
        
        try:
            async with self.session.delete(
                f"{BASE_URL}/classification-rules/{rule_id}",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 删除分类规则成功:")
                    print(f"   消息: {result['message']}")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ 删除分类规则失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return None
        except Exception as e:
            print(f"❌ 删除分类规则异常: {e}")
            return None
    
    async def test_batch_create_rules(self):
        """测试批量创建分类规则"""
        print("\n🔍 测试批量创建分类规则...")
        
        batch_data = {
            "rules": [
                {
                    "rule_text": "新批量测试规则1：支付宝账单中商户名包含'美团'的支出是'餐饮消费'",
                    "source_type": "alipay",
                    "target_category": "餐饮消费",
                    "priority": 3
                },
                {
                    "rule_text": "新批量测试规则2：招商银行账单中描述包含'房贷'的支出是'房贷还款'",
                    "source_type": "cmb",
                    "target_category": "房贷还款",
                    "priority": 4
                }
            ]
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/classification-rules/batch",
                headers=self.headers,
                json=batch_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 批量创建分类规则成功:")
                    for rule in result:
                        print(f"   - ID {rule['id']}: {rule['rule_text'][:50]}...")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ 批量创建分类规则失败: {response.status}")
                    print(f"   错误信息: {error_text}")
                    return None
        except Exception as e:
            print(f"❌ 批量创建分类规则异常: {e}")
            return None

async def main():
    """主测试函数"""
    print("🚀 开始测试分类规则API...")
    
    async with ClassificationRulesAPITester() as tester:
        # 1. 登录
        if not await tester.login():
            print("❌ 登录失败，终止测试")
            return
        
        # 2. 测试获取来源类型选项
        await tester.test_get_source_types()
        
        # 3. 测试获取现有规则列表
        await tester.test_get_rules()
        
        # 4. 测试创建单个规则
        created_rule = await tester.test_create_rule()
        
        if created_rule:
            rule_id = created_rule['id']
            
            # 5. 测试更新规则
            await tester.test_update_rule(rule_id)
            
            # 6. 测试切换规则状态
            await tester.test_toggle_rule(rule_id)
            
            # 7. 测试删除规则
            await tester.test_delete_rule(rule_id)
        
        # 8. 测试批量创建规则
        batch_rules = await tester.test_batch_create_rules()
        
        # 9. 再次获取规则列表查看最终结果
        print("\n🔍 最终规则列表:")
        await tester.test_get_rules()
    
    print("\n✅ 分类规则API测试完成！")

if __name__ == "__main__":
    asyncio.run(main())