"""
测试支付宝解析器的 transaction_desc 字段修改
验证只使用备注字段，不拼接来源和标签
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from parsers.alipay_parser import AlipayParser


def test_transaction_desc_only_uses_remark():
    """测试 transaction_desc 只使用备注字段"""
    parser = AlipayParser()
    
    # 模拟清理后的记录数据
    test_record = {
        "transaction_desc": "测试备注内容",
        "source": "测试来源",
        "tags": "测试标签",
        "income_expense": "支出",
        "amount": "100.00",
        "_original_record": {
            "记录时间": "2024-01-01 12:00:00",
            "分类": "餐饮美食",
            "收支类型": "支出",
            "金额": "100.00",
            "备注": "测试备注内容",
            "账户": "支付宝余额",
            "来源": "测试来源",
            "标签": "测试标签"
        }
    }
    
    # 调用处理方法
    result = parser._process_alipay_fields(test_record)
    
    # 验证 transaction_desc 只包含备注内容，不包含来源和标签
    assert result["transaction_desc"] == "测试备注内容"
    assert "来源:" not in result["transaction_desc"]
    assert "标签:" not in result["transaction_desc"]
    assert "|" not in result["transaction_desc"]
    print("✅ 测试通过: transaction_desc 只使用备注字段")

def test_transaction_desc_with_empty_remark():
    """测试备注为空时的情况"""
    parser = AlipayParser()
    
    test_record = {
        "transaction_desc": "",
        "source": "测试来源",
        "tags": "测试标签",
        "_original_record": {
            "记录时间": "2024-01-01 12:00:00",
            "备注": "",
            "来源": "测试来源",
            "标签": "测试标签"
        }
    }
    
    result = parser._process_alipay_fields(test_record)
    
    # 当备注为空时，应该设置为空字符串
    assert result["transaction_desc"] == ""
    print("✅ 测试通过: 备注为空时正确处理")

def test_transaction_desc_with_no_remark():
    """测试没有备注字段时的情况"""
    parser = AlipayParser()
    
    test_record = {
        "source": "测试来源",
        "tags": "测试标签",
        "_original_record": {
            "记录时间": "2024-01-01 12:00:00",
            "来源": "测试来源",
            "标签": "测试标签"
        }
    }
    
    result = parser._process_alipay_fields(test_record)
    
    # 当没有备注字段时，不应该设置 transaction_desc
    assert "transaction_desc" not in result
    print("✅ 测试通过: 没有备注字段时正确处理")

def test_raw_data_still_contains_all_fields():
    """测试 raw_data 仍然包含所有原始字段"""
    parser = AlipayParser()
    
    test_record = {
        "transaction_desc": "测试备注内容",
        "source": "测试来源", 
        "tags": "测试标签",
        "_original_record": {
            "记录时间": "2024-01-01 12:00:00",
            "分类": "餐饮美食",
            "收支类型": "支出",
            "金额": "100.00",
            "备注": "测试备注内容",
            "账户": "支付宝余额",
            "来源": "测试来源",
            "标签": "测试标签"
        }
    }
    
    result = parser._process_alipay_fields(test_record)
    
    # 验证 raw_data 仍然包含所有原始字段
    assert "raw_data" in result
    raw_data = result["raw_data"]
    assert raw_data["description"] == "测试备注内容"
    assert raw_data["source"] == "测试来源"
    assert raw_data["tags"] == "测试标签"
    print("✅ 测试通过: raw_data 仍然包含所有原始字段")


if __name__ == "__main__":
    # 运行测试
    print("开始测试支付宝解析器的 transaction_desc 字段修改...")
    print()
    
    try:
        test_transaction_desc_only_uses_remark()
        test_transaction_desc_with_empty_remark()
        test_transaction_desc_with_no_remark()
        test_raw_data_still_contains_all_fields()
        
        print()
        print("🎉 所有测试都通过了！")
        print("✅ 支付宝账单导入时，transaction_desc 字段现在只使用备注字段，不再拼接来源和标签")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()