from .base_parser import BaseParser, ParseResult
from .alipay_parser import AlipayParser
from .jd_parser import JDParser
from .cmb_parser import CMBParser
from typing import Optional, Dict, Type

# 解析器映射
PARSER_MAP: Dict[str, Type[BaseParser]] = {
    "alipay": AlipayParser,
    "jd": JDParser,
    "cmb": CMBParser,
}


def get_parser(source_type: str) -> Optional[BaseParser]:
    """根据来源类型获取对应的解析器实例"""
    parser_class = PARSER_MAP.get(source_type.lower())
    if parser_class:
        return parser_class()
    return None


def get_available_parsers() -> Dict[str, str]:
    """获取所有可用的解析器及其描述"""
    return {
        "alipay": "支付宝账单解析器 (CSV格式)",
        "jd": "京东账单解析器 (CSV格式)",
        "cmb": "招商银行账单解析器 (PDF格式)",
    }


__all__ = [
    "BaseParser",
    "ParseResult",
    "AlipayParser",
    "JDParser", 
    "CMBParser",
    "get_parser",
    "get_available_parsers",
    "PARSER_MAP",
] 