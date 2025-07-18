import pdfplumber
import re
import logging
from typing import Dict, Any, List
from datetime import datetime
from .base_parser import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class CMBParser(BaseParser):
    """招商银行PDF账单解析器"""
    
    def __init__(self):
        super().__init__()
        self.source_type = "cmb"
        
        # 招商银行字段映射
        self.field_mapping = {
            "记账日期": "transaction_time",
            "货币": "currency", 
            "交易金额": "amount",
            "联机余额": "balance",
            "交易摘要": "transaction_desc",
            "对手信息": "counter_party"
        }
    
    def parse_file(self, file_path: str) -> ParseResult:
        """解析招商银行PDF文件"""
        result = ParseResult()
        
        try:
            with pdfplumber.open(file_path) as pdf:
                all_text = ""
                all_tables = []
                
                # 提取所有页面的文本和表格
                for page in pdf.pages:
                    # 提取文本
                    page_text = page.extract_text()
                    if page_text:
                        all_text += page_text + "\n"
                    
                    # 提取表格
                    tables = page.extract_tables()
                    if tables:
                        all_tables.extend(tables)
                
                # 解析表格数据
                if all_tables:
                    result = self._parse_tables(all_tables)
                else:
                    # 如果没有表格，尝试解析文本
                    result = self._parse_text(all_text)
                
                return result
                
        except Exception as e:
            logger.error(f"解析招商银行PDF文件时出错: {e}")
            result.add_failed({}, f"PDF解析错误: {str(e)}")
            return result
    
    def parse_content(self, content: str) -> ParseResult:
        """解析招商银行文本内容"""
        return self._parse_text(content)
    
    def _is_transaction_line(self, line: str) -> bool:
        """判断是否为交易记录行"""
        line = line.strip()
        
        # 排除非交易记录行
        exclude_patterns = [
            r'申请时间：',  # 申请时间行
            r'验证码：',    # 验证码行
            r'记账日期.*货币.*交易金额',  # 表头行
            r'Transaction.*Date.*Currency',  # 英文表头行
            r'^\s*$',      # 空行
            r'第\s*\d+\s*页',  # 页码行
            r'招商银行',    # 银行名称行
            r'客户姓名：',  # 客户信息行
            r'账户号码：',  # 账户信息行
            r'查询时间：',  # 查询时间行
            r'打印时间：',  # 打印时间行
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, line):
                return False
        
        # 检查是否包含交易记录的基本特征
        # 1. 包含日期
        if not re.search(r'\d{4}-\d{2}-\d{2}', line):
            return False
        
        # 2. 包含货币代码或金额
        if not (re.search(r'\bCNY\b|\bUSD\b|\bEUR\b|\bHKD\b', line) or 
                re.search(r'-?\d+[,.]?\d*\.?\d+', line)):
            return False
        
        # 3. 行的结构应该类似：日期 货币 金额 余额 描述 对手方
        parts = line.split()
        if len(parts) < 4:  # 至少应该有日期、货币、金额、余额
            return False
        
        # 4. 第一个部分应该是日期
        if not re.match(r'\d{4}-\d{2}-\d{2}', parts[0]):
            return False
        
        return True
    
    def _parse_tables(self, tables: List[List[List[str]]]) -> ParseResult:
        """解析PDF表格数据"""
        result = ParseResult()
        
        try:
            for table in tables:
                if not table or len(table) < 2:
                    continue
                
                # 查找表头行
                header_row = None
                data_start_row = 0
                
                for i, row in enumerate(table):
                    if row and any("记账日期" in str(cell) or "Transaction" in str(cell) for cell in row if cell):
                        header_row = row
                        data_start_row = i + 1
                        break
                
                if not header_row:
                    continue
                
                # 处理数据行
                for row_idx in range(data_start_row, len(table)):
                    row = table[row_idx]
                    if not row or not any(cell for cell in row if cell):
                        continue
                    
                    try:
                        # 解析行数据
                        raw_record = self._parse_table_row(header_row, row)
                        if raw_record:
                            # 处理银行特有字段
                            processed_record = self._process_cmb_fields(raw_record)
                            
                            # 标准化记录
                            standardized = self.standardize_record(processed_record)
                            if standardized:
                                result.add_success(standardized)
                            else:
                                result.add_failed(raw_record, "记录标准化失败")
                                
                    except Exception as e:
                        logger.warning(f"处理表格第{row_idx}行时出错: {e}")
                        result.add_failed({"row": row}, str(e))
                        
        except Exception as e:
            logger.error(f"解析表格时出错: {e}")
            result.add_failed({}, f"表格解析错误: {str(e)}")
        
        return result
    
    def _parse_table_row(self, header_row: List[str], data_row: List[str]) -> Dict[str, Any]:
        """解析表格行数据"""
        record = {}
        
        # 清理表头
        clean_headers = []
        for header in header_row:
            if header:
                clean_header = str(header).strip()
                # 映射英文表头到中文
                if "Date" in clean_header:
                    clean_header = "记账日期"
                elif "Currency" in clean_header:
                    clean_header = "货币"
                elif "Amount" in clean_header:
                    clean_header = "交易金额"
                elif "Balance" in clean_header:
                    clean_header = "联机余额"
                elif "Transaction" in clean_header and "Type" in clean_header:
                    clean_header = "交易摘要"
                elif "Counter" in clean_header or "Party" in clean_header:
                    clean_header = "对手信息"
                
                clean_headers.append(clean_header)
            else:
                clean_headers.append("")
        
        # 映射数据
        for i, value in enumerate(data_row):
            if i < len(clean_headers) and clean_headers[i] and value:
                record[clean_headers[i]] = str(value).strip()
        
        return record
    
    def _parse_text(self, text: str) -> ParseResult:
        """解析文本内容（备用方法）"""
        result = ParseResult()
        
        try:
            lines = text.split('\n')
            
            # 查找数据行（包含日期的行）
            date_pattern = r'\d{4}-\d{2}-\d{2}'
            
            for line in lines:
                if re.search(date_pattern, line):
                    # 过滤掉非交易记录行
                    if self._is_transaction_line(line):
                        try:
                            # 尝试解析行数据
                            raw_record = self._parse_text_line(line)
                            if raw_record:
                                # 处理银行特有字段
                                processed_record = self._process_cmb_fields(raw_record)
                                
                                # 标准化记录
                                standardized = self.standardize_record(processed_record)
                                if standardized:
                                    result.add_success(standardized)
                                else:
                                    result.add_failed(raw_record, "记录标准化失败")
                                    
                        except Exception as e:
                            logger.warning(f"处理文本行时出错: {e}")
                            result.add_failed({"line": line}, str(e))
                        
        except Exception as e:
            logger.error(f"解析文本时出错: {e}")
            result.add_failed({}, f"文本解析错误: {str(e)}")
        
        return result
    
    def _parse_text_line(self, line: str) -> Dict[str, Any]:
        """解析文本行"""
        # 根据招商银行流水格式解析
        # 示例：2025-01-03 CNY 300.00 328.96 银联渠道转入 陈兴
        parts = line.strip().split()
        
        if len(parts) < 4:
            return {}
        
        record = {}
        
        # 解析日期
        if re.match(r'\d{4}-\d{2}-\d{2}', parts[0]):
            record["记账日期"] = parts[0]
        
        # 解析货币
        if len(parts) > 1 and parts[1] in ['CNY', 'USD', 'EUR', 'HKD']:
            record["货币"] = parts[1]
            amount_idx = 2
        else:
            record["货币"] = "CNY"
            amount_idx = 1
        
        # 解析金额
        if len(parts) > amount_idx:
            amount_str = parts[amount_idx]
            # 处理负数
            if amount_str.startswith('-'):
                record["交易金额"] = amount_str
            else:
                record["交易金额"] = amount_str
        
        # 解析余额
        if len(parts) > amount_idx + 1:
            record["联机余额"] = parts[amount_idx + 1]
        
        # 解析交易摘要和对手信息
        if len(parts) > amount_idx + 2:
            remaining_parts = parts[amount_idx + 2:]
            if len(remaining_parts) >= 2:
                record["交易摘要"] = remaining_parts[0]
                record["对手信息"] = ' '.join(remaining_parts[1:])
            elif len(remaining_parts) == 1:
                record["交易摘要"] = remaining_parts[0]
        
        return record
    
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
        
        # 处理交易类型（根据金额正负判断）
        amount_str = str(processed.get("amount", ""))
        if amount_str:
            if amount_str.startswith('-'):
                processed["transaction_type"] = "支出"
                # 移除负号
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
        
        return processed