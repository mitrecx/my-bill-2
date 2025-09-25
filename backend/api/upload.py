from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional, Dict, Any, Set, Tuple
import logging
import os
import tempfile
from datetime import datetime, timedelta

from config.database import get_db
from config.settings import settings
from models.user import User
from models.bill import Bill, BillCategory
from models.family import FamilyMember
from api.auth import get_current_user
from parsers import get_parser, get_available_parsers
from utils.validators import validate_file_extension, validate_file_size, detect_file_source_type
from schemas.upload import (
    UploadResponse,
    UploadHistoryResponse,
    UploadStatsResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])


async def get_user_family_members(user: User, db: Session) -> List[int]:
    """获取用户家庭中所有成员的用户ID列表"""
    # 获取用户所属的家庭
    family_member = db.query(FamilyMember).filter(
        FamilyMember.user_id == user.id
    ).first()
    
    if not family_member:
        return [user.id]  # 如果用户不属于任何家庭，只返回自己的ID
    
    # 获取该家庭的所有成员
    family_members = db.query(FamilyMember).filter(
        FamilyMember.family_id == family_member.family_id
    ).all()
    
    return [fm.user_id for fm in family_members]


async def get_existing_category(
    name: str, 
    db: Session
) -> Optional[BillCategory]:
    """获取现有的账单分类（不创建新分类）"""
    # 尝试精确匹配现有分类
    category = db.query(BillCategory).filter(
        BillCategory.category_name == name
    ).first()
    
    return category


def handle_jd_bill_overlap(filename: str, records: List[Dict[str, Any]], family_user_ids: List[int], db: Session) -> int:
    """
    处理JD账单的按日期覆盖逻辑（与CMB账单保持一致）
    删除数据库中与新文件记录日期相同的所有JD账单记录
    
    Args:
        filename: 当前上传的文件名
        records: 当前文件解析出的账单记录
        family_user_ids: 家庭成员用户ID列表
        db: 数据库会话
    
    Returns:
        被删除的重叠记录数量
    """
    try:
        # 获取当前文件中的所有交易日期
        if not records:
            return 0
            
        transaction_dates = set()  # 使用set去重
        for record in records:
            transaction_time = record.get("transaction_time")
            if transaction_time:
                if isinstance(transaction_time, str):
                    # 如果是字符串，尝试解析
                    try:
                        transaction_time = datetime.fromisoformat(transaction_time.replace('Z', '+00:00'))
                    except:
                        continue
                transaction_dates.add(transaction_time.date())
        
        if not transaction_dates:
            return 0
            
        logger.info(f"当前JD文件 {filename} 包含的交易日期: {sorted(transaction_dates)}")
        
        # 优化：使用单个SQL查询删除所有相关日期的记录
        # 构建日期范围条件
        date_conditions = []
        for date in transaction_dates:
            date_conditions.append(func.date(Bill.transaction_time) == date)
        
        # 使用or_条件组合所有日期
        if date_conditions:
            # 先查询要删除的记录数量
            bills_to_delete = db.query(Bill).filter(
                Bill.user_id.in_(family_user_ids),
                Bill.source_type == "jd",
                or_(*date_conditions)
            ).all()
            
            deleted_count = len(bills_to_delete)
            
            if deleted_count > 0:
                logger.info(f"准备删除 {deleted_count} 条JD记录")
                
                # 批量删除
                db.query(Bill).filter(
                    Bill.user_id.in_(family_user_ids),
                    Bill.source_type == "jd",
                    or_(*date_conditions)
                ).delete(synchronize_session=False)
                
                db.commit()
                logger.info(f"JD账单按日期覆盖完成，共删除 {deleted_count} 条记录")
            
            return deleted_count
        
        return 0
        
    except Exception as e:
        logger.error(f"处理JD账单按日期覆盖时出错: {e}")
        db.rollback()
        return 0


def check_duplicate_alipay_file(filename: str, family_id: int, db: Session) -> bool:
    """
    检查支付宝文件是否已经上传过
    """
    try:
        logger.info(f"检查支付宝文件重复: filename={filename}, family_id={family_id}")
        existing_bill = db.query(Bill).filter(
            Bill.family_id == family_id,
            Bill.source_type == "alipay",
            Bill.source_filename == filename
        ).first()
        
        result = existing_bill is not None
        logger.info(f"支付宝文件重复检查结果: {result}, existing_bill_id={existing_bill.id if existing_bill else None}")
        return result
        
    except Exception as e:
        logger.error(f"检查支付宝文件重复失败: {e}")
        return False


def check_duplicate_alipay_file(filename: str, family_user_ids: List[int], db: Session) -> bool:
    """
    检查支付宝文件是否已经上传过
    """
    try:
        logger.info(f"检查支付宝文件重复: filename={filename}, family_user_ids={family_user_ids}")
        existing_bill = db.query(Bill).filter(
            Bill.user_id.in_(family_user_ids),
            Bill.source_type == "alipay",
            Bill.source_filename == filename
        ).first()
        
        result = existing_bill is not None
        logger.info(f"支付宝文件重复检查结果: {result}, existing_bill_id={existing_bill.id if existing_bill else None}")
        return result
        
    except Exception as e:
        logger.error(f"检查支付宝文件重复失败: {e}")
        return False


def check_duplicate_cmb_record(record: Dict[str, Any], family_user_ids: List[int], db: Session) -> bool:
    """
    招商银行账单重复数据判定（严格匹配）
    满足以下条件即视为重复：
      - 仅比较交易日期（忽略时间）：func.date(transaction_time) == record.transaction_time.date()
      - 金额相等（amount）
      - 原始数据中的 counter_party 完全一致（raw_data->>'counter_party'）
    匹配范围限定在当前用户家庭成员（family_user_ids）并且来源为 cmb。
    """
    try:
        transaction_time = record.get("transaction_time")
        amount = record.get("amount")
        # 从解析后的标准化记录中读取原始对手方
        raw_data = record.get("raw_data", {}) or {}
        counter_party = raw_data.get("counter_party")

        if transaction_time is None or amount is None:
            return False

        # 仅比较日期部分
        record_date = transaction_time.date()

        query = db.query(Bill).filter(
            Bill.user_id.in_(family_user_ids),
            Bill.source_type == "cmb",
            func.date(Bill.transaction_time) == record_date,
            Bill.amount == float(amount)
        )

        # 严格匹配 counter_party：必须完全一致（当上传记录有该字段时）
        if counter_party is not None:
            query = query.filter(Bill.raw_data.op('->>')('counter_party') == str(counter_party))
        else:
            # 上传记录未提供对手方时，同样要求库中该字段为空（严格一致）
            query = query.filter(Bill.raw_data.op('->>')('counter_party') == None)  # noqa: E711

        existing_bill = query.first()
        if existing_bill:
            logger.info(
                f"发现CMB重复记录: 日期={record_date}, 金额={amount}, 对手方={counter_party}"
            )
            return True
        return False
    except Exception as e:
        logger.error(f"检查CMB重复记录失败: {e}")
        return False


def check_duplicate_alipay_record(record: Dict[str, Any], family_user_ids: List[int], db: Session) -> bool:
    """
    支付宝账单重复数据判定（严格匹配）
    满足以下三个条件完全相同即视为重复：
      - 交易时间相同（transaction_time）
      - 交易金额相同（amount）
      - 交易备注相同（transaction_desc）
    匹配范围限定在当前用户家庭成员（family_user_ids）并且来源为 alipay。
    """
    try:
        transaction_time = record.get("transaction_time")
        amount = record.get("amount")
        transaction_desc = record.get("transaction_desc") or ""

        if transaction_time is None or amount is None:
            return False

        existing_bill = db.query(Bill).filter(
            Bill.user_id.in_(family_user_ids),
            Bill.source_type == "alipay",
            Bill.transaction_time == transaction_time,
            Bill.amount == amount,
            Bill.transaction_desc == transaction_desc
        ).first()

        is_dup = existing_bill is not None
        if is_dup:
            logger.info(
                f"发现支付宝重复记录: 时间={transaction_time}, 金额={amount}, 备注={transaction_desc}"
            )
        return is_dup
    except Exception as e:
        logger.error(f"检查支付宝重复记录失败: {e}")
        return False


def check_duplicate_wechat_record(record: Dict[str, Any], family_user_ids: List[int], db: Session) -> bool:
    """
    微信账单重复数据判定（严格匹配）
    满足以下两个条件完全相同即视为重复：
      - 交易时间相同（transaction_time，精确匹配到秒）
      - 原始数据中的交易单号完全一致（raw_data->>'transaction_id'）
    匹配范围限定在当前用户家庭成员（family_user_ids）并且来源为 wechat。
    """
    try:
        transaction_time = record.get("transaction_time")
        raw_data = record.get("raw_data", {}) or {}
        transaction_id = raw_data.get("transaction_id")

        # 严格匹配：时间和交易单号必须同时存在
        if transaction_time is None:
            return False
        if not transaction_id or str(transaction_id).strip() in ["", "/"]:
            return False

        existing_bill = db.query(Bill).filter(
            Bill.user_id.in_(family_user_ids),
            Bill.source_type == "wechat",
            Bill.transaction_time == transaction_time,
            Bill.raw_data.op('->>')('transaction_id') == str(transaction_id).strip()
        ).first()

        is_dup = existing_bill is not None
        if is_dup:
            logger.info(
                f"发现微信重复记录: 时间={transaction_time}, 交易单号={transaction_id}"
            )
        return is_dup
    except Exception as e:
        logger.error(f"检查微信重复记录失败: {e}")
        return False


def handle_alipay_bill_overlap(filename: str, records: List[Dict[str, Any]], family_user_ids: List[int], db: Session) -> int:
    """
    处理支付宝账单的按日期覆盖逻辑（优化版本）
    使用单个SQL查询删除数据库中与新文件记录日期相同的所有支付宝账单记录
    
    Args:
        filename: 当前上传的文件名
        records: 当前文件解析出的账单记录
        family_user_ids: 家庭成员用户ID列表
        db: 数据库会话
    
    Returns:
        被删除的重叠记录数量
    """
    try:
        # 获取当前文件中的所有交易日期
        if not records:
            return 0
            
        transaction_dates = set()  # 使用set去重
        for record in records:
            transaction_time = record.get("transaction_time")
            if transaction_time:
                if isinstance(transaction_time, str):
                    # 如果是字符串，尝试解析
                    try:
                        transaction_time = datetime.fromisoformat(transaction_time.replace('Z', '+00:00'))
                    except:
                        continue
                transaction_dates.add(transaction_time.date())
        
        if not transaction_dates:
            return 0
            
        logger.info(f"当前支付宝文件 {filename} 包含的交易日期: {sorted(transaction_dates)}")
        
        # 优化：使用单个SQL查询删除所有相关日期的记录
        # 构建日期范围条件
        date_conditions = []
        for date in transaction_dates:
            date_conditions.append(func.date(Bill.transaction_time) == date)
        
        # 使用or_条件组合所有日期
        if date_conditions:
            # 先查询要删除的记录数量
            bills_to_delete = db.query(Bill).filter(
                Bill.user_id.in_(family_user_ids),
                Bill.source_type == "alipay",
                or_(*date_conditions)
            ).all()
            
            deleted_count = len(bills_to_delete)
            
            if deleted_count > 0:
                logger.info(f"准备删除 {deleted_count} 条支付宝记录")
                
                # 批量删除
                db.query(Bill).filter(
                    Bill.user_id.in_(family_user_ids),
                    Bill.source_type == "alipay",
                    or_(*date_conditions)
                ).delete(synchronize_session=False)
                
                db.commit()
                logger.info(f"支付宝账单按日期覆盖完成，共删除 {deleted_count} 条记录")
            
            return deleted_count
        
        return 0
        
    except Exception as e:
        logger.error(f"处理支付宝账单按日期覆盖时出错: {e}")
        db.rollback()
        return 0


def handle_wechat_bill_overlap(filename: str, records: List[Dict[str, Any]], family_user_ids: List[int], db: Session) -> int:
    """
    处理微信账单的按日期覆盖逻辑（与CMB账单保持一致）
    删除数据库中与新文件记录日期相同的所有微信账单记录
    
    Args:
        filename: 当前上传的文件名
        records: 当前文件解析出的账单记录
        family_user_ids: 家庭成员用户ID列表
        db: 数据库会话
    
    Returns:
        被删除的重叠记录数量
    """
    try:
        # 获取当前文件中的所有交易日期
        if not records:
            return 0
            
        transaction_dates = set()  # 使用set去重
        for record in records:
            transaction_time = record.get("transaction_time")
            if transaction_time:
                if isinstance(transaction_time, str):
                    # 如果是字符串，尝试解析
                    try:
                        transaction_time = datetime.fromisoformat(transaction_time.replace('Z', '+00:00'))
                    except:
                        continue
                transaction_dates.add(transaction_time.date())
        
        if not transaction_dates:
            return 0
            
        logger.info(f"当前微信文件 {filename} 包含的交易日期: {sorted(transaction_dates)}")
        
        # 优化：使用单个SQL查询删除所有相关日期的记录
        # 构建日期范围条件
        date_conditions = []
        for date in transaction_dates:
            date_conditions.append(func.date(Bill.transaction_time) == date)
        
        # 使用or_条件组合所有日期
        if date_conditions:
            # 先查询要删除的记录数量
            bills_to_delete = db.query(Bill).filter(
                Bill.user_id.in_(family_user_ids),
                Bill.source_type == "wechat",
                or_(*date_conditions)
            ).all()
            
            deleted_count = len(bills_to_delete)
            
            if deleted_count > 0:
                logger.info(f"准备删除 {deleted_count} 条微信记录")
                
                # 批量删除
                db.query(Bill).filter(
                    Bill.user_id.in_(family_user_ids),
                    Bill.source_type == "wechat",
                    or_(*date_conditions)
                ).delete(synchronize_session=False)
                
                db.commit()
                logger.info(f"微信账单按日期覆盖完成，共删除 {deleted_count} 条记录")
            
            return deleted_count
        
        return 0
        
    except Exception as e:
        logger.error(f"处理微信账单按日期覆盖时出错: {e}")
        db.rollback()
        return 0


def handle_cmb_bill_overlap(filename: str, records: List[Dict[str, Any]], family_user_ids: List[int], db: Session) -> int:
    """
    处理CMB账单的按日期覆盖逻辑
    删除数据库中与新文件记录日期相同的所有CMB账单记录
    
    Args:
        filename: 当前上传的文件名
        records: 当前文件解析出的账单记录
        family_user_ids: 家庭成员用户ID列表
        db: 数据库会话
    
    Returns:
        被删除的重叠记录数量
    """
    try:
        # 获取当前文件中的所有交易日期
        if not records:
            return 0
            
        transaction_dates = set()  # 使用set去重
        for record in records:
            transaction_time = record.get("transaction_time")
            if transaction_time:
                if isinstance(transaction_time, str):
                    # 如果是字符串，尝试解析
                    try:
                        transaction_time = datetime.fromisoformat(transaction_time.replace('Z', '+00:00'))
                    except:
                        continue
                transaction_dates.add(transaction_time.date())
        
        if not transaction_dates:
            return 0
            
        logger.info(f"当前CMB文件 {filename} 包含的交易日期: {sorted(transaction_dates)}")
        
        # 优化：使用单个SQL查询删除所有相关日期的记录
        # 构建日期范围条件
        date_conditions = []
        for date in transaction_dates:
            date_conditions.append(func.date(Bill.transaction_time) == date)
        
        # 使用or_条件组合所有日期
        if date_conditions:
            # 先查询要删除的记录数量
            bills_to_delete = db.query(Bill).filter(
                Bill.user_id.in_(family_user_ids),
                Bill.source_type == "cmb",
                or_(*date_conditions)
            ).all()
            
            deleted_count = len(bills_to_delete)
            
            if deleted_count > 0:
                logger.info(f"准备删除 {deleted_count} 条CMB记录")
                
                # 批量删除
                db.query(Bill).filter(
                    Bill.user_id.in_(family_user_ids),
                    Bill.source_type == "cmb",
                    or_(*date_conditions)
                ).delete(synchronize_session=False)
                
                db.commit()
                logger.info(f"CMB账单按日期覆盖完成，共删除 {deleted_count} 条记录")
            
            return deleted_count
        
        return 0
        
    except Exception as e:
        logger.error(f"处理CMB账单按日期覆盖时出错: {e}")
        db.rollback()
        return 0


def check_duplicate_bill_other_sources(record: Dict[str, Any], family_user_ids: List[int], source_type: str, db: Session) -> bool:
    """
    检查非京东账单记录是否重复
    """
    try:
        # 支付宝账单不进行记录级别的去重，因为相同记录可能是两笔独立交易
        if source_type == "alipay":
            return False
        
        # 提取订单号（如果有的话）
        order_id = None
        raw_data = record.get("raw_data", {})
        
        if raw_data:
            order_id = raw_data.get("order_id") or raw_data.get("merchant_order_id")
        
        if not order_id:
            order_id = record.get("order_id") or record.get("merchant_order_id")
        
        # 如果有订单号，优先使用订单号匹配
        if order_id and order_id.strip():
            logger.debug(f"使用订单号进行去重检查: {order_id}")
            
            existing_bill = db.query(Bill).filter(
                Bill.user_id.in_(family_user_ids),
                Bill.source_type == source_type,
                Bill.raw_data.op('->>')('order_id') == order_id.strip()
            ).first()
            
            if existing_bill:
                logger.info(f"发现重复记录（订单号匹配）: {order_id}")
                return True
        
        # 使用组合字段进行匹配（交易时间 + 金额 + 交易描述）
        transaction_time = record.get("transaction_time")
        amount = record.get("amount")
        transaction_desc = record.get("transaction_desc", "")
        
        logger.debug(f"组合字段检查: time={transaction_time}, amount={amount}, desc={transaction_desc}")
        
        if transaction_time and amount is not None:
            # 时间容差：允许1分钟内的时间差异
            time_start = transaction_time - timedelta(minutes=1)
            time_end = transaction_time + timedelta(minutes=1)
            
            existing_bill = db.query(Bill).filter(
                Bill.user_id.in_(family_user_ids),
                Bill.source_type == source_type,
                Bill.transaction_time >= time_start,
                Bill.transaction_time <= time_end,
                Bill.amount == amount
            ).first()
            
            if existing_bill:
                # 进一步检查交易描述是否相似
                existing_desc = existing_bill.transaction_desc or ""
                if transaction_desc and (
                    transaction_desc in existing_desc or 
                    existing_desc in transaction_desc or
                    transaction_desc == existing_desc
                ):
                    logger.info(f"发现重复记录（组合字段匹配）: 时间={transaction_time}, 金额={amount}, 描述={transaction_desc}")
                    return True
        
        logger.debug("未发现重复记录")
        return False
        
    except Exception as e:
        logger.error(f"检查重复记录时出错: {e}")
        # 出错时不阻止导入，但记录错误
        return False


@router.get("/parsers")
@router.get("/parsers/")
async def get_parsers():
    """获取可用的解析器列表"""
    return {
        "parsers": get_available_parsers(),
        "message": "支持的文件格式"
    }


@router.post("/", response_model=UploadResponse)
@router.post("", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    source_type: Optional[str] = Form(None),
    auto_categorize: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传并解析账单文件"""
    try:
        # 获取用户家庭中所有成员的用户ID
        family_user_ids = await get_user_family_members(current_user, db)
        
        # 验证文件
        file_ext_valid, file_ext_msg = validate_file_extension(file.filename)
        if not file_ext_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=file_ext_msg
            )
        
        file_size_valid, file_size_msg = validate_file_size(file.size)
        if not file_size_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=file_size_msg
            )
        
        # 检测文件类型
        if not source_type:
            source_type = detect_file_source_type(file.filename)
        
        if not source_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法识别文件类型，请指定source_type参数"
            )
        
        # 获取解析器
        parser = get_parser(source_type)
        if not parser:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {source_type}"
            )
        
        # 读取文件内容
        content = await file.read()
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 解析文件
            parse_result = parser.parse_file(temp_file_path)
            
            # CMB、JD、支付宝和微信账单：处理时间范围重叠覆盖逻辑
            deleted_count = 0
            if source_type == "cmb":
                # 新规则：不进行按日期覆盖删除，保留数据库中现有记录
                deleted_count = 0
            elif source_type == "jd":
                # 新规则：不进行按日期覆盖删除，保留数据库中现有记录
                deleted_count = 0
            elif source_type == "alipay":
                # 新规则：不进行按日期覆盖删除，保留数据库中现有记录
                deleted_count = 0
            elif source_type == "wechat":
                # 新规则：不进行按日期覆盖删除，保留数据库中现有记录
                deleted_count = 0
            # 移除旧的按日期覆盖删除逻辑
            # elif source_type == "wechat":
            #     deleted_count = handle_wechat_bill_overlap(
            #         file.filename, 
            #         parse_result.success_records, 
            #         family_user_ids, 
            #         db
            #     )

            success_count = 0
            failed_count = 0
            updated_count = 0  # 新增：更新记录数
            created_bills = []

            # 用于批次内去重的集合
            batch_records = set()

            # 微信账单：预取现有记录以优化去重性能
            wechat_existing_pairs: Set[Tuple[datetime, str]] = set()
            if source_type == "wechat":
                try:
                    import_ids: Set[str] = set()
                    for r in parse_result.success_records:
                        tid = (r.get('raw_data') or {}).get('transaction_id')
                        if tid is not None:
                            tid_str = str(tid).strip()
                            if tid_str and tid_str != '/':
                                import_ids.add(tid_str)
                    if import_ids:
                        rows = db.query(Bill.transaction_time, Bill.raw_data.op('->>')('transaction_id')).filter(
                            Bill.user_id.in_(family_user_ids),
                            Bill.source_type == "wechat",
                            Bill.raw_data.op('->>')('transaction_id').in_(list(import_ids))
                        ).all()
                        wechat_existing_pairs = {(row[0], str(row[1])) for row in rows}
                        logger.info(f"微信预取去重集合大小: {len(wechat_existing_pairs)}")
                except Exception as e:
                    logger.error(f"微信预取去重失败: {e}")

            # 京东账单：预取现有记录以优化去重性能
            jd_existing_pairs: Set[Tuple[datetime, str]] = set()
            if source_type == "jd":
                try:
                    import_order_ids: Set[str] = set()
                    for r in parse_result.success_records:
                        oid = (r.get('raw_data') or {}).get('order_id')
                        if oid is not None:
                            oid_str = str(oid).strip()
                            if oid_str and oid_str != '/':
                                import_order_ids.add(oid_str)
                    if import_order_ids:
                        rows = db.query(Bill.transaction_time, Bill.raw_data.op('->>')('order_id')).filter(
                            Bill.user_id.in_(family_user_ids),
                            Bill.source_type == "jd",
                            Bill.raw_data.op('->>')('order_id').in_(list(import_order_ids))
                        ).all()
                        jd_existing_pairs = {(row[0], str(row[1])) for row in rows}
                        logger.info(f"京东预取去重集合大小: {len(jd_existing_pairs)}")
                except Exception as e:
                    logger.error(f"京东预取去重失败: {e}")

            # 处理成功解析的记录
            for i, record in enumerate(parse_result.success_records):
                try:
                    # 检查必需字段
                    required_fields = ["amount", "transaction_time", "transaction_type"]
                    missing_fields = [field for field in required_fields if field not in record or record[field] is None]

                    if missing_fields:
                        logger.warning(f"记录 {i+1} 缺少必需字段: {missing_fields}, 记录内容: {record}")
                        failed_count += 1
                        continue

                    # 招商银行：严格去重（按日期、金额、对手方）
                    if source_type == "cmb":
                        if check_duplicate_cmb_record(record, family_user_ids, db):
                            logger.info(f"跳过CMB重复记录 (记录 {i+1})")
                            continue

                    # 支付宝：严格按三字段去重（时间、金额、备注）
                    if source_type == "alipay":
                        if check_duplicate_alipay_record(record, family_user_ids, db):
                            logger.info(f"跳过支付宝重复记录 (记录 {i+1})")
                            continue

                    # 微信：严格去重（交易时间、交易单号），优先使用预取集合
                    if source_type == "wechat":
                        tx_time = record.get("transaction_time")
                        tx_id = str((record.get("raw_data") or {}).get("transaction_id") or "").strip()
                        if tx_id and tx_id != "/" and tx_time is not None:
                            if (tx_time, tx_id) in wechat_existing_pairs:
                                logger.info(f"跳过微信重复记录 (记录 {i+1})：时间={tx_time}, 交易单号={tx_id}")
                                continue
                        else:
                            # 当交易单号缺失或为'/'时，不进行去重
                            pass

                    # 京东：严格去重（交易时间、订单号），优先使用预取集合
                    if source_type == "jd":
                        tx_time = record.get("transaction_time")
                        order_id = str((record.get("raw_data") or {}).get("order_id") or "").strip()
                        if order_id and order_id != "/" and tx_time is not None:
                            if (tx_time, order_id) in jd_existing_pairs:
                                logger.info(f"跳过京东重复记录 (记录 {i+1})：时间={tx_time}, 订单号={order_id}")
                                continue
                        else:
                            # 当订单号缺失或为'/'时，不进行去重
                            pass

                    # 其他来源：检查重复
                    if source_type not in ["cmb", "jd", "alipay", "wechat"]:  # 招商银行、京东、支付宝和微信账单已在文件级别检测/处理
                        if check_duplicate_bill_other_sources(record, family_user_ids, source_type, db):
                            logger.info(f"跳过重复记录 (记录 {i+1})")
                            continue

                    # 分类处理：只查找现有分类，不自动创建
                    category = None
                    if auto_categorize and record.get("category"):
                        category = await get_existing_category(
                            record["category"], 
                            db
                        )
                    # fallback: 如果没有找到匹配的分类，使用"其他"分类
                    if not category:
                        category = db.query(BillCategory).filter(BillCategory.category_name == "其他").first()
                    # 使用交易描述字段
                    combined_description = record.get("transaction_desc", '')

                    # 创建新的账单记录
                    bill = Bill(
                        user_id=current_user.id,
                        amount=record["amount"],
                        transaction_time=record["transaction_time"],
                        transaction_type=record["transaction_type"],
                        transaction_desc=combined_description,  # 使用组合后的描述
                        source_type=source_type,
                        source_filename=file.filename,
                        category_id=category.id if category else None,
                        currency=record.get("currency"),
                        raw_data=record.get("raw_data", {})
                    )

                    db.add(bill)
                    created_bills.append(bill)
                    success_count += 1

                except Exception as e:
                    logger.error(f"创建账单记录失败 (记录 {i+1}): {e}")
                    logger.error(f"问题记录内容: {record}")
                    failed_count += 1

            # 最终提交所有成功的记录
            try:
                db.commit()
            except Exception as commit_error:
                logger.error(f"最终提交失败: {commit_error}")
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="数据库提交失败"
                )
            
            # AI批量分类处理
            ai_classified_count = 0
            if auto_categorize and created_bills:
                try:
                    from services.ai_classification_service import ai_classification_service
                    ai_service = ai_classification_service
                    
                    if ai_service.is_available():
                        logger.info(f"开始对 {len(created_bills)} 个账单进行AI分类")
                        
                        # 准备账单数据用于AI分类（移除交易时间，添加账单ID）
                        bills_data = []
                        for bill in created_bills:
                            # 构建描述：组合交易说明和交易分类
                            description_parts = []
                            if bill.transaction_desc:
                                # 对于支付宝账单，需要从transaction_desc中提取纯备注内容（去掉"来源:"部分）
                                if bill.source_type == 'alipay':
                                    # 支付宝的transaction_desc格式可能是："备注内容 | 来源: 账单同步"
                                    desc_text = bill.transaction_desc
                                    if ' | 来源:' in desc_text:
                                        # 只取备注部分，去掉来源部分
                                        desc_text = desc_text.split(' | 来源:')[0]
                                    description_parts.append(desc_text)
                                else:
                                    description_parts.append(bill.transaction_desc)
                            
                            # 从raw_data中获取交易分类
                            if bill.raw_data and isinstance(bill.raw_data, dict):
                                category = bill.raw_data.get('category')
                                if category and category.strip():
                                    if bill.source_type == 'jd':
                                        description_parts.append(f"[{category}]")
                                    elif bill.source_type == 'alipay':
                                        description_parts.append(f"[{category}]")
                            
                            bill_data = {
                                'id': bill.id,
                                'amount': float(bill.amount),
                                'transaction_type': bill.transaction_type,
                                'description': ' '.join(description_parts) if description_parts else '',
                                'source_type': bill.source_type
                            }
                            bills_data.append(bill_data)
                        
                        # 使用优化的批量AI分类（一次处理多个账单）
                        classification_results = ai_service.classify_bills_batch_optimized(bills_data, db, current_user.id)
                        
                        # 应用分类结果
                        for bill_id, category_name in classification_results:
                            if category_name:
                                # 查找对应的账单和分类
                                bill = db.query(Bill).filter(Bill.id == bill_id).first()
                                category = db.query(BillCategory).filter(
                                    BillCategory.category_name == category_name
                                ).first()
                                
                                if bill and category:
                                    bill.category_id = category.id
                                    ai_classified_count += 1
                                    logger.info(f"账单 {bill_id} 分类为: {category_name}")
                        
                        # 提交AI分类结果
                        db.commit()
                        logger.info(f"AI分类完成，成功分类 {ai_classified_count} 个账单")
                    else:
                        logger.warning("AI分类服务不可用，跳过自动分类")
                        
                except Exception as e:
                    logger.error(f"AI批量分类失败: {e}")
                    # AI分类失败不影响账单导入，只记录错误
            
            logger.info(f"文件上传完成: {file.filename}, 新增: {success_count}, 更新: {updated_count}, 失败: {failed_count}, AI分类: {ai_classified_count}")
            
            total_records = len(parse_result.success_records) + len(parse_result.failed_records)
            total_failed = failed_count + len(parse_result.failed_records)
            total_success = success_count + updated_count  # 成功数包括新增和更新
            upload_status = "completed" if failed_count == 0 else "partial_success"
            
            # 构建警告信息
            warnings = parse_result.errors.copy() if hasattr(parse_result, 'errors') else []
            if updated_count > 0:
                warnings.append(f"更新已存在记录数: {updated_count}")
            if deleted_count > 0:
                warnings.append(f"覆盖重叠时间范围内的旧记录数: {deleted_count}")
            
            # 构建错误信息列表
            error_messages = []
            # 添加解析失败的记录错误信息
            for failed_record in parse_result.failed_records:
                if isinstance(failed_record, dict) and 'parse_error' in failed_record:
                    error_messages.append(failed_record['parse_error'])
                else:
                    error_messages.append(str(failed_record))
            
            # 添加保存失败的记录数
            if failed_count > 0:
                error_messages.append(f"保存失败记录数: {failed_count}")
            
            return UploadResponse(
                upload_id=0,  # 临时ID
                filename=file.filename,
                source_type=source_type,
                total_records=total_records,
                success_count=total_success,  # 总成功数（新增+更新）
                created_count=success_count,  # 新增记录数
                updated_count=updated_count,  # 更新记录数
                failed_count=total_failed,
                status=upload_status,
                created_bills=[bill.id for bill in created_bills],
                errors=error_messages,
                warnings=warnings,
                ai_classified_count=ai_classified_count  # AI分类成功数量
            )
            
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件上传失败"
        )


@router.get("/history", response_model=List[UploadHistoryResponse])
@router.get("/history/", response_model=List[UploadHistoryResponse])
async def get_upload_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取上传历史记录"""
    try:
        # 获取用户家庭中所有成员的用户ID
        family_user_ids = await get_user_family_members(current_user, db)
        
        # 查询上传历史
        bills = db.query(Bill).filter(
            Bill.user_id.in_(family_user_ids),
            Bill.source_filename.isnot(None)
        ).order_by(Bill.created_at.desc()).all()
        
        # 按文件名分组统计
        file_stats = {}
        for bill in bills:
            filename = bill.source_filename
            if filename not in file_stats:
                file_stats[filename] = {
                    "filename": filename,
                    "source_type": bill.source_type,
                    "upload_time": bill.created_at,
                    "total_records": 0,
                    "uploader": bill.user.username if bill.user else "未知用户"
                }
            file_stats[filename]["total_records"] += 1
        
        return list(file_stats.values())
        
    except Exception as e:
        logger.error(f"获取上传历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取上传历史失败"
        )


@router.get("/stats", response_model=UploadStatsResponse)
@router.get("/stats/", response_model=UploadStatsResponse)
async def get_upload_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取上传统计信息"""
    try:
        # 获取用户家庭中所有成员的用户ID
        family_user_ids = await get_user_family_members(current_user, db)
        
        # 统计总记录数
        total_bills = db.query(Bill).filter(
            Bill.user_id.in_(family_user_ids)
        ).count()
        
        # 统计各来源类型的记录数
        source_stats = db.query(
            Bill.source_type,
            func.count(Bill.id).label('count')
        ).filter(
            Bill.user_id.in_(family_user_ids)
        ).group_by(Bill.source_type).all()
        
        # 统计上传文件数
        uploaded_files = db.query(
            func.count(func.distinct(Bill.source_filename))
        ).filter(
            Bill.user_id.in_(family_user_ids),
            Bill.source_filename.isnot(None)
        ).scalar()
        
        return UploadStatsResponse(
            total_bills=total_bills,
            uploaded_files=uploaded_files or 0,
            source_stats={stat.source_type: stat.count for stat in source_stats}
        )
        
    except Exception as e:
        logger.error(f"获取上传统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取上传统计失败"
        )


@router.delete("/{upload_id}")
@router.delete("/{upload_id}/")
async def delete_upload_record(
    upload_id: int,
    delete_bills: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除上传记录（可选择是否同时删除相关账单）"""
    try:
        # 由于UploadRecord模型不存在，这个功能暂时不可用
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="上传记录删除功能暂未实现"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除上传记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除上传记录失败"
        )