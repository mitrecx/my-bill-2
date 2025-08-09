#!/usr/bin/env python3
"""
测试 raw_data 中 counter_party 字段的命名修正
"""

import sys
import os
import json

# 添加项目根目录到Python路径
project_root = "/Users/chenxing/projects/my-bills-2"
backend_root = os.path.join(project_root, "backend")
sys.path.insert(0, project_root)
sys.path.insert(0, backend_root)

def test_cmb_parser_raw_data():
    """测试招商银行解析器的 raw_data 字段命名"""
    try:
        from parsers.cmb_parser import CMBParser
        
        print("=== 测试招商银行解析器 raw_data 字段命名 ===")
        
        # 创建模拟的银行账单文本
        test_content = """2025-04-15
CNY
-4577.17
6522.51
掌上生活还款
陈兴
2025-04-16
CNY
100.00
6622.51
工资收入
公司财务部"""
        
        parser = CMBParser()
        result = parser.parse_content(test_content)
        
        if result.success_records:
            print(f"✅ 成功解析 {len(result.success_records)} 条记录")
            
            # 检查第一条记录的 raw_data
            first_record = result.success_records[0]
            raw_data = first_record.get('raw_data')
            
            if raw_data:
                print(f"✅ raw_data 字段存在")
                
                # 解析 raw_data JSON
                if isinstance(raw_data, str):
                    raw_data_dict = json.loads(raw_data)
                else:
                    raw_data_dict = raw_data
                
                print(f"📋 raw_data 内容: {json.dumps(raw_data_dict, ensure_ascii=False, indent=2)}")
                
                # 检查字段命名
                if 'counter_party' in raw_data_dict:
                    print("✅ raw_data 中使用了正确的 counter_party 字段命名")
                    print(f"   counter_party 值: {raw_data_dict['counter_party']}")
                    
                    # 检查是否还有旧的 counterpart 字段
                    if 'counterpart' in raw_data_dict:
                        print("❌ raw_data 中仍然存在旧的 counterpart 字段")
                        return False
                    else:
                        print("✅ 已移除旧的 counterpart 字段")
                    
                    # 检查所有必需字段
                    required_fields = ['date', 'currency', 'amount', 'balance', 'description', 'counter_party']
                    missing_fields = [field for field in required_fields if field not in raw_data_dict]
                    
                    if missing_fields:
                        print(f"❌ raw_data 缺少字段: {missing_fields}")
                        return False
                    else:
                        print("✅ raw_data 包含所有必需字段")
                    
                    return True
                else:
                    print("❌ raw_data 中缺少 counter_party 字段")
                    return False
            else:
                print("❌ 记录中缺少 raw_data 字段")
                return False
        else:
            print("❌ 解析失败，没有成功记录")
            if result.failed_records:
                print(f"失败记录: {result.failed_records}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_other_parsers():
    """测试其他解析器是否受影响"""
    try:
        from parsers.jd_parser import JDParser
        from parsers.alipay_parser import AlipayParser
        
        print("\n=== 测试其他解析器 ===")
        
        # 测试京东解析器
        jd_parser = JDParser()
        print("✅ JDParser 导入成功")
        
        # 测试支付宝解析器
        alipay_parser = AlipayParser()
        print("✅ AlipayParser 导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试其他解析器失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 测试 raw_data 中 counter_party 字段命名修正 ===\n")
    
    results = []
    
    # 测试招商银行解析器
    results.append(test_cmb_parser_raw_data())
    
    # 测试其他解析器
    results.append(test_other_parsers())
    
    print(f"\n=== 测试结果汇总 ===")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ 所有测试通过 ({passed}/{total})")
        print("✅ raw_data 中的 counter_party 字段命名修正成功")
    else:
        print(f"❌ 部分测试失败 ({passed}/{total})")
        print("❌ 需要进一步检查和修复")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)