import fitz  # PyMuPDF
import re
import logging
from typing import Dict, Any, List
from datetime import datetime
from .base_parser import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class CMBParser(BaseParser):
    """招商银行PDF账单解析器 (使用PyMuPDF)"""
    
    def __init__(self):
        super().__init__()
        self.source_type = "cmb"
        
        # 招商银行字段映射
        self.field_mapping = {
            "date": "transaction_time",
            "currency": "currency", 
            "amount": "amount",
            "balance": "balance",
            "description": "transaction_desc",
            "counterpart": "counter_party",
            "type": "transaction_type"
        }
    
    def parse_file(self, file_path: str) -> ParseResult:
        """解析招商银行PDF文件"""
        result = ParseResult()
        
        try:
            # 使用PyMuPDF提取PDF文本
            pdf_text = self._extract_pdf_text(file_path)
            if not pdf_text:
                result.add_failed({}, "PDF文件为空或无法读取")
                return result
            
            # 解析文本内容
            transactions = self._parse_bank_statement(pdf_text)
            
            # 处理每个交易记录
            for transaction in transactions:
                try:
                    # 处理银行特有字段
                    processed_record = self._process_cmb_fields(transaction)
                    
                    # 标准化记录
                    standardized = self.standardize_record(processed_record)
                    if standardized:
                        result.add_success(standardized)
                    else:
                        result.add_failed(transaction, "记录标准化失败")
                        
                except Exception as e:
                    logger.warning(f"处理交易记录时出错: {e}")
                    result.add_failed(transaction, str(e))
            
            return result
                
        except Exception as e:
            logger.error(f"解析招商银行PDF文件时出错: {e}")
            result.add_failed({}, f"PDF解析错误: {str(e)}")
            return result
    
    def parse_content(self, content: str) -> ParseResult:
        """解析招商银行文本内容"""
        result = ParseResult()
        
        try:
            transactions = self._parse_bank_statement(content)
            
            # 处理每个交易记录
            for transaction in transactions:
                try:
                    # 处理银行特有字段
                    processed_record = self._process_cmb_fields(transaction)
                    
                    # 标准化记录
                    standardized = self.standardize_record(processed_record)
                    if standardized:
                        result.add_success(standardized)
                    else:
                        result.add_failed(transaction, "记录标准化失败")
                        
                except Exception as e:
                    logger.warning(f"处理交易记录时出错: {e}")
                    result.add_failed(transaction, str(e))
            
            return result
            
        except Exception as e:
            logger.error(f"解析文本内容时出错: {e}")
            result.add_failed({}, f"文本解析错误: {str(e)}")
            return result
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """使用PyMuPDF提取PDF文件中的文本内容"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"提取PDF文本时出错: {e}")
            raise
    
    def _parse_bank_statement(self, text_content: str) -> List[Dict[str, Any]]:
        """解析银行账单数据"""
        # 分行处理
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        transactions = []
        
        # 匹配日期模式 (YYYY-MM-DD)
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        
        # 匹配金额模式 (包含正负号，可能有逗号分隔符)
        amount_pattern = r'^[+-]?\d+(?:,\d{3})*(?:\.\d{1,2})?$'
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 检查是否是日期行
            if re.match(date_pattern, line):
                # 确保后面有足够的行来构成一个完整的交易记录
                if i + 5 < len(lines):
                    try:
                        date = lines[i]           # 日期
                        currency = lines[i + 1]   # 货币 (CNY)
                        amount = lines[i + 2]     # 交易金额
                        balance = lines[i + 3]    # 联机余额
                        description = lines[i + 4] # 交易摘要
                        counterpart = lines[i + 5] # 对手信息
                        
                        # 验证格式
                        if (currency == "CNY" and 
                            re.match(amount_pattern, amount) and 
                            re.match(amount_pattern, balance)):
                            
                            # 判断交易类型
                            trans_type = "支出"
                            if (not amount.startswith('-') or 
                                any(keyword in description for keyword in 
                                    ['收入', '存入', '工资', '奖金', '退款', '汇入', '转入', '赎回', '红利', '鼓励金'])):
                                trans_type = "收入"
                            
                            transaction = {
                                'date': date,
                                'currency': currency,
                                'amount': amount,
                                'balance': balance,
                                'description': description,
                                'counterpart': counterpart,
                                'type': trans_type
                            }
                            
                            transactions.append(transaction)
                            
                            # 跳过已处理的行
                            i += 6
                            continue
                            
                    except IndexError:
                        pass
            
            i += 1
        
        return transactions
    
    def _process_cmb_fields(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """处理招商银行特有字段"""
        processed = record.copy()
        
        # 映射字段名
        mapped = {}
        for original_field, standard_field in self.field_mapping.items():
            if original_field in processed:
                mapped[standard_field] = processed[original_field]
        
        # 保留未映射的字段
        for key, value in processed.items():
            if key not in self.field_mapping:
                mapped[key] = value
        
        processed = mapped
        
        # 处理金额字段 - 移除负号并设置正确的交易类型
        amount_str = str(processed.get("amount", ""))
        if amount_str:
            if amount_str.startswith('-'):
                processed["transaction_type"] = "支出"
                # 移除负号，金额统一为正数
                processed["amount"] = amount_str[1:]
            else:
                processed["transaction_type"] = "收入"
        
        # 处理商户名称（从交易摘要中提取）
        transaction_desc = processed.get("transaction_desc", "")
        if transaction_desc:
            # 常见的银行交易类型
            if any(keyword in transaction_desc for keyword in ["转账", "汇款", "还款"]):
                processed["merchant_name"] = "银行转账"
            elif "快捷支付" in transaction_desc:
                processed["merchant_name"] = "快捷支付"
            elif "基金" in transaction_desc:
                processed["merchant_name"] = "基金交易"
            elif "银联" in transaction_desc:
                processed["merchant_name"] = "银联支付"
            elif "工资" in transaction_desc:
                processed["merchant_name"] = "工资收入"
            elif "奖金" in transaction_desc:
                processed["merchant_name"] = "奖金收入"
            elif "退款" in transaction_desc:
                processed["merchant_name"] = "退款"
            else:
                processed["merchant_name"] = transaction_desc
        
        # 处理支付方式
        transaction_desc = processed.get("transaction_desc", "")
        if "银联" in transaction_desc:
            processed["payment_method"] = "银联"
        elif "快捷支付" in transaction_desc:
            processed["payment_method"] = "快捷支付"
        elif "转账" in transaction_desc:
            processed["payment_method"] = "银行转账"
        elif "基金" in transaction_desc:
            processed["payment_method"] = "基金"
        else:
            processed["payment_method"] = "银行卡"
        
        # 生成订单ID（使用日期+金额+描述的组合）
        if not processed.get("order_id"):
            date_str = processed.get("transaction_time", "")
            amount_str = processed.get("amount", "")
            desc_str = processed.get("transaction_desc", "")
            if date_str and amount_str:
                # 创建一个简单的订单ID
                order_id = f"CMB_{date_str.replace('-', '')}_{amount_str}_{hash(desc_str) % 10000:04d}"
                processed["order_id"] = order_id
        
        # 设置分类（基于交易描述）
        if not processed.get("category"):
            transaction_desc = processed.get("transaction_desc", "")
            if "工资" in transaction_desc:
                processed["category"] = "工资收入"
            elif "奖金" in transaction_desc:
                processed["category"] = "奖金收入"
            elif "基金" in transaction_desc:
                processed["category"] = "投资理财"
            elif "转账" in transaction_desc or "汇款" in transaction_desc:
                processed["category"] = "转账汇款"
            elif "还款" in transaction_desc:
                processed["category"] = "还款"
            elif "退款" in transaction_desc:
                processed["category"] = "退款"
            else:
                processed["category"] = "其他"
        
        return processed