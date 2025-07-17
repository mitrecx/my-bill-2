from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
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


async def get_user_families(user: User, db: Session) -> List[int]:
    """获取用户所属的家庭ID列表"""
    family_members = db.query(FamilyMember).filter(
        FamilyMember.user_id == user.id
    ).all()
    return [fm.family_id for fm in family_members]


async def get_or_create_category(
    name: str, 
    family_id: int, 
    db: Session,
    description: str = None,
    icon: str = None,
    color: str = None
) -> BillCategory:
    """获取或创建账单分类"""
    category = db.query(BillCategory).filter(
        BillCategory.category_name == name,
        BillCategory.family_id == family_id
    ).first()
    
    if not category:
        category = BillCategory(
            category_name=name,
            family_id=family_id,
            icon=icon or "category",
            color=color or "#666666"
        )
        db.add(category)
        db.commit()
        db.refresh(category)
    
    return category


def find_existing_jd_bill(record: Dict[str, Any], family_id: int, db: Session) -> Optional[Bill]:
    """
    查找已存在的京东账单记录
    
    返回：
    - 如果找到重复记录，返回该记录
    - 如果没有找到，返回 None
    """
    try:
        raw_data = record.get("raw_data", {})
        order_id = raw_data.get("order_id")
        
        logger.debug(f"查找京东账单: family_id={family_id}, order_id={order_id}")
        
        if not order_id:
            logger.warning("京东账单缺少交易订单号")
            return None
        
        # 使用交易订单号进行精确匹配
        existing_bill = db.query(Bill).filter(
            Bill.family_id == family_id,
            Bill.source_type == "jd",
            Bill.raw_data.op('->>')('order_id') == order_id
        ).first()
        
        if existing_bill:
            logger.info(f"找到已存在的京东账单（订单号匹配）: {order_id}")
        else:
            logger.debug(f"未找到重复的京东账单: {order_id}")
            
        return existing_bill
        
    except Exception as e:
        logger.error(f"查找京东账单时出错: {e}")
        return None


def check_duplicate_bill_other_sources(record: Dict[str, Any], family_id: int, source_type: str, db: Session) -> bool:
    """
    检查非京东账单记录是否重复
    """
    try:
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
                Bill.family_id == family_id,
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
                Bill.family_id == family_id,
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
    family_id: int = Form(...),
    source_type: Optional[str] = Form(None),
    auto_categorize: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传并解析账单文件"""
    try:
        # 验证用户是否属于指定家庭
        user_family_ids = await get_user_families(current_user, db)
        if family_id not in user_family_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问指定家庭"
            )
        
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
            
            success_count = 0
            failed_count = 0
            updated_count = 0  # 新增：更新记录数
            created_bills = []
            
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
                    
                    # 京东账单：查找已存在的记录并更新
                    if source_type == "jd":
                        existing_bill = find_existing_jd_bill(record, family_id, db)
                        
                        if existing_bill:
                            # 更新已存在的记录
                            existing_bill.amount = record["amount"]
                            existing_bill.transaction_time = record["transaction_time"]
                            existing_bill.transaction_type = record["transaction_type"]
                            existing_bill.transaction_desc = record.get("transaction_desc")
                            existing_bill.raw_data = record.get("raw_data", {})
                            existing_bill.updated_at = datetime.now()
                            
                            # 自动分类
                            if auto_categorize and record.get("category"):
                                category = await get_or_create_category(
                                    record["category"], 
                                    family_id, 
                                    db
                                )
                                existing_bill.category_id = category.id
                            
                            created_bills.append(existing_bill)
                            updated_count += 1  # 统计更新记录数
                            logger.info(f"更新京东账单记录: {record.get('raw_data', {}).get('order_id')}")
                            continue
                    
                    # 其他来源：检查重复
                    else:
                        if check_duplicate_bill_other_sources(record, family_id, source_type, db):
                            logger.info(f"跳过重复记录 (记录 {i+1})")
                            continue
                    
                    # 自动分类
                    category = None
                    if auto_categorize and record.get("category"):
                        category = await get_or_create_category(
                            record["category"], 
                            family_id, 
                            db
                        )
                    
                    # 创建新的账单记录
                    bill = Bill(
                        user_id=current_user.id,
                        family_id=family_id,
                        amount=record["amount"],
                        transaction_time=record["transaction_time"],
                        transaction_type=record["transaction_type"],
                        transaction_desc=record.get("transaction_desc"),
                        source_type=source_type,
                        category_id=category.id if category else None,
                        raw_data=record.get("raw_data", {})
                    )
                    
                    db.add(bill)
                    created_bills.append(bill)
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"创建账单记录失败 (记录 {i+1}): {e}")
                    logger.error(f"问题记录内容: {record}")
                    failed_count += 1
            
            db.commit()
            
            logger.info(f"文件上传完成: {file.filename}, 新增: {success_count}, 更新: {updated_count}, 失败: {failed_count}")
            
            total_records = len(parse_result.success_records) + len(parse_result.failed_records)
            total_failed = failed_count + len(parse_result.failed_records)
            total_success = success_count + updated_count  # 成功数包括新增和更新
            upload_status = "completed" if failed_count == 0 else "partial_success"
            
            # 构建警告信息
            warnings = parse_result.errors.copy() if hasattr(parse_result, 'errors') else []
            if updated_count > 0:
                warnings.append(f"更新已存在记录数: {updated_count}")
            
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
                errors=parse_result.failed_records + [f"保存失败记录数: {failed_count}"] if failed_count > 0 else parse_result.failed_records,
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


@router.get("/history")
async def get_upload_history(
    family_id: Optional[int] = None,
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取上传历史记录"""
    try:
        # 暂时返回空列表，因为UploadRecord模型不存在
        return []
        
    except Exception as e:
        logger.error(f"获取上传历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取上传历史失败"
        )


@router.get("/stats", response_model=UploadStatsResponse)
async def get_upload_stats(
    family_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取上传统计信息"""
    try:
        # 获取用户所属家庭
        user_family_ids = await get_user_families(current_user, db)
        
        # 由于UploadRecord模型不存在，返回基本统计信息
        bills_query = db.query(Bill).filter(
            Bill.family_id.in_(user_family_ids)
        )
        
        if family_id and family_id in user_family_ids:
            bills_query = bills_query.filter(Bill.family_id == family_id)
        
        bills = bills_query.all()
        
        # 统计信息
        total_uploads = 0
        total_records = len(bills)
        total_success = len(bills)
        total_failed = 0
        
        # 按状态统计
        by_status = {"completed": 1} if bills else {}
        
        # 按来源类型统计
        by_source = {}
        for bill in bills:
            source = bill.source_type
            if source not in by_source:
                by_source[source] = {
                    "count": 0,
                    "records": 0,
                    "success": 0,
                    "failed": 0
                }
            by_source[source]["count"] += 1
            by_source[source]["records"] += 1
            by_source[source]["success"] += 1
            by_source[source]["failed"] += 0
        
        return UploadStatsResponse(
            total_uploads=total_uploads,
            total_records=total_records,
            total_success=total_success,
            total_failed=total_failed,
            success_rate=total_success / total_records if total_records > 0 else 0,
            by_status=by_status,
            by_source=by_source
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