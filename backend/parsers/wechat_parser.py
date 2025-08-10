"""
微信支付账单解析器
支持解析微信导出的Excel格式账单文件
"""

import pandas as pd
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from .base_parser import BaseParser, ParseResult


class WeChatParser(BaseParser):
    """微信支付账单解析器"""
    
    def __init__(self):
        super().__init__()
        self.source_type = 'wechat'
        
    def parse_file(self, file_path: str) -> ParseResult:
        """解析微信账单Excel文件"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, header=None)
            return self._parse_dataframe(df)
        except Exception as e:
            result = ParseResult()
            result.errors.append(f"读取Excel文件失败: {str(e)}")
            return result
    
    def parse_content(self, content: str) -> ParseResult:
        """解析微信账单内容（从字符串）"""
        # 对于Excel文件，这个方法不太适用，但为了兼容基类接口
        result = ParseResult()
        result.errors.append("微信账单解析器不支持字符串内容解析，请使用parse_file方法")
        return result
    
    def _parse_dataframe(self, df: pd.DataFrame) -> ParseResult:
        """解析微信账单内容"""
        result = ParseResult()
        
        try:
            # 查找数据开始行（包含"交易时间"的行）
            data_start_row = None
            for idx, row in df.iterrows():
                if any('交易时间' in str(cell) for cell in row if pd.notna(cell)):
                    data_start_row = idx
                    break
            
            if data_start_row is None:
                result.errors.append("未找到交易数据开始行（包含'交易时间'的行）")
                return result
            
            # 获取列名
            header_row = df.iloc[data_start_row]
            columns = [str(cell).strip() for cell in header_row if pd.notna(cell)]
            
            # 验证必要的列是否存在
            required_columns = ['交易时间', '交易类型', '交易对方', '商品', '收/支', '金额(元)']
            missing_columns = [col for col in required_columns if col not in columns]
            if missing_columns:
                result.errors.append(f"缺少必要的列: {', '.join(missing_columns)}")
                return result
            
            # 获取数据行
            data_df = df.iloc[data_start_row + 1:].copy()
            data_df.columns = columns[:len(data_df.columns)]
            
            # 过滤掉空行
            data_df = data_df.dropna(subset=['交易时间'])
            
            # 解析每一行数据
            for idx, row in data_df.iterrows():
                try:
                    record = self._parse_wechat_record(row)
                    if record:
                        result.add_success(record)
                except Exception as e:
                    result.add_failed({
                        'row': idx + 1,
                        'raw_data': row.to_dict()
                    }, str(e))
                    
        except Exception as e:
            result.errors.append(f"解析过程中发生错误: {str(e)}")
        
        return result
    
    def _parse_wechat_record(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """解析单条微信账单记录"""
        try:
            # 获取原始数据
            raw_data = {}
            
            # 安全获取字段值
            transaction_time = self._safe_get_value(row, '交易时间')
            transaction_type = self._safe_get_value(row, '交易类型')
            counter_party = self._safe_get_value(row, '交易对方')
            product = self._safe_get_value(row, '商品')
            income_expense = self._safe_get_value(row, '收/支')
            amount_str = self._safe_get_value(row, '金额(元)')
            payment_method = self._safe_get_value(row, '支付方式')
            current_status = self._safe_get_value(row, '当前状态')
            transaction_id = self._safe_get_value(row, '交易单号')
            merchant_order_id = self._safe_get_value(row, '商户单号')
            remark = self._safe_get_value(row, '备注')
            
            # 构建raw_data（使用snake_case命名）
            raw_data = {
                'transaction_time': transaction_time,
                'transaction_type': transaction_type,
                'counter_party': counter_party,
                'product': product,
                'income_expense': income_expense,
                'amount': amount_str,
                'payment_method': payment_method,
                'current_status': current_status,
                'transaction_id': transaction_id,
                'merchant_order_id': merchant_order_id,
                'remark': remark
            }
            
            # 解析交易时间
            parsed_datetime = self._parse_datetime(transaction_time)
            if not parsed_datetime:
                raise ValueError(f"无法解析交易时间: {transaction_time}")
            
            # 解析金额
            amount = self._parse_amount(amount_str)
            if amount is None:
                raise ValueError(f"无法解析金额: {amount_str}")
            
            # 确定交易类型（收入/支出）
            is_income = income_expense == '收入'
            
            # 构建描述
            description = self._build_description(counter_party, product, transaction_type)
            
            # 构建符合BaseParser标准的记录
            record = {
                'transaction_time': parsed_datetime,
                'transaction_desc': description[:500] if description else None,  # 限制长度
                'amount': amount,
                'currency': 'CNY',
                'transaction_type': '收入' if is_income else '支出',
                'category': None,  # 将由AI分类
                'remark': self._build_notes(current_status, remark)[:500] if self._build_notes(current_status, remark) else None  # 限制长度
            }
            
            return self.standardize_record(record, raw_data)
            
        except Exception as e:
            raise ValueError(f"解析记录失败: {str(e)}")
    
    def _safe_get_value(self, row: pd.Series, column: str) -> str:
        """安全获取列值"""
        try:
            value = row.get(column, '')
            if pd.isna(value):
                return '/'
            return str(value).strip()
        except:
            return '/'
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """解析金额字符串"""
        if not amount_str or amount_str == '/':
            return None
            
        try:
            # 移除¥符号和其他非数字字符（保留小数点和负号）
            cleaned = re.sub(r'[¥,，\s]', '', str(amount_str))
            
            # 处理负数（支出）
            if cleaned.startswith('-'):
                return -float(cleaned[1:])
            
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def _build_description(self, counter_party: str, product: str, transaction_type: str) -> str:
        """构建交易描述"""
        parts = []
        
        if counter_party and counter_party != '/':
            parts.append(counter_party)
        
        if product and product != '/':
            parts.append(product)
        
        if not parts and transaction_type and transaction_type != '/':
            parts.append(transaction_type)
        
        return ' - '.join(parts) if parts else '微信支付'
    
    def _extract_tags(self, transaction_type: str, payment_method: str) -> List[str]:
        """提取标签"""
        tags = []
        
        if transaction_type and transaction_type != '/':
            tags.append(transaction_type)
        
        if payment_method and payment_method != '/':
            # 简化支付方式标签
            if '信用卡' in payment_method:
                tags.append('信用卡')
            elif '储蓄卡' in payment_method:
                tags.append('储蓄卡')
            elif '零钱' in payment_method:
                tags.append('零钱')
            else:
                tags.append(payment_method)
        
        return tags
    
    def _build_notes(self, current_status: str, remark: str) -> str:
        """构建备注"""
        notes = []
        
        if current_status and current_status != '/':
            notes.append(f"状态: {current_status}")
        
        if remark and remark != '/':
            notes.append(f"备注: {remark}")
        
        return '; '.join(notes) if notes else ''
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """解析微信的日期时间格式"""
        if not datetime_str or datetime_str == '/':
            return None
        
        # 微信时间格式: 2025-07-28 17:37:35
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(datetime_str).strip(), fmt)
            except ValueError:
                continue
        
        return None