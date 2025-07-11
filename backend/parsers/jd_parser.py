import pandas as pd
import logging
from typing import Dict, Any
from .base_parser import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class JDParser(BaseParser):
    """京东账单解析器"""
    
    def __init__(self):
        super().__init__()
        self.source_type = "jd"
        
        # 京东CSV字段映射
        self.field_mapping = {
            "交易时间": "transaction_time",
            "商户名称": "merchant_name",
            "交易说明": "transaction_desc",
            "金额": "amount",
            "收/付款方式": "payment_method",
            "交易状态": "transaction_status",
            "收/支": "income_expense",
            "交易分类": "category",
            "交易订单号": "order_id",
            "商家订单号": "merchant_order_id",
            "备注": "remark"
        }
    
    def parse_file(self, file_path: str) -> ParseResult:
        """解析京东账单文件"""
        result = ParseResult()
        
        try:
            # 检测文件编码
            encoding = self._detect_encoding(file_path)
            
            # 读取文件内容，跳过前面的说明文字
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            
            # 找到数据开始的行（包含字段名的行）
            data_start_line = self._find_data_start(lines)
            if data_start_line == -1:
                result.add_failed({}, "未找到有效的数据开始行")
                return result
            
            # 从数据开始行读取CSV
            data_lines = lines[data_start_line:]
            csv_content = ''.join(data_lines)
            
            return self.parse_content(csv_content)
            
        except Exception as e:
            logger.error(f"解析京东文件时出错: {e}")
            result.add_failed({}, f"文件解析错误: {str(e)}")
            return result
    
    def parse_content(self, content: str) -> ParseResult:
        """解析京东账单内容"""
        result = ParseResult()
        
        try:
            # 使用pandas读取CSV内容
            from io import StringIO
            df = pd.read_csv(StringIO(content), encoding='utf-8')
            
            # 清理数据框，移除空行和无效行
            df = df.dropna(how='all')
            
            # 遍历每一行数据
            for index, row in df.iterrows():
                try:
                    # 转换为字典
                    raw_record = row.to_dict()
                    
                    # 映射字段名
                    mapped_record = self._map_fields(raw_record)
                    
                    # 额外处理京东特有字段
                    processed_record = self._process_jd_fields(mapped_record)
                    
                    # 标准化记录
                    standardized = self.standardize_record(processed_record)
                    if standardized:
                        result.add_success(standardized)
                    else:
                        result.add_failed(raw_record, "记录标准化失败")
                        
                except Exception as e:
                    logger.warning(f"处理第{index}行时出错: {e}")
                    result.add_failed(row.to_dict() if hasattr(row, 'to_dict') else {}, str(e))
            
            return result
            
        except Exception as e:
            logger.error(f"解析京东内容时出错: {e}")
            result.add_failed({}, f"内容解析错误: {str(e)}")
            return result
    
    def _find_data_start(self, lines) -> int:
        """找到数据开始的行号"""
        for i, line in enumerate(lines):
            # 查找包含字段名的行
            if "交易时间" in line and "商户名称" in line and "金额" in line:
                return i
        return -1
    
    def _map_fields(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """映射字段名"""
        mapped = {}
        for original_field, standard_field in self.field_mapping.items():
            if original_field in raw_record:
                mapped[standard_field] = raw_record[original_field]
        
        # 保留未映射的字段
        for key, value in raw_record.items():
            if key not in self.field_mapping:
                mapped[key] = value
                
        return mapped
    
    def _process_jd_fields(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """处理京东特有字段"""
        processed = record.copy()
        
        # 处理收支情况
        income_expense = record.get("income_expense", "")
        if income_expense:
            if "收入" in income_expense:
                processed["transaction_type"] = "收入"
            elif "支出" in income_expense:
                processed["transaction_type"] = "支出"
            elif "不计收支" in income_expense:
                processed["transaction_type"] = "不计收支"
        
        # 处理金额，京东可能有特殊标记（如已退款）
        amount_str = str(record.get("amount", ""))
        if amount_str:
            # 移除京东特有的标记
            amount_str = amount_str.replace("(已全额退款)", "").replace("(已退款", "").strip()
            # 提取退款金额
            if "(已退款" in str(record.get("amount", "")):
                # 标记为退款交易
                processed["transaction_type"] = "不计收支"
                processed["remark"] = f"退款交易: {processed.get('remark', '')}"
            
            processed["amount"] = amount_str
        
        # 处理交易描述，合并商户名称和交易说明
        desc_parts = []
        if record.get("merchant_name"):
            desc_parts.append(str(record["merchant_name"]))
        if record.get("transaction_desc"):
            desc_parts.append(str(record["transaction_desc"]))
            
        if desc_parts:
            processed["transaction_desc"] = " - ".join(desc_parts)
        
        # 处理订单号，优先使用交易订单号
        if record.get("order_id"):
            processed["order_id"] = record["order_id"]
        elif record.get("merchant_order_id"):
            processed["order_id"] = record["merchant_order_id"]
        
        # 处理备注，合并多个备注字段
        remark_parts = []
        if record.get("remark"):
            remark_parts.append(str(record["remark"]))
        if record.get("transaction_status"):
            remark_parts.append(f"状态: {record['transaction_status']}")
        if record.get("category"):
            remark_parts.append(f"分类: {record['category']}")
            
        if remark_parts:
            processed["remark"] = " | ".join(remark_parts)
        
        # 提取对手方信息（从商户名称中提取）
        merchant_name = record.get("merchant_name", "")
        if merchant_name and merchant_name not in ["京东小金库", "京东白条", "京东金融"]:
            processed["counter_party"] = merchant_name
        
        return processed 