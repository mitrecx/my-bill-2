#!/usr/bin/env python3
"""
测试真实的分类规则
创建一些常用的分类规则并测试
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from config.database import get_db
from models.bill import BillCategory
from models.classification_rule import ClassificationRule
from services.rule_classification_service import rule_classification_service
from services.ai_classification_service import ai_classification_service


def create_common_classification_rules():
    """创建常用的分类规则"""
    print("=== 创建常用分类规则 ===")
    
    db = next(get_db())
    
    try:
        # 常用分类规则
        common_rules = [
            # 交通出行
            {
                'rule_text': '关键词: 滴滴,打车,出租车,网约车,快车,专车',
                'source_type': 'all',
                'target_category': '交通出行',
                'priority': 10,
                'is_active': True
            },
            {
                'rule_text': '关键词: 地铁,公交,公共交通,一卡通',
                'source_type': 'all',
                'target_category': '交通出行',
                'priority': 9,
                'is_active': True
            },
            {
                'rule_text': '关键词: 加油,中石油,中石化,壳牌',
                'source_type': 'all',
                'target_category': '交通出行',
                'priority': 8,
                'is_active': True
            },
            
            # 餐饮美食
            {
                'rule_text': '关键词: 美团,饿了么,外卖,餐厅,咖啡,奶茶',
                'source_type': 'all',
                'target_category': '餐饮美食',
                'priority': 10,
                'is_active': True
            },
            {
                'rule_text': '关键词: 麦当劳,肯德基,星巴克,瑞幸',
                'source_type': 'all',
                'target_category': '餐饮美食',
                'priority': 9,
                'is_active': True
            },
            
            # 日用百货
            {
                'rule_text': '关键词: 超市,便利店,7-11,全家,罗森',
                'source_type': 'all',
                'target_category': '日用百货',
                'priority': 10,
                'is_active': True
            },
            {
                'rule_text': '关键词: 沃尔玛,家乐福,大润发,华润万家',
                'source_type': 'all',
                'target_category': '日用百货',
                'priority': 9,
                'is_active': True
            },
            
            # 医疗保健
            {
                'rule_text': '关键词: 医院,挂号费,药费,体检,诊疗',
                'source_type': 'all',
                'target_category': '医疗保健',
                'priority': 10,
                'is_active': True
            },
            {
                'rule_text': '关键词: 药店,药房,同仁堂,海王星辰',
                'source_type': 'all',
                'target_category': '医疗保健',
                'priority': 9,
                'is_active': True
            },
            
            # 投资收益
            {
                'rule_text': '关键词: 基金,理财,股票,债券,分红',
                'source_type': 'all',
                'target_category': '投资收益',
                'priority': 10,
                'is_active': True
            },
            {
                'rule_text': '关键词: 余额宝,理财通,定期存款',
                'source_type': 'all',
                'target_category': '投资收益',
                'priority': 9,
                'is_active': True
            },
            
            # 工资薪酬
            {
                'rule_text': '关键词: 工资,薪资,薪酬,奖金,津贴',
                'source_type': 'all',
                'target_category': '工资薪酬',
                'priority': 10,
                'is_active': True
            },
            
            # 娱乐休闲
            {
                'rule_text': '关键词: 电影,KTV,游戏,娱乐,健身',
                'source_type': 'all',
                'target_category': '娱乐休闲',
                'priority': 10,
                'is_active': True
            },
            {
                'rule_text': '关键词: 腾讯,网易,Steam,Apple,App Store',
                'source_type': 'all',
                'target_category': '娱乐休闲',
                'priority': 9,
                'is_active': True
            },
            
            # 服装美容
            {
                'rule_text': '关键词: 淘宝,天猫,京东,拼多多,唯品会',
                'source_type': 'all',
                'target_category': '服装美容',
                'priority': 8,
                'is_active': True
            },
            {
                'rule_text': '关键词: 美容,化妆品,护肤,理发,美发',
                'source_type': 'all',
                'target_category': '服装美容',
                'priority': 9,
                'is_active': True
            }
        ]
        
        # 检查是否已存在规则，避免重复创建
        existing_count = db.query(ClassificationRule).filter(
            ClassificationRule.rule_text.like('%关键词:%')
        ).count()
        
        if existing_count > 0:
            print(f"已存在 {existing_count} 条类似规则，跳过创建")
            return
        
        # 创建规则
        created_count = 0
        for rule_data in common_rules:
            # 检查目标分类是否存在
            category = db.query(BillCategory).filter(
                BillCategory.category_name == rule_data['target_category']
            ).first()
            
            if category:
                rule = ClassificationRule(**rule_data)
                db.add(rule)
                created_count += 1
            else:
                print(f"警告: 分类 '{rule_data['target_category']}' 不存在，跳过规则创建")
        
        db.commit()
        print(f"成功创建 {created_count} 条分类规则")
        
    except Exception as e:
        print(f"创建分类规则失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_real_bills():
    """测试真实账单数据"""
    print("\n=== 测试真实账单数据 ===")
    
    db = next(get_db())
    
    try:
        # 真实账单测试数据
        real_bills = [
            {
                'id': 2001,
                'description': '滴滴出行-快车费用',
                'source_type': 'alipay',
                'transaction_type': '支出'
            },
            {
                'id': 2002,
                'description': '美团外卖-午餐',
                'source_type': 'alipay',
                'transaction_type': '支出'
            },
            {
                'id': 2003,
                'description': '7-11便利店',
                'source_type': 'cmb',
                'transaction_type': '支出'
            },
            {
                'id': 2004,
                'description': '医院挂号费',
                'source_type': 'alipay',
                'transaction_type': '支出'
            },
            {
                'id': 2005,
                'description': '基金分红到账',
                'source_type': 'cmb',
                'transaction_type': '收入'
            },
            {
                'id': 2006,
                'description': '公司工资发放',
                'source_type': 'cmb',
                'transaction_type': '收入'
            },
            {
                'id': 2007,
                'description': '星巴克咖啡',
                'source_type': 'alipay',
                'transaction_type': '支出'
            },
            {
                'id': 2008,
                'description': '中石化加油站',
                'source_type': 'cmb',
                'transaction_type': '支出'
            },
            {
                'id': 2009,
                'description': '腾讯游戏充值',
                'source_type': 'alipay',
                'transaction_type': '支出'
            },
            {
                'id': 2010,
                'description': '淘宝购物',
                'source_type': 'alipay',
                'transaction_type': '支出'
            }
        ]
        
        print("\n规则分类结果:")
        rule_classified = 0
        for bill in real_bills:
            category = rule_classification_service.apply_classification_rules(bill, db)
            if category:
                rule_classified += 1
                print(f"✓ 账单 {bill['id']} ({bill['description']}) -> {category}")
            else:
                print(f"✗ 账单 {bill['id']} ({bill['description']}) -> 无匹配规则")
        
        print(f"\n规则分类成功率: {rule_classified}/{len(real_bills)} ({rule_classified/len(real_bills)*100:.1f}%)")
        
        print("\nAI分类结果:")
        ai_classified = 0
        for bill in real_bills:
            category = ai_classification_service.classify_single_bill(bill, db)
            if category:
                ai_classified += 1
                print(f"✓ 账单 {bill['id']} ({bill['description']}) -> {category}")
            else:
                print(f"✗ 账单 {bill['id']} ({bill['description']}) -> 分类失败")
        
        print(f"\n总分类成功率: {ai_classified}/{len(real_bills)} ({ai_classified/len(real_bills)*100:.1f}%)")
        
        # 测试批量分类
        print("\n批量分类结果:")
        batch_results = ai_classification_service.classify_bills_batch_optimized(real_bills, db)
        batch_classified = 0
        for bill_id, category in batch_results:
            bill = next(b for b in real_bills if b['id'] == bill_id)
            if category:
                batch_classified += 1
                print(f"✓ 账单 {bill_id} ({bill['description']}) -> {category}")
            else:
                print(f"✗ 账单 {bill_id} ({bill['description']}) -> 分类失败")
        
        print(f"\n批量分类成功率: {batch_classified}/{len(real_bills)} ({batch_classified/len(real_bills)*100:.1f}%)")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def show_rule_statistics():
    """显示规则统计信息"""
    print("\n=== 分类规则统计 ===")
    
    db = next(get_db())
    
    try:
        stats = rule_classification_service.get_rule_statistics(db)
        print(f"总规则数: {stats.get('total_rules', 0)}")
        print(f"启用规则数: {stats.get('active_rules', 0)}")
        print(f"禁用规则数: {stats.get('inactive_rules', 0)}")
        
        source_stats = stats.get('source_stats', {})
        print("\n按来源类型统计:")
        for source_type, count in source_stats.items():
            print(f"  {source_type}: {count} 条规则")
        
        # 显示所有启用的规则
        rules = db.query(ClassificationRule).filter(
            ClassificationRule.is_active == True
        ).order_by(ClassificationRule.priority.desc()).all()
        
        print(f"\n启用的规则列表 ({len(rules)} 条):")
        for rule in rules:
            print(f"  [{rule.priority}] {rule.source_type} -> {rule.target_category}: {rule.rule_text}")
        
    except Exception as e:
        print(f"获取统计信息失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_common_classification_rules()
    show_rule_statistics()
    test_real_bills()