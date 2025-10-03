import pandas as pd
import logging
from typing import Dict, Any
from .base_parser import BaseParser, ParseResult
import re
from decimal import Decimal

logger = logging.getLogger(__name__)


class MeituanParser(BaseParser):
    """美团账单解析器"""
    
    def __init__(self):
        super().__init__()
        self.source_type = "meituan"
        
        # 美团CSV字段映射
        self.field_mapping = {
            "交易创建时间": "transaction_create_time",
            "交易成功时间": "transaction_time",
            "交易类型": "transaction_category",
            "订单标题": "transaction_desc",
            "收/支": "income_expense",
            "支付方式": "payment_method",
            "订单金额": "order_amount",
            "实付金额": "amount",
            "交易单号": "transaction_id",
            "商家单号": "merchant_order_id",
            "备注": "remark"
        }
    
    def parse_file(self, file_path: str) -> ParseResult:
        """解析美团账单文件"""
        result = ParseResult()
        
        try:
            # 检测文件编码
            encoding = self._detect_encoding(file_path)
            
            # 读取文件内容
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return self.parse_content(content)
            
        except Exception as e:
            logger.error(f"解析美团文件时出错: {e}")
            result.add_failed({}, f"文件解析错误: {str(e)}")
            return result
    
    def parse_content(self, content: str) -> ParseResult:
        """解析美团账单内容"""
        result = ParseResult()
        
        try:
            # 找到数据开始的行（【美团交易账单明细列表】之后的表头）
            lines = content.split('\n')
            data_start_line = self._find_data_start(lines)
            
            if data_start_line == -1:
                result.add_failed({}, "未找到有效的数据开始行")
                return result
            
            # 提取CSV数据部分
            csv_lines = lines[data_start_line:]
            csv_content = '\n'.join(csv_lines)
            
            # 使用pandas读取CSV内容
            from io import StringIO
            df = pd.read_csv(StringIO(csv_content), encoding='utf-8')
            
            # 清理数据框，移除空行和无效行
            df = df.dropna(how='all')
            
            # 第一步：处理所有记录并收集数据
            all_records = []
            for index, row in df.iterrows():
                try:
                    # 转换为字典
                    raw_record = row.to_dict()
                    
                    # 映射字段名
                    mapped_record = self._map_fields(raw_record)
                    
                    # 额外处理美团特有字段
                    processed_record = self._process_meituan_fields(mapped_record)
                    
                    all_records.append(processed_record)
                        
                except Exception as e:
                    logger.warning(f"处理第{index}行时出错: {e}")
                    result.add_failed(row.to_dict() if hasattr(row, 'to_dict') else {}, str(e))
            
            # 第二步：执行支付退款配对逻辑
            paired_records = self._pair_payment_refund_records(all_records)
            
            # 第三步：标准化并添加到结果中
            for processed_record in paired_records:
                try:
                    # 提取custom_raw_data
                    custom_raw_data = processed_record.pop("raw_data", None)
                    
                    # 标准化记录
                    standardized = self.standardize_record(processed_record, custom_raw_data)
                    if standardized:
                        result.add_success(standardized)
                    else:
                        result.add_failed({}, "记录标准化失败")
                        
                except Exception as e:
                    logger.warning(f"标准化记录时出错: {e}")
                    result.add_failed({}, str(e))
            
            return result
            
        except Exception as e:
            logger.error(f"解析美团内容时出错: {e}")
            result.add_failed({}, f"内容解析错误: {str(e)}")
            return result
    
    def _find_data_start(self, lines) -> int:
        """找到数据开始的行号"""
        for i, line in enumerate(lines):
            if "交易创建时间,交易成功时间,交易类型" in line:
                return i
        return -1
    
    def _map_fields(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """映射字段名"""
        mapped = {}
        for original_field, mapped_field in self.field_mapping.items():
            if original_field in raw_record:
                value = raw_record[original_field]
                # 清理NaN值
                if pd.isna(value):
                    value = None
                mapped[mapped_field] = value
        return mapped
    
    def _process_meituan_fields(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """处理美团特有字段"""
        processed = record.copy()
        
        # 处理金额字段 - 移除¥符号
        if 'amount' in processed and processed['amount']:
            amount_str = str(processed['amount'])
            # 移除¥符号和空格
            amount_str = amount_str.replace('¥', '').replace(' ', '').strip()
            processed['amount'] = amount_str
        
        # 处理收支类型映射 - 使用中文类型与数据库保持一致
        if 'income_expense' in processed:
            income_expense = processed['income_expense']
            if income_expense == '收入':
                processed['transaction_type'] = '收入'
            elif income_expense == '支出':
                processed['transaction_type'] = '支出'
            else:
                processed['transaction_type'] = '不计收支'
        
        # 处理交易描述 - 使用订单标题
        if 'transaction_desc' in processed and processed['transaction_desc']:
            # 清理交易描述中的特殊字符
            desc = str(processed['transaction_desc']).strip()
            processed['transaction_desc'] = desc
        
        # 处理分类 - 基于交易类型和订单标题进行简单分类
        category = self._categorize_transaction(
            processed.get('transaction_category', ''),
            processed.get('transaction_desc', '')
        )
        processed['category'] = category
        
        # 处理备注 - 合并支付方式和原备注
        remark_parts = []
        if processed.get('payment_method'):
            remark_parts.append(f"支付方式: {processed['payment_method']}")
        if processed.get('remark') and processed['remark'] != '/':
            remark_parts.append(processed['remark'])
        if processed.get('transaction_id'):
            remark_parts.append(f"交易单号: {processed['transaction_id']}")
        
        processed['remark'] = '; '.join(remark_parts) if remark_parts else None
        
        # 构建原始数据
        processed['raw_data'] = {
            'transaction_create_time': record.get('transaction_create_time'),
            'transaction_success_time': record.get('transaction_time'),
            'transaction_category': record.get('transaction_category'),
            'order_title': record.get('transaction_desc'),
            'income_expense': record.get('income_expense'),
            'payment_method': record.get('payment_method'),
            'order_amount': record.get('order_amount'),
            'actual_amount': record.get('amount'),
            'transaction_id': record.get('transaction_id'),
            'merchant_order_id': record.get('merchant_order_id'),
            'original_remark': record.get('remark')
        }
        
        return processed
    
    def _categorize_transaction(self, transaction_category: str, transaction_desc: str) -> str:
        """基于交易类型和描述进行分类"""
        if not transaction_category and not transaction_desc:
            return "其他"
        
        # 合并分类信息
        combined_text = f"{transaction_category} {transaction_desc}".lower()
        
        # 餐饮相关
        if any(keyword in combined_text for keyword in ['餐', '火锅', '羊肉', '美食', '外卖']):
            return "餐饮美食"
        
        # 娱乐相关
        if any(keyword in combined_text for keyword in ['电影', '猫眼', '桌球', '台球', '娱乐']):
            return "休闲娱乐"
        
        # 交通相关
        if any(keyword in combined_text for keyword in ['骑行', '单车', '交通', '出行']):
            return "交通出行"
        
        # 退款
        if '退款' in combined_text:
            return "退款"
        
        # 支付相关
        if '支付' in combined_text:
            return "支付"
        
        return "其他"
    
    def _pair_payment_refund_records(self, records):
        """配对支付和退款记录，将匹配的记录标记为不计收支"""
        paired_records = []
        processed_indices = set()
        
        # 首先收集所有支付记录
        payment_records = []
        refund_records = []
        
        for i, record in enumerate(records):
            raw_data = record.get('raw_data', {})
            transaction_category = raw_data.get('transaction_category', '')
            
            if (transaction_category == '支付' and 
                record.get('transaction_type') == '支出'):
                payment_records.append((i, record))
            elif (transaction_category == '退款' and
                  record.get('transaction_type') == '收入'):
                refund_records.append((i, record))
        
        logger.info(f"找到 {len(payment_records)} 条支付记录，{len(refund_records)} 条退款记录")
        
        # 执行配对
        for payment_idx, payment_record in payment_records:
            if payment_idx in processed_indices:
                continue
                
            payment_title = payment_record.get('transaction_desc', '')
            payment_amount = payment_record.get('amount', '')
            
            # 寻找匹配的退款记录
            for refund_idx, refund_record in refund_records:
                if refund_idx in processed_indices:
                    continue
                    
                refund_title = refund_record.get('transaction_desc', '')
                refund_amount = refund_record.get('amount', '')
                
                # 检查订单标题和金额是否完全匹配
                if (payment_title == refund_title and 
                    payment_amount == refund_amount and
                    payment_title.strip() != '' and
                    payment_amount.strip() != ''):
                    
                    # 找到匹配的支付退款对，标记为不计收支
                    logger.info(f"找到支付退款配对: {payment_title}, 金额: {payment_amount}")
                    
                    # 修改支付记录
                    payment_record_copy = payment_record.copy()
                    payment_record_copy['transaction_type'] = '不计收支'
                    payment_record_copy['income_expense'] = '不计收支'
                    
                    # 修改退款记录
                    refund_record_copy = refund_record.copy()
                    refund_record_copy['transaction_type'] = '不计收支'
                    refund_record_copy['income_expense'] = '不计收支'
                    
                    # 在备注中添加配对信息
                    pair_info = f"[已配对] 支付退款对: {payment_title}"
                    if payment_record_copy.get('remark'):
                        payment_record_copy['remark'] = f"{payment_record_copy['remark']}; {pair_info}"
                    else:
                        payment_record_copy['remark'] = pair_info
                        
                    if refund_record_copy.get('remark'):
                        refund_record_copy['remark'] = f"{refund_record_copy['remark']}; {pair_info}"
                    else:
                        refund_record_copy['remark'] = pair_info
                    
                    paired_records.append(payment_record_copy)
                    paired_records.append(refund_record_copy)
                    
                    processed_indices.add(payment_idx)
                    processed_indices.add(refund_idx)
                    break
        
        # 添加未配对的记录
        for i, record in enumerate(records):
            if i not in processed_indices:
                paired_records.append(record)
        
        logger.info(f"配对完成，共处理 {len(paired_records)} 条记录，其中 {len(processed_indices)} 条参与配对")
        return paired_records
    
    def _detect_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        try:
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                return result['encoding'] or 'utf-8'
        except ImportError:
            # 如果没有chardet，尝试常见编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        f.read()
                    return encoding
                except UnicodeDecodeError:
                    continue
        return 'utf-8'