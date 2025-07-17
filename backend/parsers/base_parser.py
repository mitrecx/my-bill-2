from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)


class ParseResult:
    """解析结果类"""
    def __init__(self):
        self.success_records: List[Dict[str, Any]] = []
        self.failed_records: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.total_count: int = 0
        self.success_count: int = 0
        self.failed_count: int = 0

    def add_success(self, record: Dict[str, Any]):
        """添加成功记录"""
        self.success_records.append(record)
        self.success_count += 1
        self.total_count += 1

    def add_failed(self, record: Dict[str, Any], error: str):
        """添加失败记录"""
        record['parse_error'] = error
        self.failed_records.append(record)
        self.failed_count += 1
        self.total_count += 1
        self.errors.append(error)

    def get_summary(self) -> Dict[str, Any]:
        """获取解析结果摘要"""
        return {
            "total_count": self.total_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "success_rate": self.success_count / self.total_count if self.total_count > 0 else 0,
            "errors": self.errors[:10]  # 只返回前10个错误
        }


class BaseParser(ABC):
    """文件解析器基类"""
    
    def __init__(self):
        self.source_type: str = ""
        self.encoding: str = "utf-8"
        
    @abstractmethod
    def parse_file(self, file_path: str) -> ParseResult:
        """解析文件的抽象方法"""
        pass
    
    @abstractmethod
    def parse_content(self, content: str) -> ParseResult:
        """解析文件内容的抽象方法"""
        pass
    
    def standardize_record(self, raw_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """标准化记录格式"""
        try:
            standardized = {
                "source_type": self.source_type,
                "transaction_time": self._parse_datetime(raw_record.get("transaction_time")),
                "merchant_name": self._clean_string(raw_record.get("merchant_name")),
                "transaction_desc": self._clean_string(raw_record.get("transaction_desc")),
                "amount": self._parse_amount(raw_record.get("amount")),
                "currency": raw_record.get("currency", "CNY"),
                "transaction_type": self._clean_string(raw_record.get("transaction_type")),
                "payment_method": self._clean_string(raw_record.get("payment_method")),
                "balance": self._parse_amount(raw_record.get("balance")),
                "order_id": self._clean_string(raw_record.get("order_id")),
                "counter_party": self._clean_string(raw_record.get("counter_party")),
                "category": self._clean_string(raw_record.get("category")),  # 添加分类字段
                "remark": self._clean_string(raw_record.get("remark")),
                "raw_data": raw_record  # 保存原始数据
            }
            
            # 移除空值
            return {k: v for k, v in standardized.items() if v is not None}
            
        except Exception as e:
            logger.error(f"标准化记录时出错: {e}")
            return None
    
    def _parse_datetime(self, dt_str: Any) -> Optional[datetime]:
        """解析日期时间"""
        if not dt_str:
            return None
            
        if isinstance(dt_str, datetime):
            return dt_str
            
        if not isinstance(dt_str, str):
            dt_str = str(dt_str)
        
        # 常见的日期时间格式
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y年%m月%d日 %H:%M:%S",
            "%Y年%m月%d日 %H时%M分%S秒",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(dt_str.strip(), fmt)
            except ValueError:
                continue
        
        logger.warning(f"无法解析日期时间: {dt_str}")
        return None
    
    def _parse_amount(self, amount_str: Any) -> Optional[Decimal]:
        """解析金额"""
        if not amount_str:
            return None
            
        if isinstance(amount_str, (int, float)):
            return Decimal(str(amount_str))
            
        if isinstance(amount_str, Decimal):
            return amount_str
            
        if not isinstance(amount_str, str):
            amount_str = str(amount_str)
        
        # 清理金额字符串
        amount_str = amount_str.strip()
        # 移除货币符号和千分位分隔符
        amount_str = amount_str.replace('¥', '').replace('￥', '').replace(',', '').replace('，', '')
        # 移除其他特殊字符，但保留负号和小数点
        amount_str = ''.join(c for c in amount_str if c.isdigit() or c in '.-')
        
        try:
            return Decimal(amount_str)
        except (InvalidOperation, ValueError):
            logger.warning(f"无法解析金额: {amount_str}")
            return None
    
    def _clean_string(self, text: Any) -> Optional[str]:
        """清理字符串"""
        if not text:
            return None
            
        if not isinstance(text, str):
            text = str(text)
        
        # 移除前后空格和换行符
        cleaned = text.strip().replace('\n', ' ').replace('\r', '')
        
        return cleaned if cleaned else None
    
    def _detect_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # 读取前1024字符测试
                return encoding
            except UnicodeDecodeError:
                continue
        
        logger.warning(f"无法检测文件编码，使用默认编码: {self.encoding}")
        return self.encoding