#!/usr/bin/env python3
"""
调试AI分类服务
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.orm import Session
from config.database import get_db
from services.ai_classification_service import AIClassificationService

def debug_ai_classification():
    """调试AI分类服务"""
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 初始化AI分类服务
        ai_service = AIClassificationService()
        
        print("=== AI分类服务状态 ===")
        print(f"服务可用: {ai_service.is_available()}")
        
        if ai_service.is_available():
            print("\n=== 获取分类上下文 ===")
            context = ai_service.get_categories_context(db)
            print(f"分类上下文:\n{context}")
            
            print("\n=== 测试单个账单分类 ===")
            test_bill_data = {
                'id': 11018,
                'amount': 3500.0,
                'transaction_type': '收入',
                'description': '招商银行工资发放',
                'source_type': 'cmb',
                'transaction_time': '2025-08-07T23:23:35.892210'
            }
            
            print(f"测试账单数据: {test_bill_data}")
            
            # 手动调用AI分类，添加详细日志
            print("\n=== 手动调用AI分类 ===")
            try:
                # 构建提示词
                bill_info = f"""
账单信息：
- 金额: {test_bill_data.get('amount', 0)}元
- 交易类型: {test_bill_data.get('transaction_type', '未知')}
- 描述: {test_bill_data.get('description', '无描述')}
- 来源: {test_bill_data.get('source_type', '未知')}
- 交易时间: {test_bill_data.get('transaction_time', '未知')}
"""
                
                prompt = f"""你是一个专业的账单分类助手。请根据账单信息，从给定的分类列表中选择最合适的分类。

{context}

{bill_info}

请仔细分析账单的描述、金额、交易类型等信息，选择最合适的分类。

要求：
1. 只返回分类名称，不要返回其他内容
2. 必须从上述分类列表中选择，不能创建新分类
3. 如果无法确定，返回"其他收入"或"其他支出"（根据交易类型）

分类名称："""
                
                print(f"发送给AI的提示词:\n{prompt}")
                
                # 调用AI
                response = ai_service.client.chat.completions.create(
                    model="glm-4.5",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=50,
                    thinking={"type": "disabled"}  # 禁用深度思考模式
                )
                
                print(f"AI原始响应: {response}")
                if response.choices and response.choices[0].message:
                    content = response.choices[0].message.content
                    print(f"AI响应内容: '{content}'")
                    print(f"AI响应内容长度: {len(content)}")
                    print(f"AI响应内容(strip后): '{content.strip()}'")
                    print(f"AI响应内容(strip后)长度: {len(content.strip())}")
                
            except Exception as e:
                print(f"手动调用AI失败: {e}")
                import traceback
                traceback.print_exc()
            
            result = ai_service.classify_single_bill(test_bill_data, db)
            print(f"分类结果: {result}")
        else:
            print("AI分类服务不可用，请检查ZHIPU_API_KEY配置")
            
    except Exception as e:
        print(f"调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_ai_classification()