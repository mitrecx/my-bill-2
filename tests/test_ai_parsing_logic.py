#!/usr/bin/env python3
"""
测试AI响应解析逻辑
模拟AI返回的多行响应格式，验证解析是否正确
"""

import re

def parse_ai_response(content):
    """
    模拟AI分类服务中的解析逻辑
    """
    print(f"原始AI响应: {repr(content)}")
    
    # 模拟分类ID到名称的映射
    category_id_to_name = {
        11: "食品餐饮",
        12: "交通出行", 
        13: "日用百货",
        14: "医疗健康"
    }
    
    # 尝试从响应中提取分类ID
    category_id = None
    
    # 处理多行响应，查找包含"分类ID"的行
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        print(f"处理行: {repr(line)}")
        
        if '分类ID:' in line:
            # 处理格式：分类ID: 11
            parts = line.split('分类ID:', 1)
            if len(parts) == 2:
                category_id_str = parts[1].strip()
                try:
                    category_id = int(category_id_str)
                    print(f"从'分类ID:'行提取到分类ID: {category_id}")
                    break
                except ValueError:
                    continue
        elif line and ':' in line and not line.startswith('账单ID:'):
            # 处理简单格式：账单ID: 分类ID
            parts = line.split(':', 1)
            if len(parts) == 2:
                category_id_str = parts[1].strip()
                try:
                    category_id = int(category_id_str)
                    print(f"从简单格式提取到分类ID: {category_id}")
                    break
                except ValueError:
                    continue
    
    # 如果还没找到，尝试从整个内容中提取数字
    if category_id is None:
        # 查找最后一个数字作为分类ID
        numbers = re.findall(r'\d+', content)
        if numbers:
            try:
                category_id = int(numbers[-1])
                print(f"从数字列表提取到分类ID: {category_id} (数字列表: {numbers})")
            except ValueError:
                pass
    
    if category_id is not None:
        # 根据分类ID获取分类名称
        category_name = category_id_to_name.get(category_id)
        
        if category_name:
            print(f"✅ 解析成功: 分类ID {category_id} ({category_name})")
            return category_name
        else:
            print(f"❌ 无效分类ID: {category_id}")
            return None
    else:
        print(f"❌ 无法从响应中提取分类ID")
        return None

def test_parsing():
    """测试不同格式的AI响应"""
    
    print("=" * 60)
    print("测试AI响应解析逻辑")
    print("=" * 60)
    
    # 测试用例1：日志中显示的问题格式
    test_case_1 = """账单ID: 14797
分类ID: 11"""
    
    print("\n测试用例1 - 多行格式（日志中的问题格式）:")
    result1 = parse_ai_response(test_case_1)
    
    # 测试用例2：简单格式
    test_case_2 = "14797: 11"
    
    print("\n测试用例2 - 简单格式:")
    result2 = parse_ai_response(test_case_2)
    
    # 测试用例3：只有分类ID
    test_case_3 = "分类ID: 12"
    
    print("\n测试用例3 - 只有分类ID:")
    result3 = parse_ai_response(test_case_3)
    
    # 测试用例4：复杂格式
    test_case_4 = """根据账单描述"午餐费用"，这应该归类为食品餐饮。
账单ID: 14798
分类ID: 11"""
    
    print("\n测试用例4 - 复杂格式:")
    result4 = parse_ai_response(test_case_4)
    
    # 测试用例5：无效格式
    test_case_5 = "无法分类此账单"
    
    print("\n测试用例5 - 无效格式:")
    result5 = parse_ai_response(test_case_5)
    
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"测试用例1: {'✅ 通过' if result1 == '食品餐饮' else '❌ 失败'}")
    print(f"测试用例2: {'✅ 通过' if result2 == '食品餐饮' else '❌ 失败'}")
    print(f"测试用例3: {'✅ 通过' if result3 == '交通出行' else '❌ 失败'}")
    print(f"测试用例4: {'✅ 通过' if result4 == '食品餐饮' else '❌ 失败'}")
    print(f"测试用例5: {'✅ 通过' if result5 is None else '❌ 失败'}")
    print("=" * 60)

if __name__ == "__main__":
    test_parsing()