#!/usr/bin/env python3
"""
数据库迁移脚本：为classification_rules表添加用户隔离机制

修改内容：
1. 将created_by字段设为NOT NULL
2. 添加新的唯一约束：UNIQUE(created_by, rule_text, source_type)
3. 删除旧的唯一约束：UNIQUE(rule_text, source_type)
4. 处理现有的NULL数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config.settings import settings
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """执行数据库迁移"""
    try:
        # 获取数据库连接
        database_url = settings.DATABASE_URL
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                logger.info("开始执行classification_rules表用户隔离迁移...")
                
                # 1. 检查表是否存在
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'classification_rules'
                    );
                """))
                
                if not result.scalar():
                    logger.error("classification_rules表不存在，请先创建表")
                    return False
                
                # 2. 检查是否有created_by为NULL的记录
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM classification_rules WHERE created_by IS NULL;
                """))
                null_count = result.scalar()
                
                if null_count > 0:
                    logger.warning(f"发现 {null_count} 条created_by为NULL的记录")
                    
                    # 选择处理方式：删除这些记录（也可以选择分配给管理员用户）
                    logger.info("删除created_by为NULL的记录...")
                    conn.execute(text("""
                        DELETE FROM classification_rules WHERE created_by IS NULL;
                    """))
                    logger.info(f"已删除 {null_count} 条记录")
                
                # 3. 检查并删除旧的唯一约束
                logger.info("检查现有约束...")
                result = conn.execute(text("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'classification_rules' 
                    AND constraint_type = 'UNIQUE'
                    AND constraint_name LIKE '%rule_text%';
                """))
                
                old_constraints = result.fetchall()
                for constraint in old_constraints:
                    constraint_name = constraint[0]
                    logger.info(f"删除旧约束: {constraint_name}")
                    conn.execute(text(f"""
                        ALTER TABLE classification_rules DROP CONSTRAINT IF EXISTS {constraint_name};
                    """))
                
                # 4. 将created_by字段设为NOT NULL
                logger.info("设置created_by字段为NOT NULL...")
                conn.execute(text("""
                    ALTER TABLE classification_rules 
                    ALTER COLUMN created_by SET NOT NULL;
                """))
                
                # 5. 添加新的唯一约束
                logger.info("添加新的唯一约束...")
                conn.execute(text("""
                    ALTER TABLE classification_rules 
                    ADD CONSTRAINT uq_classification_rules_user_rule_source 
                    UNIQUE (created_by, rule_text, source_type);
                """))
                
                # 6. 验证修改结果
                logger.info("验证修改结果...")
                
                # 检查created_by字段是否为NOT NULL
                result = conn.execute(text("""
                    SELECT is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'classification_rules' 
                    AND column_name = 'created_by';
                """))
                is_nullable = result.scalar()
                
                if is_nullable == 'NO':
                    logger.info("✓ created_by字段已设为NOT NULL")
                else:
                    logger.error("✗ created_by字段设置NOT NULL失败")
                    return False
                
                # 检查新约束是否存在
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'classification_rules' 
                    AND constraint_name = 'uq_classification_rules_user_rule_source';
                """))
                
                if result.scalar() > 0:
                    logger.info("✓ 新的唯一约束已添加")
                else:
                    logger.error("✗ 新的唯一约束添加失败")
                    return False
                
                # 提交事务
                trans.commit()
                logger.info("数据库迁移完成！")
                return True
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                logger.error(f"迁移失败，已回滚: {e}")
                return False
                
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False

def rollback_migration():
    """回滚迁移（如果需要）"""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                logger.info("开始回滚迁移...")
                
                # 删除新约束
                conn.execute(text("""
                    ALTER TABLE classification_rules 
                    DROP CONSTRAINT IF EXISTS uq_classification_rules_user_rule_source;
                """))
                
                # 将created_by字段设为可NULL
                conn.execute(text("""
                    ALTER TABLE classification_rules 
                    ALTER COLUMN created_by DROP NOT NULL;
                """))
                
                # 恢复旧约束（如果需要）
                conn.execute(text("""
                    ALTER TABLE classification_rules 
                    ADD CONSTRAINT uq_classification_rules_rule_source 
                    UNIQUE (rule_text, source_type);
                """))
                
                trans.commit()
                logger.info("回滚完成！")
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"回滚失败: {e}")
                return False
                
    except Exception as e:
        logger.error(f"回滚时数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Classification Rules用户隔离迁移")
    parser.add_argument("--rollback", action="store_true", help="回滚迁移")
    
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback_migration()
    else:
        success = run_migration()
    
    if success:
        logger.info("操作成功完成")
        sys.exit(0)
    else:
        logger.error("操作失败")
        sys.exit(1)