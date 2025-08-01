from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional, Dict, Any
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


async def get_or_create_category(
    name: str, 
    user_id: int, 
    db: Session,
    description: str = None,
    icon: str = None,
    color: str = None
) -> Optional[BillCategory]:
    """获取或映射账单分类（不创建新分类，只进行映射）"""
    # 首先尝试精确匹配
    category = db.query(BillCategory).filter(
        BillCategory.category_name == name
    ).first()
    
    if category:
        return category
    
    # 如果没有精确匹配，尝试智能映射
    category = map_category_name(name, db)
    
    if category:
        logger.info(f"分类映射: '{name}' -> '{category.category_name}'")
        return category
    
    # 如果无法映射，返回None（不创建新分类）
    logger.warning(f"无法映射分类: '{name}'，将使用默认分类")
    return None

def map_category_name(name: str, db: Session) -> Optional[BillCategory]:
    """智能映射分类名称到预定义分类"""
    # 分类映射规则 - 更新为新的20个分类
    category_mapping = {
        # 收入分类映射（8个）
        "工资": "工资收入",
        "薪资": "工资收入",
        "奖金": "工资收入",
        "绩效": "工资收入",
        "股票": "投资收益",
        "基金": "投资收益",
        "理财": "投资收益",
        "投资": "投资收益",
        "兼职": "兼职收入",
        "副业": "兼职收入",
        "借款": "借款收入",
        "借钱": "借款收入",
        "退款": "退款收入",
        "红包": "红包收入",
        "礼金": "红包收入",
        "压岁钱": "红包收入",
        
        # 支出分类映射（13个）
        "餐饮": "食品餐饮",
        "吃饭": "食品餐饮",
        "外卖": "食品餐饮",
        "零食": "食品餐饮",
        "饮料": "食品餐饮",
        "水果": "食品餐饮",
        "蔬菜": "食品餐饮",
        "肉类": "食品餐饮",
        "衣服": "服饰鞋包",
        "鞋子": "服饰鞋包",
        "包包": "服饰鞋包",
        "服装": "服饰鞋包",
        "化妆品": "美妆个护",
        "护肤品": "美妆个护",
        "洗护": "美妆个护",
        "日用品": "日用百货",
        "生活用品": "日用百货",
        "交通": "交通出行",
        "公交": "交通出行",
        "地铁": "交通出行",
        "打车": "交通出行",
        "加油": "交通出行",
        "停车": "交通出行",
        "房租": "住房物业",
        "物业": "住房物业",
        "水电": "住房物业",
        "燃气": "住房物业",
        "医疗": "医疗保健",
        "医院": "医疗保健",
        "药品": "医疗保健",
        "教育": "教育培训",
        "培训": "教育培训",
        "学习": "教育培训",
        "书籍": "教育培训",
        "人情": "人情社交",
        "请客": "人情社交",
        "送礼": "人情社交",
        "娱乐": "休闲玩乐",
        "游戏": "休闲玩乐",
        "电影": "休闲玩乐",
        "旅游": "休闲玩乐",
        "还款": "借还款",
        "白条": "借还款",
        "花呗": "借还款",
        "信用卡": "借还款",
    }
    
    # 尝试精确匹配
    if name in category_mapping:
        mapped_name = category_mapping[name]
        return db.query(BillCategory).filter(
            BillCategory.category_name == mapped_name
        ).first()
    
    # 尝试包含匹配
    for key, mapped_name in category_mapping.items():
        if key in name or name in key:
            return db.query(BillCategory).filter(
                BillCategory.category_name == mapped_name
            ).first()
    
    # 如果都无法匹配，返回"其他"分类
    return db.query(BillCategory).filter(
        BillCategory.category_name == "其他"
    ).first()


def find_existing_jd_bill(record: Dict[str, Any], family_user_ids: List[int], db: Session) -> Optional[Bill]:
    """
    查找已存在的京东账单记录
    
    对于京东账单，使用更精确的匹配策略：
    1. 优先使用 order_id + transaction_time + amount 的组合
    2. 如果没有order_id，则使用 transaction_time + amount + transaction_desc
    
    返回：
    - 如果找到重复记录，返回该记录
    - 如果没有找到，返回 None
    """
    try:
        raw_data = record.get("raw_data", {})
        order_id = raw_data.get("order_id")
        transaction_time = record.get("transaction_time")
        amount = record.get("amount")
        transaction_desc = record.get("transaction_desc", "")
        
        logger.debug(f"查找京东账单: family_user_ids={family_user_ids}, order_id={order_id}, time={transaction_time}, amount={amount}")
        
        # 策略1: 如果有order_id，使用order_id + transaction_time + amount进行精确匹配
        if order_id and transaction_time and amount is not None:
            existing_bill = db.query(Bill).filter(
                Bill.user_id.in_(family_user_ids),
                Bill.source_type == "jd",
                Bill.raw_data.op('->>')('order_id') == order_id,
                Bill.transaction_time == transaction_time,
                Bill.amount == amount
            ).first()
            
            if existing_bill:
                logger.info(f"找到已存在的京东账单（订单号+时间+金额匹配）: {order_id}")
                return existing_bill
        
        # 策略2: 如果没有order_id或策略1没找到，使用时间+金额+描述进行匹配
        if transaction_time and amount is not None and transaction_desc:
            # 时间容差：允许1分钟内的时间差异
            time_start = transaction_time - timedelta(minutes=1)
            time_end = transaction_time + timedelta(minutes=1)
            
            existing_bill = db.query(Bill).filter(
                Bill.user_id.in_(family_user_ids),
                Bill.source_type == "jd",
                Bill.transaction_time >= time_start,
                Bill.transaction_time <= time_end,
                Bill.amount == amount,
                Bill.transaction_desc == transaction_desc
            ).first()
            
            if existing_bill:
                logger.info(f"找到已存在的京东账单（时间+金额+描述匹配）: {transaction_desc[:50]}...")
                return existing_bill
        
        logger.debug(f"未找到重复的京东账单")
        return None
        
    except Exception as e:
        logger.error(f"查找京东账单时出错: {e}")
        return None


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
        
        # 使用组合字段进行匹配（交易时间 + 金额 + 商户名称）
        transaction_time = record.get("transaction_time")
        amount = record.get("amount")
        merchant_name = record.get("merchant_name") or record.get("transaction_desc", "")
        
        logger.debug(f"组合字段检查: time={transaction_time}, amount={amount}, merchant={merchant_name}")
        
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
                # 进一步检查商户名称或交易描述是否相似
                existing_desc = existing_bill.transaction_desc or ""
                if merchant_name and (
                    merchant_name in existing_desc or 
                    existing_desc in merchant_name or
                    merchant_name == existing_desc
                ):
                    logger.info(f"发现重复记录（组合字段匹配）: 时间={transaction_time}, 金额={amount}, 商户={merchant_name}")
                    return True
        
        logger.debug("未发现重复记录")
        return False
        
    except Exception as e:
        logger.error(f"检查重复记录时出错: {e}")
        # 出错时不阻止导入，但记录错误
        return False


@router.get("/parsers")
async def get_parsers():
    """获取可用的解析器列表"""
    return {
        "parsers": get_available_parsers(),
        "message": "支持的文件格式"
    }


@router.post("/", response_model=UploadResponse)
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
        
        # 支付宝文件重复检查
        if source_type == "alipay":
            if check_duplicate_alipay_file(file.filename, family_user_ids, db):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="此账单已经上传, 支付宝账单不支持重复上传!"
                )
        
        # 招商银行文件重复检查
        if source_type == "cmb":
            existing_cmb_bill = db.query(Bill).filter(
                Bill.user_id.in_(family_user_ids),
                Bill.source_type == "cmb",
                Bill.source_filename == file.filename
            ).first()
            
            if existing_cmb_bill:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="此招商银行账单文件已经上传过，不支持重复上传!"
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
            
            success_count = 0
            failed_count = 0
            updated_count = 0  # 新增：更新记录数
            created_bills = []
            
            # 用于批次内去重的集合
            batch_records = set()
            
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
                    
                    # 批次内去重检查（支付宝和招商银行账单不进行批次内去重）
                    if source_type not in ["alipay", "cmb"]:
                        record_key = (
                            record["transaction_time"].isoformat() if hasattr(record["transaction_time"], 'isoformat') else str(record["transaction_time"]),
                            str(record["amount"]),
                            record.get("transaction_desc", ""),
                            record.get("counter_party", "")  # 加入对手方信息
                        )
                        
                        if record_key in batch_records:
                            logger.info(f"跳过批次内重复记录 (记录 {i+1}): {record_key}")
                            continue
                        
                        batch_records.add(record_key)
                    
                    # 京东账单：查找已存在的记录并更新
                    if source_type == "jd":
                        existing_bill = find_existing_jd_bill(record, family_user_ids, db)
                        
                        if existing_bill:
                            # 更新已存在的记录
                            existing_bill.amount = record["amount"]
                            existing_bill.transaction_time = record["transaction_time"]
                            existing_bill.transaction_type = record["transaction_type"]
                            existing_bill.transaction_desc = record.get("transaction_desc")
                            existing_bill.raw_data = record.get("raw_data", {})
                            existing_bill.source_filename = file.filename  # 更新文件名
                            existing_bill.order_id = record.get("order_id")  # 更新订单号
                            existing_bill.counter_party = record.get("counter_party")  # 更新对手方
                            existing_bill.remark = record.get("remark")  # 更新备注
                            existing_bill.balance = record.get("balance")  # 更新余额
                            existing_bill.updated_at = datetime.now()
                            
                            # 自动分类
                            if auto_categorize and record.get("category"):
                                category = await get_or_create_category(
                                    record["category"], 
                                    current_user.id, 
                                    db
                                )
                                if category:
                                    existing_bill.category_id = category.id
                                else:
                                    # fallback: 强制归为"其他"分类
                                    other_category = db.query(BillCategory).filter(BillCategory.category_name == "其他").first()
                                    existing_bill.category_id = other_category.id
                            
                            created_bills.append(existing_bill)
                            updated_count += 1  # 统计更新记录数
                            logger.info(f"更新京东账单记录: {record.get('raw_data', {}).get('order_id')}")
                            continue
                    
                    # 其他来源：检查重复
                    elif source_type not in ["cmb"]:  # 招商银行已在文件级别检测重复，京东账单不进行重复检查
                        if check_duplicate_bill_other_sources(record, family_user_ids, source_type, db):
                            logger.info(f"跳过重复记录 (记录 {i+1})")
                            continue
                    
                    # 自动分类
                    category = None
                    if auto_categorize and record.get("category"):
                        category = await get_or_create_category(
                            record["category"], 
                            current_user.id, 
                            db
                        )
                    # fallback: 无论如何都要有分类
                    if not category:
                        category = db.query(BillCategory).filter(BillCategory.category_name == "其他").first()
                    # 创建新的账单记录
                    bill = Bill(
                        user_id=current_user.id,
                        amount=record["amount"],
                        transaction_time=record["transaction_time"],
                        transaction_type=record["transaction_type"],
                        transaction_desc=record.get("transaction_desc"),
                        source_type=source_type,
                        category_id=category.id,
                        raw_data=record.get("raw_data", {}),
                        source_filename=file.filename,  # 记录所有账单的文件名
                        order_id=record.get("order_id"),  # 添加订单号字段
                        counter_party=record.get("counter_party"),  # 添加对手方字段
                        remark=record.get("remark"),  # 添加备注字段
                        balance=record.get("balance")  # 添加余额字段
                    )
                    
                    try:
                        db.add(bill)
                        db.flush()  # 先flush检查是否有错误
                        created_bills.append(bill)
                        success_count += 1
                    except Exception as db_error:
                        logger.error(f"数据库插入失败 (记录 {i+1}): {db_error}")
                        logger.error(f"问题记录内容: {record}")
                        db.rollback()  # 回滚这个记录
                        failed_count += 1
                        continue
                    
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
            
            logger.info(f"文件上传完成: {file.filename}, 新增: {success_count}, 更新: {updated_count}, 失败: {failed_count}")
            
            total_records = len(parse_result.success_records) + len(parse_result.failed_records)
            total_failed = failed_count + len(parse_result.failed_records)
            total_success = success_count + updated_count  # 成功数包括新增和更新
            upload_status = "completed" if failed_count == 0 else "partial_success"
            
            # 构建警告信息
            warnings = parse_result.errors.copy() if hasattr(parse_result, 'errors') else []
            if updated_count > 0:
                warnings.append(f"更新已存在记录数: {updated_count}")
            
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
                warnings=warnings
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