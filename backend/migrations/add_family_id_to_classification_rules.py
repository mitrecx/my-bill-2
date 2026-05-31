#!/usr/bin/env python3
"""为 classification_rules 表添加 family_id，改为家庭级共享"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

from config.settings import settings


def add_family_id_column():
    engine = create_engine(settings.DATABASE_URL)
    migration_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(migration_dir, "add_family_id_to_classification_rules.sql")

    with open(sql_path, "r", encoding="utf-8") as f:
        migration_sql = f.read()

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            result = conn.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'classification_rules'
                      AND column_name = 'family_id'
                    """
                )
            )
            if result.fetchone():
                constraint = conn.execute(
                    text(
                        """
                        SELECT 1 FROM pg_constraint
                        WHERE conname = 'uq_classification_rules_family_rule_source_type'
                        """
                    )
                )
                if constraint.fetchone():
                    print("family_id 迁移已完成，跳过")
                    trans.commit()
                    return

            print("为 classification_rules 添加 family_id 并迁移为家庭级规则...")
            for statement in migration_sql.split(";"):
                stmt = statement.strip()
                if stmt:
                    conn.execute(text(stmt))

            trans.commit()
            print("family_id 迁移成功！")
        except Exception as exc:
            trans.rollback()
            print(f"迁移失败: {exc}")
            raise


if __name__ == "__main__":
    add_family_id_column()
