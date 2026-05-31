"""
AI账单分类服务
使用智谱GLM-4.5模型进行账单智能分类
"""

import json
import logging
from typing import List, Dict, Optional, Tuple
from zai import ZhipuAiClient
from sqlalchemy.orm import Session

from config.settings import settings
from models.bill import BillCategory
from schemas.bills import BillResponse
from models.classification_rule import ClassificationRule

logger = logging.getLogger(__name__)


class AIClassificationService:
    """AI账单分类服务"""
    
    def __init__(self):
        """初始化AI分类服务"""
        self.client = None
        if settings.ZHIPU_API_KEY:
            try:
                self.client = ZhipuAiClient(api_key=settings.ZHIPU_API_KEY)
                logger.info("智谱AI客户端初始化成功")
            except Exception as e:
                logger.error(f"智谱AI客户端初始化失败: {e}")
        else:
            logger.warning("未配置ZHIPU_API_KEY，AI分类功能不可用")
    
    def is_available(self) -> bool:
        """检查AI分类服务是否可用"""
        return self.client is not None
    
    def get_categories_context(self, db: Session) -> str:
        """获取分类上下文信息"""
        try:
            categories = db.query(BillCategory).filter(BillCategory.is_deleted == False).all()
            
            income_categories = []
            expense_categories = []
            
            for category in categories:
                # 包含分类ID和名称，避免歧义
                category_info = f"- {category.category_name} (ID: {category.id})"
                if category.description:
                    category_info += f": {category.description}"
                
                if category.category_type == "income":
                    income_categories.append(category_info)
                else:
                    expense_categories.append(category_info)
            
            context = "可用的账单分类如下：\n\n"
            context += "收入类别：\n" + "\n".join(income_categories) + "\n\n"
            context += "支出类别：\n" + "\n".join(expense_categories)
            
            return context
        except Exception as e:
            logger.error(f"获取分类上下文失败: {e}")
            return "无法获取分类信息"
    
    def get_classification_rules_context(
        self,
        db: Session,
        user_id: int,
        source_type: str = None,
        transaction_type: str = None,
    ) -> str:
        """获取分类规则上下文信息"""
        try:
            from services.classification_rule_service import TRANSACTION_TYPE_LABELS, normalize_transaction_type

            normalized_transaction_type = normalize_transaction_type(transaction_type)

            # 查询当前用户启用的分类规则
            query = db.query(ClassificationRule).filter(
                ClassificationRule.created_by == user_id,
                ClassificationRule.is_active == True
            )
            
            # 如果指定了来源类型，则过滤规则
            if source_type:
                query = query.filter(
                    (ClassificationRule.source_type == source_type) |
                    (ClassificationRule.source_type == 'all')
                )
            else:
                # 如果没有指定来源类型，只获取通用规则
                query = query.filter(ClassificationRule.source_type == 'all')

            if normalized_transaction_type:
                query = query.filter(
                    (ClassificationRule.transaction_type == normalized_transaction_type) |
                    (ClassificationRule.transaction_type == 'all')
                )
            
            # 按优先级排序
            rules = query.order_by(ClassificationRule.priority.desc()).all()
            
            if not rules:
                return ""
            
            context = "\n分类规则（请优先按照以下规则进行分类）：\n"
            
            for rule in rules:
                type_label = TRANSACTION_TYPE_LABELS.get(rule.transaction_type, rule.transaction_type)
                context += (
                    f"- 如果账单描述包含「{rule.rule_text}」"
                    f"（适用类型：{type_label}），则分类为「{rule.target_category}」\n"
                )
            
            context += "\n注意：以上规则具有优先级，请优先匹配高优先级规则。如果没有匹配的规则，再根据账单描述进行智能分类。\n"
            
            return context
            
        except Exception as e:
            logger.error(f"获取分类规则上下文失败: {e}")
            return ""
    

    
    def classify_single_bill(self, bill_data: Dict, db: Session, user_id: int) -> Optional[str]:
        """
        使用AI对单个账单进行分类（包含分类规则）
        
        Args:
            bill_data: 账单数据字典
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            分类名称，如果分类失败则返回None
        """
        if not self.is_available():
            logger.warning("AI分类服务不可用")
            return None
        
        try:
            # 构建分类上下文
            categories_context = self.get_categories_context(db)
            
            # 获取分类规则上下文
            source_type = bill_data.get('source_type')
            transaction_type = bill_data.get('transaction_type')
            rules_context = self.get_classification_rules_context(
                db, user_id, source_type, transaction_type
            )
            
            # 构建账单信息（删除金额字段，因为对AI推理分类没有帮助）
            bill_info = f"""账单信息：
- 账单ID: {bill_data.get('id', '未知')}
- 交易类型: {bill_data.get('transaction_type', '未知')}
- 描述: {bill_data.get('description', '无描述')}"""
            
            # 构建提示词（包含分类规则）
            prompt = f"""你是一个专业的账单分类助手。请根据账单信息为账单选择最合适的分类。

{categories_context}{rules_context}

分类指导：
1. **优先级顺序**：首先检查是否匹配分类规则，如果匹配则按规则分类；如果不匹配任何规则，再根据账单描述进行智能分类
2. **交易类型匹配**：根据交易类型选择对应类别
   - 不能混淆收入和支出类别
   - 交易类型为"收入"的账单，必须从收入类别中选择分类
   - 交易类型为"支出"的账单，必须从支出类别中选择分类
   - 交易类型为"不计收支"的账单，分类可以选择支出或收入，根据账单描述判断
3. **关键词分析**：仔细分析账单描述中的关键词
4. **最佳匹配**：选择最具体、最相关的分类

示例输入：
- 账单ID: 11244
- 交易类型: 支出
- 描述: 打车费用-滴滴出行

示例输出：
11244: 12

{bill_info}

请按以下格式返回账单的分类结果：
账单ID: 分类ID

请严格按照上述格式返回，只返回分类ID（数字），分类ID必须从上述分类列表中选择："""

            # 记录发送给AI的提示词
            logger.info(f"单个分类提示词: {prompt}")
            
            # 调用GLM-4.5模型
            response = self.client.chat.completions.create(
                model="glm-4.5",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 降低随机性，提高一致性
                max_tokens=100,   # 适当增加输出长度限制以支持格式化输出
                thinking={"type": "disabled"}  # 禁用深度思考模式
            )
            
            # 记录AI的原始响应
            logger.info(f"AI单个分类原始响应: {response}")
            
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content.strip()
                logger.info(f"AI单个分类内容: {content}")
                
                # 解析AI响应，支持多种格式
                try:
                    # 获取所有可用的分类，创建ID到名称的映射
                    all_categories = db.query(BillCategory).filter(BillCategory.is_deleted == False).all()
                    category_id_to_name = {cat.id: cat.category_name for cat in all_categories}
                    
                    # 尝试从响应中提取分类ID
                    category_id = None
                    
                    # 处理多行响应，查找包含"分类ID"的行
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if '分类ID:' in line:
                            # 处理格式：分类ID: 11
                            parts = line.split('分类ID:', 1)
                            if len(parts) == 2:
                                category_id_str = parts[1].strip()
                                try:
                                    category_id = int(category_id_str)
                                    break
                                except ValueError:
                                    continue
                        elif line and ':' in line and not line.startswith('账单ID:'):
                            # 处理简单格式：账单ID: 分类ID
                            parts = line.split(':', 1)
                            if len(parts) == 2:
                                category_id_str = parts[1].strip()
                                try:
                                    category_id = int(category_id_str)
                                    break
                                except ValueError:
                                    continue
                    
                    # 如果还没找到，尝试从整个内容中提取数字
                    if category_id is None:
                        import re
                        # 查找最后一个数字作为分类ID
                        numbers = re.findall(r'\d+', content)
                        if numbers:
                            try:
                                category_id = int(numbers[-1])
                            except ValueError:
                                pass
                    
                    if category_id is not None:
                        # 根据分类ID获取分类名称
                        category_name = category_id_to_name.get(category_id)
                        
                        if category_name:
                            logger.info(f"解析成功: 分类ID {category_id} ({category_name})")
                            return category_name
                        else:
                            logger.warning(f"无效分类ID: {category_id}")
                            return None
                    else:
                        logger.warning(f"无法从响应中提取分类ID: {content}")
                        return None
                        
                except Exception as e:
                    logger.warning(f"解析响应失败: {content}, 错误: {e}")
                    return None
                else:
                    logger.warning(f"AI响应格式不正确: {content}")
                    return None
            else:
                logger.warning("AI未返回有效的分类结果")
                return None
                
        except Exception as e:
            logger.error(f"AI分类失败: {e}")
            return None
    

    
    def classify_bills_batch_optimized(self, bills_data: List[Dict], db: Session, user_id: int, batch_size: int = 20) -> List[Tuple[int, Optional[str]]]:
        """
        优化的批量分类账单（使用AI分类，包含分类规则）
        
        Args:
            bills_data: 账单数据列表
            db: 数据库会话
            user_id: 用户ID
            batch_size: 每批处理的账单数量，默认20个
            
        Returns:
            [(bill_id, category_name), ...] 分类结果列表
        """
        results = []
        
        if not self.is_available():
            logger.warning("AI分类服务不可用")
            return [(bill.get('id'), None) for bill in bills_data]
        
        # 分批处理AI分类
        for i in range(0, len(bills_data), batch_size):
            batch = bills_data[i:i + batch_size]
            batch_results = self._classify_bills_batch_single_request(batch, db, user_id)
            results.extend(batch_results)
        
        return results
    
    def _classify_bills_batch_single_request(self, bills_batch: List[Dict], db: Session, user_id: int) -> List[Tuple[int, Optional[str]]]:
        """
        单次请求批量分类账单
        
        Args:
            bills_batch: 账单数据批次（最多20个）
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            [(bill_id, category_name), ...] 分类结果列表
        """
        try:
            # 构建分类上下文
            categories_context = self.get_categories_context(db)
            
            # 获取分类规则上下文（匹配批次内任一账单的来源与交易类型）
            from services.classification_rule_service import (
                TRANSACTION_TYPE_LABELS,
                normalize_transaction_type,
            )

            source_types = {
                bill.get('source_type')
                for bill in bills_batch
                if bill.get('source_type')
            }
            transaction_types = {
                normalize_transaction_type(bill.get('transaction_type'))
                for bill in bills_batch
                if normalize_transaction_type(bill.get('transaction_type'))
            }

            rules_query = db.query(ClassificationRule).filter(
                ClassificationRule.created_by == user_id,
                ClassificationRule.is_active == True,
            )
            if source_types:
                rules_query = rules_query.filter(
                    ClassificationRule.source_type.in_(source_types)
                    | (ClassificationRule.source_type == 'all')
                )
            else:
                rules_query = rules_query.filter(ClassificationRule.source_type == 'all')

            if transaction_types:
                rules_query = rules_query.filter(
                    ClassificationRule.transaction_type.in_(transaction_types)
                    | (ClassificationRule.transaction_type == 'all')
                )

            rules = rules_query.order_by(ClassificationRule.priority.desc()).all()
            if rules:
                rules_context = "\n分类规则（请优先按照以下规则进行分类）：\n"
                for rule in rules:
                    type_label = TRANSACTION_TYPE_LABELS.get(
                        rule.transaction_type, rule.transaction_type
                    )
                    rules_context += (
                        f"- 如果账单描述包含「{rule.rule_text}」"
                        f"（适用类型：{type_label}），则分类为「{rule.target_category}」\n"
                    )
                rules_context += (
                    "\n注意：以上规则具有优先级，请优先匹配高优先级规则。"
                    "如果没有匹配的规则，再根据账单描述进行智能分类。\n"
                )
            else:
                rules_context = self.get_classification_rules_context(db, user_id)
            
            # 构建批量账单信息（删除金额字段和来源字段）
            bills_info = "账单列表：\n"
            for i, bill_data in enumerate(bills_batch, 1):
                bills_info += f"""
{i}. 账单ID: {bill_data.get('id', '未知')}
   - 交易类型: {bill_data.get('transaction_type', '未知')}
   - 描述: {bill_data.get('description', '无描述')}
"""
            
            # 构建提示词（包含分类规则）
            prompt = f"""你是一个专业的账单分类助手。请根据账单信息为每个账单选择最合适的分类。

{categories_context}{rules_context}

分类指导：
1. **优先级顺序**：首先检查是否匹配分类规则，如果匹配则按规则分类；如果不匹配任何规则，再根据账单描述进行智能分类
2. **交易类型匹配**：根据交易类型选择对应类别
   - 不能混淆收入和支出类别
   - 交易类型为"收入"的账单，必须从收入类别中选择分类
   - 交易类型为"支出"的账单，必须从支出类别中选择分类
   - 交易类型为"不计收支"的账单，分类可以选择支出或收入，根据账单描述判断
3. **关键词分析**：仔细分析账单描述中的关键词
4. **最佳匹配**：选择最具体、最相关的分类

示例输入：
1. 账单ID: 11244
   - 交易类型: 支出
   - 描述: 打车费用-滴滴出行

2. 账单ID: 11245
   - 交易类型: 支出
   - 描述: 挂号费

3. 账单ID: 11246
   - 交易类型: 收入
   - 描述: 基金赎回

示例输出：
11244: 12
11245: 14
11246: 2

{bills_info}

请按以下格式返回每个账单的分类结果，每行一个账单：
账单ID: 分类ID

请严格按照上述格式返回，只返回分类ID（数字），分类ID必须从上述分类列表中选择："""

            # 记录发送给AI的提示词
            logger.info(f"批量分类提示词: {prompt}")
            
            # 调用GLM-4.5模型
            response = self.client.chat.completions.create(
                model="glm-4.5",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 降低随机性，提高一致性
                max_tokens=500,   # 增加输出长度限制以支持多个账单
                thinking={"type": "disabled"}  # 禁用深度思考模式
            )
            
            # 记录AI的原始响应
            logger.info(f"AI批量分类原始响应: {response}")
            
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content.strip()
                logger.info(f"AI批量分类内容: {content}")
                
                # 解析AI返回的分类结果
                results = self._parse_batch_classification_result(content, bills_batch, db, user_id)
                return results
            else:
                logger.warning("AI未返回有效的批量分类结果")
                return [(bill.get('id'), None) for bill in bills_batch]
                
        except Exception as e:
            logger.error(f"批量AI分类失败: {e}")
            return [(bill.get('id'), None) for bill in bills_batch]
    
    def _parse_batch_classification_result(self, ai_response: str, bills_batch: List[Dict], db: Session, user_id: int) -> List[Tuple[int, Optional[str]]]:
        """
        解析AI批量分类结果
        
        Args:
            ai_response: AI返回的文本
            bills_batch: 账单数据批次
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            [(bill_id, category_name), ...] 分类结果列表
        """
        results = []
        
        # 获取所有可用的分类，创建ID到名称的映射
        all_categories = db.query(BillCategory).filter(BillCategory.is_deleted == False).all()
        category_id_to_name = {cat.id: cat.category_name for cat in all_categories}
        
        # 创建账单ID到账单数据的映射
        bill_id_map = {bill.get('id'): bill for bill in bills_batch}
        
        # 解析AI响应
        lines = ai_response.strip().split('\n')
        parsed_results = {}
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                try:
                    # 解析格式：账单ID: xxx: yyy 或 xxx: yyy
                    if line.startswith('账单ID:'):
                        # 处理格式：账单ID: 13082: 2
                        parts = line.split(':', 2)  # 最多分割成3部分
                        if len(parts) >= 3:
                            bill_id_str = parts[1].strip()
                            category_id_str = parts[2].strip()
                        else:
                            continue
                    else:
                        # 处理格式：13082: 2
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            bill_id_str = parts[0].strip()
                            category_id_str = parts[1].strip()
                        else:
                            continue
                    
                    # 转换账单ID和分类ID为整数
                    try:
                        bill_id = int(bill_id_str)
                        category_id = int(category_id_str)
                        
                        # 根据分类ID获取分类名称
                        category_name = category_id_to_name.get(category_id)
                        
                        if category_name:
                            parsed_results[bill_id] = category_name
                            logger.info(f"解析成功: 账单{bill_id} -> 分类ID {category_id} ({category_name})")
                        else:
                            logger.warning(f"无效分类ID: {category_id}")
                            parsed_results[bill_id] = None
                    except ValueError:
                        logger.warning(f"无效的ID格式: 账单ID={bill_id_str}, 分类ID={category_id_str}")
                except Exception as e:
                    logger.warning(f"解析行失败: {line}, 错误: {e}")
        
        # 为每个账单生成结果
        for bill in bills_batch:
            bill_id = bill.get('id')
            category_name = parsed_results.get(bill_id)
            
            # 如果AI没有返回该账单的分类，尝试使用单个分类方法作为后备
            if category_name is None:
                logger.warning(f"账单{bill_id}未在AI响应中找到分类，使用单个分类方法作为后备")
                category_name = self.classify_single_bill(bill, db, user_id)
            
            results.append((bill_id, category_name))
        
        return results
    
    def suggest_classification_rule(self, bill_data: Dict, category_name: str, db: Session) -> Optional[str]:
        """
        基于分类结果建议分类规则
        
        Args:
            bill_data: 账单数据
            category_name: 分类名称
            db: 数据库会话
            
        Returns:
            建议的分类规则文本
        """
        if not self.is_available():
            return None
        
        try:
            # 构建提示词（删除金额字段，因为对AI推理分类没有帮助）
            prompt = f"""基于以下账单信息和分类结果，请生成一个简洁的分类规则：

账单信息：
- 交易类型: {bill_data.get('transaction_type', '未知')}
- 描述: {bill_data.get('description', '无描述')}
- 来源: {bill_data.get('source_type', '未知')}

分类结果: {category_name}

请生成一个简洁的分类规则，用于自动识别类似的账单。规则应该：
1. 基于账单描述中的关键词
2. 简洁明了，易于理解
3. 具有一定的通用性

分类规则："""

            response = self.client.chat.completions.create(
                model="glm-4.5",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100,
                thinking={"type": "disabled"}  # 禁用深度思考模式
            )
            
            if response.choices and response.choices[0].message:
                rule_text = response.choices[0].message.content.strip()
                logger.info(f"建议的分类规则: {rule_text}")
                return rule_text
            
        except Exception as e:
            logger.error(f"生成分类规则建议失败: {e}")
            return None
        
        return None
    
    def analyze_classification_accuracy(self, bills_data: List[Dict], db: Session, user_id: int) -> Dict:
        """
        分析分类准确性
        
        Args:
            bills_data: 已分类的账单数据
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            分析结果字典
        """
        if not self.is_available():
            return {"error": "AI分类服务不可用"}
        
        try:
            total_bills = len(bills_data)
            ai_classified = 0
            accuracy_issues = []
            
            for bill_data in bills_data:
                # 获取当前分类
                current_category = bill_data.get('category_name')
                
                # AI重新分类
                ai_category = self.classify_single_bill(bill_data, db, user_id)
                
                if ai_category:
                    ai_classified += 1
                    
                    # 检查分类是否一致
                    if current_category and current_category != ai_category:
                        accuracy_issues.append({
                            'bill_id': bill_data.get('id'),
                            'description': bill_data.get('description'),
                            'current_category': current_category,
                            'ai_suggested_category': ai_category
                        })
            
            return {
                'total_bills': total_bills,
                'ai_classified_count': ai_classified,
                'ai_classification_rate': ai_classified / total_bills if total_bills > 0 else 0,
                'accuracy_issues_count': len(accuracy_issues),
                'accuracy_issues': accuracy_issues[:10]  # 只返回前10个问题
            }
            
        except Exception as e:
            logger.error(f"分析分类准确性失败: {e}")
            return {"error": str(e)}


# 全局AI分类服务实例
ai_classification_service = AIClassificationService()