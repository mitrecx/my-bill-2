#!/usr/bin/env python3
"""
测试删除 counter_party 字段后的功能
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = "/Users/chenxing/projects/my-bills-2"
backend_root = os.path.join(project_root, "backend")
sys.path.insert(0, project_root)
sys.path.insert(0, backend_root)

def test_bill_model():
    """测试 Bill 模型是否正确删除了 counter_party 字段"""
    try:
        from models.bill import Bill
        
        # 检查 Bill 模型的字段
        bill_fields = [attr for attr in dir(Bill) if not attr.startswith('_')]
        print("=== Bill 模型字段 ===")
        for field in sorted(bill_fields):
            if hasattr(getattr(Bill, field), 'type'):
                print(f"  {field}")
        
        # 检查是否还有 counter_party 字段
        if hasattr(Bill, 'counter_party'):
            print("❌ Bill 模型中仍然存在 counter_party 字段")
            return False
        else:
            print("✅ Bill 模型中已成功删除 counter_party 字段")
            return True
            
    except Exception as e:
        print(f"❌ 测试 Bill 模型失败: {e}")
        return False

def test_parsers():
    """测试解析器是否正确处理了 counter_party 字段的删除"""
    try:
        from parsers.cmb_parser import CMBParser
        from parsers.jd_parser import JDParser
        
        print("\n=== 测试解析器 ===")
        
        # 测试招商银行解析器
        cmb_parser = CMBParser()
        if hasattr(cmb_parser, 'field_mapping') and 'counter_party' in cmb_parser.field_mapping.values():
            print("❌ CMBParser 仍在映射 counter_party 字段")
            return False
        else:
            print("✅ CMBParser 已正确移除 counter_party 字段映射")
        
        # 测试京东解析器
        jd_parser = JDParser()
        print("✅ JDParser 检查通过")
        
        # 测试基础解析器的 standardize_record 方法
        # 通过检查源码来验证
        import inspect
        from parsers.base_parser import BaseParser
        source = inspect.getsource(BaseParser.standardize_record)
        if 'counter_party' in source:
            print("❌ BaseParser.standardize_record 仍包含 counter_party 字段")
            return False
        else:
            print("✅ BaseParser.standardize_record 已正确移除 counter_party 字段")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试解析器失败: {e}")
        return False

def test_schemas():
    """测试 Pydantic schemas 是否正确"""
    try:
        from schemas.bills import BillBase, BillCreate, BillUpdate, BillResponse
        
        print("\n=== 测试 Pydantic Schemas ===")
        
        # 检查各个 schema 是否包含 counter_party 字段
        schemas = [
            ("BillBase", BillBase),
            ("BillCreate", BillCreate),
            ("BillUpdate", BillUpdate),
            ("BillResponse", BillResponse)
        ]
        
        all_good = True
        for name, schema_class in schemas:
            # 使用 model_fields 替代废弃的 __fields__
            fields = getattr(schema_class, 'model_fields', getattr(schema_class, '__fields__', {}))
            if 'counter_party' in fields:
                print(f"❌ {name} 仍包含 counter_party 字段")
                all_good = False
            else:
                print(f"✅ {name} 正确，不包含 counter_party 字段")
        
        return all_good
        
    except Exception as e:
        print(f"❌ 测试 schemas 失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 测试 counter_party 字段删除后的系统状态 ===\n")
    
    results = []
    
    # 测试 Bill 模型
    results.append(test_bill_model())
    
    # 测试解析器
    results.append(test_parsers())
    
    # 测试 schemas
    results.append(test_schemas())
    
    print(f"\n=== 测试结果汇总 ===")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ 所有测试通过 ({passed}/{total})")
        print("✅ counter_party 字段已成功从系统中删除")
    else:
        print(f"❌ 部分测试失败 ({passed}/{total})")
        print("❌ 需要进一步检查和修复")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)