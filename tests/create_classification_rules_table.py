#!/usr/bin/env python3
"""
创建分类规则表的脚本
支持基于自然语言的账单分类规则配置
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import asyncio
import asyncpg
from config.settings import settings

async def create_classification_rules_table():
    """创建分类规则表"""
    
    # 连接数据库
    database_url = settings.DATABASE_URL
    conn = await asyncpg.connect(database_url)
    
    try:
        print("开始创建分类规则表...")
        
        # 创建分类规则表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS classification_rules (
            id SERIAL PRIMARY KEY,
            rule_text TEXT NOT NULL,
            source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('alipay', 'jd', 'cmb', 'all')),
            target_category VARCHAR(50) NOT NULL,
            priority INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT true,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT unique_rule_per_source UNIQUE(rule_text, source_type)
        );
        """
        
        await conn.execute(create_table_sql)
        print("✅ 分类规则表创建成功")
        
        # 创建索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_classification_rules_source_type ON classification_rules(source_type);",
            "CREATE INDEX IF NOT EXISTS idx_classification_rules_active ON classification_rules(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_classification_rules_priority ON classification_rules(priority DESC);",
        ]
        
        for index_sql in indexes:
            await conn.execute(index_sql)
        
        print("✅ 索引创建成功")
        
        # 创建更新时间触发器
        trigger_sql = """
        CREATE TRIGGER update_classification_rules_updated_at 
        BEFORE UPDATE ON classification_rules
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        try:
            await conn.execute(trigger_sql)
            print("✅ 更新时间触发器创建成功")
        except Exception as e:
            if "already exists" in str(e):
                print("⚠️  更新时间触发器已存在")
            else:
                print(f"❌ 创建触发器失败: {e}")
        
        # 插入一些示例规则
        sample_rules = [
            {
                'rule_text': '招商银行账单中对手方含有"信雅达"关键字的收入是"工资收入"',
                'source_type': 'cmb',
                'target_category': '工资收入',
                'priority': 10
            },
            {
                'rule_text': '支付宝账单中描述包含"红包"的收入是"其他收入"',
                'source_type': 'alipay', 
                'target_category': '其他收入',
                'priority': 5
            },
            {
                'rule_text': '任何包含"基金赎回"的收入都是"投资收益"',
                'source_type': 'all',
                'target_category': '投资收益',
                'priority': 8
            },
            {
                'rule_text': '京东账单中商户名包含"京东"且金额为负数的是"网购消费"',
                'source_type': 'jd',
                'target_category': '网购消费',
                'priority': 6
            },
            {
                'rule_text': '招商银行账单中描述包含"理财"的支出是"投资理财"',
                'source_type': 'cmb',
                'target_category': '投资理财',
                'priority': 7
            }
        ]
        
        for rule in sample_rules:
            insert_sql = """
            INSERT INTO classification_rules (rule_text, source_type, target_category, priority)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (rule_text, source_type) DO NOTHING;
            """
            await conn.execute(insert_sql, 
                             rule['rule_text'], 
                             rule['source_type'], 
                             rule['target_category'], 
                             rule['priority'])
        
        print("✅ 示例规则插入成功")
        
        # 查询并显示创建的规则
        rules = await conn.fetch("""
            SELECT id, rule_text, source_type, target_category, priority, is_active
            FROM classification_rules 
            ORDER BY priority DESC, id
        """)
        
        print("\n📋 当前分类规则:")
        print("-" * 100)
        for rule in rules:
            print(f"ID: {rule['id']}")
            print(f"规则: {rule['rule_text']}")
            print(f"来源: {rule['source_type']}")
            print(f"目标分类: {rule['target_category']}")
            print(f"优先级: {rule['priority']}")
            print(f"状态: {'✅ 启用' if rule['is_active'] else '❌ 禁用'}")
            print("-" * 100)
        
        # 显示表结构
        table_info = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'classification_rules'
            ORDER BY ordinal_position;
        """)
        
        print("\n📊 表结构:")
        print("-" * 80)
        for col in table_info:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"{col['column_name']:<20} {col['data_type']:<15} {nullable:<10}{default}")
        
    except Exception as e:
        print(f"❌ 创建分类规则表失败: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_classification_rules_table())