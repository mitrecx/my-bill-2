#!/usr/bin/env python3
"""
测试优化后的AI分类服务：
1. 验证账单列表在提示词最后
2. 验证示例输出包含分类ID
3. 验证交易类型分类规则
4. 验证解析包含ID的输出格式
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from services.ai_classification_service import AIClassificationService
from config.database import get_db
from models.bill import BillCategory
from sqlalchemy.orm import Session

def test_single_bill_prompt_structure():
    """测试单个账单分类提示词结构"""
    print("测试单个账单分类提示词结构...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建AI分类服务实例
        ai_service = AIClassificationService()
        
        # 模拟账单数据
        test_bill = {
            'id': 12345,
            'amount': 100.50,
            'transaction_type': '支出',
            'description': '滴滴出行打车费',
            'source_type': 'cmb'
        }
        
        # 构建分类上下文
        categories_context = ai_service.get_categories_context(db)
        
        # 构建账单信息
        bill_info = f"""
账单信息：
- 账单ID: {test_bill.get('id', '未知')}
- 交易类型: {test_bill.get('transaction_type', '未知')}
- 描述: {test_bill.get('description', '无描述')}
- 来源: {test_bill.get('source_type', '未知')}
"""
        
        # 构建提示词
        prompt = f"""你是一个专业的账单分类助手。请根据账单信息选择最合适的分类。

{categories_context}

分类规则：
1. 仔细分析账单描述中的关键词
2. **重要：根据交易类型选择对应类别**
   - 交易类型为"收入"的账单，必须从收入类别中选择分类
   - 交易类型为"支出"的账单，必须从支出类别中选择分类
   - 不能混淆收入和支出类别
3. 优先匹配最具体、最相关的分类
4. 如果描述包含多个关键词，选择最主要的分类

示例：
- "午餐-麦当劳" (支出) → 食品餐饮 (ID: 8)
- "打车费用-滴滴出行" (支出) → 交通出行 (ID: 12)
- "日用品采购-天猫超市" (支出) → 日用百货 (ID: 11)
- "挂号费-人民医院" (支出) → 医疗保健 (ID: 14)
- "工资发放" (收入) → 工资收入 (ID: 1)

{bill_info}

请只返回分类名称，必须从上述分类列表中选择："""
        
        print("单个账单分类提示词:")
        print(prompt)
        print()
        
        # 检查账单信息是否在最后
        prompt_lines = prompt.strip().split('\n')
        bill_info_found = False
        bill_info_line_index = -1
        
        for i, line in enumerate(prompt_lines):
            if "账单信息：" in line:
                bill_info_found = True
                bill_info_line_index = i
                break
        
        if bill_info_found:
            # 检查账单信息是否在提示词的后半部分
            total_lines = len(prompt_lines)
            if bill_info_line_index > total_lines * 0.6:  # 在后40%的位置
                print("✅ 账单信息位于提示词的后部")
            else:
                print("❌ 账单信息不在提示词的后部")
        else:
            print("❌ 未找到账单信息")
            
        # 检查示例是否包含分类ID
        if "(ID:" in prompt:
            print("✅ 示例包含分类ID")
        else:
            print("❌ 示例不包含分类ID")
            
        # 检查交易类型规则
        if "交易类型为\"收入\"的账单，必须从收入类别中选择分类" in prompt:
            print("✅ 包含收入类别选择规则")
        else:
            print("❌ 缺少收入类别选择规则")
            
        if "交易类型为\"支出\"的账单，必须从支出类别中选择分类" in prompt:
            print("✅ 包含支出类别选择规则")
        else:
            print("❌ 缺少支出类别选择规则")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        db.close()

def test_batch_classification_prompt_structure():
    """测试批量分类提示词结构"""
    print("\n测试批量分类提示词结构...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建AI分类服务实例
        ai_service = AIClassificationService()
        
        # 模拟账单数据
        test_bills = [
            {
                'id': 12345,
                'transaction_type': '支出',
                'description': '滴滴出行打车费',
                'source_type': 'cmb'
            },
            {
                'id': 12346,
                'transaction_type': '收入',
                'description': '工资发放',
                'source_type': 'bank'
            }
        ]
        
        # 构建分类上下文
        categories_context = ai_service.get_categories_context(db)
        
        # 构建批量账单信息
        bills_info = "账单列表：\n"
        for i, bill_data in enumerate(test_bills, 1):
            bills_info += f"""
{i}. 账单ID: {bill_data.get('id', '未知')}
   - 交易类型: {bill_data.get('transaction_type', '未知')}
   - 描述: {bill_data.get('description', '无描述')}
   - 来源: {bill_data.get('source_type', '未知')}
"""
        
        # 构建提示词
        prompt = f"""你是一个专业的账单分类助手。请根据账单信息为每个账单选择最合适的分类。

{categories_context}

分类规则：
1. 仔细分析账单描述中的关键词
2. **重要：根据交易类型选择对应类别**
   - 交易类型为"收入"的账单，必须从收入类别中选择分类
   - 交易类型为"支出"的账单，必须从支出类别中选择分类
   - 不能混淆收入和支出类别
3. 优先匹配最具体、最相关的分类
4. 如果描述包含多个关键词，选择最主要的分类

示例输入：
1. 账单ID: 11244
   - 交易类型: 支出
   - 描述: 打车费用-滴滴出行
   - 来源: cmb

2. 账单ID: 11245
   - 交易类型: 支出
   - 描述: 挂号费
   - 来源: cmb

3. 账单ID: 11246
   - 交易类型: 收入
   - 描述: 基金赎回
   - 来源: cmb

示例输出：
11244: 交通出行 (ID: 12)
11245: 医疗保健 (ID: 14)
11246: 投资收益 (ID: 2)

{bills_info}

请按以下格式返回每个账单的分类结果，每行一个账单：
账单ID: 分类名称 (ID: 分类ID)

请严格按照上述格式返回，分类名称必须从上述分类列表中选择："""
        
        print("批量分类提示词:")
        print(prompt)
        print()
        
        # 检查账单列表是否在最后
        prompt_lines = prompt.strip().split('\n')
        bills_list_found = False
        bills_list_line_index = -1
        
        for i, line in enumerate(prompt_lines):
            if "账单列表：" in line:
                bills_list_found = True
                bills_list_line_index = i
                break
        
        if bills_list_found:
            # 检查账单列表是否在提示词的后半部分
            total_lines = len(prompt_lines)
            if bills_list_line_index > total_lines * 0.6:  # 在后40%的位置
                print("✅ 账单列表位于提示词的后部")
            else:
                print("❌ 账单列表不在提示词的后部")
        else:
            print("❌ 未找到账单列表")
            
        # 检查示例输出是否包含分类ID
        if "11244: 交通出行 (ID: 12)" in prompt:
            print("✅ 示例输出包含分类ID")
        else:
            print("❌ 示例输出不包含分类ID")
            
        # 检查输出格式要求
        if "账单ID: 分类名称 (ID: 分类ID)" in prompt:
            print("✅ 包含正确的输出格式要求")
        else:
            print("❌ 缺少正确的输出格式要求")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        db.close()

def test_parse_classification_result_with_id():
    """测试解析包含分类ID的分类结果"""
    print("\n测试解析包含分类ID的分类结果...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建AI分类服务实例
        ai_service = AIClassificationService()
        
        # 模拟AI返回的包含分类ID的响应
        ai_response = """12345: 交通出行 (ID: 12)
12346: 工资收入 (ID: 1)
12347: 食品餐饮 (ID: 8)"""
        
        # 模拟账单数据
        bills_batch = [
            {'id': 12345, 'description': '滴滴出行'},
            {'id': 12346, 'description': '工资发放'},
            {'id': 12347, 'description': '午餐费用'}
        ]
        
        # 解析结果
        results = ai_service._parse_batch_classification_result(ai_response, bills_batch, db)
        
        print("解析结果:")
        for bill_id, category_name in results:
            print(f"账单{bill_id}: {category_name}")
        
        # 验证解析结果
        expected_results = {
            12345: '交通出行',
            12346: '工资收入', 
            12347: '食品餐饮'
        }
        
        all_correct = True
        for bill_id, category_name in results:
            if expected_results.get(bill_id) == category_name:
                print(f"✅ 账单{bill_id}解析正确: {category_name}")
            else:
                print(f"❌ 账单{bill_id}解析错误: 期望{expected_results.get(bill_id)}, 实际{category_name}")
                all_correct = False
        
        if all_correct:
            print("✅ 所有分类结果解析正确")
        else:
            print("❌ 部分分类结果解析错误")
            
        # 测试不包含ID的格式
        print("\n测试解析不包含分类ID的格式...")
        ai_response_no_id = """12345: 交通出行
12346: 工资收入"""
        
        bills_batch_no_id = [
            {'id': 12345, 'description': '滴滴出行'},
            {'id': 12346, 'description': '工资发放'}
        ]
        
        results_no_id = ai_service._parse_batch_classification_result(ai_response_no_id, bills_batch_no_id, db)
        
        print("不包含ID的解析结果:")
        for bill_id, category_name in results_no_id:
            print(f"账单{bill_id}: {category_name}")
            
        if len(results_no_id) == 2 and results_no_id[0][1] == '交通出行' and results_no_id[1][1] == '工资收入':
            print("✅ 不包含ID的格式也能正确解析")
        else:
            print("❌ 不包含ID的格式解析失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("开始测试优化后的AI分类服务...")
    print("=" * 60)
    
    test_single_bill_prompt_structure()
    test_batch_classification_prompt_structure()
    test_parse_classification_result_with_id()
    
    print("\n" + "=" * 60)
    print("测试完成!")