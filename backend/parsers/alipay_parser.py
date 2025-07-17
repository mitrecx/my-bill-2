import pandas as pd
import logging
from typing import Dict, Any
from .base_parser import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class AlipayParser(BaseParser):
    """支付宝账单解析器"""
    
    def __init__(self):
        super().__init__()
        self.source_type = "alipay"
        
        # 支付宝CSV字段映射
        self.field_mapping = {
            "记录时间": "transaction_time",
            "分类": "category",
            "收支类型": "income_expense",
            "金额": "amount",
            "备注": "transaction_desc",
            "账户": "account",
            "来源": "source",
            "标签": "tags"
        }
    
    def parse_file(self, file_path: str) -> ParseResult:
        """解析支付宝账单文件"""
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
            logger.error(f"解析支付宝文件时出错: {e}")
            result.add_failed({}, f"文件解析错误: {str(e)}")
            return result
    
    def parse_content(self, content: str) -> ParseResult:
        """解析支付宝账单内容"""
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
                    
                    # 额外处理支付宝特有字段
                    processed_record = self._process_alipay_fields(mapped_record)
                    
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
            logger.error(f"解析支付宝内容时出错: {e}")
            result.add_failed({}, f"内容解析错误: {str(e)}")
            return result
    
    def _find_data_start(self, lines) -> int:
        """找到数据开始的行号"""
        for i, line in enumerate(lines):
            # 查找包含字段名的行
            if "记录时间" in line and "分类" in line and "金额" in line:
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
    
    def _clean_nan_values(self, obj):
        """递归清理对象中的NaN值"""
        if isinstance(obj, dict):
            cleaned = {}
            for key, value in obj.items():
                cleaned[key] = self._clean_nan_values(value)
            return cleaned
        elif isinstance(obj, list):
            return [self._clean_nan_values(item) for item in obj]
        elif pd.isna(obj):
            return None
        elif isinstance(obj, float) and (obj != obj):  # 另一种检查NaN的方法
            return None
        else:
            return obj
    
    def _process_alipay_fields(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """处理支付宝特有字段"""
        # 首先清理原始记录中的NaN值
        cleaned_record = self._clean_nan_values(record)
        processed = cleaned_record.copy()
        
        # 处理收支情况
        income_expense = cleaned_record.get("income_expense", "")
        if income_expense:
            if "收入" in income_expense:
                processed["transaction_type"] = "收入"
            elif "支出" in income_expense:
                processed["transaction_type"] = "支出"
            elif "不计收支" in income_expense:
                processed["transaction_type"] = "不计收支"
        
        # 使用分类字段作为交易类型的补充
        category = cleaned_record.get("category", "")
        if category and not processed.get("transaction_type"):
            processed["transaction_type"] = category
        
        # 处理交易描述，合并多个描述字段
        desc_parts = []
        if cleaned_record.get("transaction_desc"):
            desc_parts.append(str(cleaned_record["transaction_desc"]))
        if cleaned_record.get("source"):
            desc_parts.append(f"来源: {cleaned_record['source']}")
        if cleaned_record.get("tags"):
            desc_parts.append(f"标签: {cleaned_record['tags']}")
            
        if desc_parts:
            processed["transaction_desc"] = " | ".join(desc_parts)
        
        # 提取商户名称（从备注中提取）
        if cleaned_record.get("transaction_desc"):
            desc = str(cleaned_record["transaction_desc"])
            # 尝试从描述中提取商户名称
            if "-" in desc:
                parts = desc.split("-", 1)
                if len(parts) > 1:
                    processed["merchant_name"] = parts[0].strip()
            elif "：" in desc:
                parts = desc.split("：", 1)
                if len(parts) > 1:
                    processed["merchant_name"] = parts[0].strip()
        
        # 处理支付方式
        account = cleaned_record.get("account", "")
        if account:
            processed["payment_method"] = account
        
        # 设置raw_data字段为清理后的原始记录，避免嵌套
        processed["raw_data"] = cleaned_record
        
        return processed
    
    def _detect_encoding(self, file_path: str) -> str:
        """检测文件编码，支付宝文件通常是GBK编码"""
        encodings = ['gbk', 'gb2312', 'gb18030', 'utf-8', 'utf-8-sig']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # 读取前1024字符测试
                return encoding
            except UnicodeDecodeError:
                continue
        
        logger.warning(f"无法检测文件编码，使用默认编码: gbk")
        return 'gbk'