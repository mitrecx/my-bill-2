#!/usr/bin/env python3
"""为 classification_rules 表添加 transaction_type 字段"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

from config.settings import settings


def add_transaction_type_column():
    engine = create_engine(settings.DATABASE_URL)
    migration_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(migration_dir, "add_transaction_type_to_classification_rules.sql")

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
                      AND column_name = 'transaction_type'
                    """
                )
            )
            if result.fetchone():
                print("transaction_type 字段已存在，跳过迁移")
                trans.commit()
                return

            print("为 classification_rules 表添加 transaction_type 字段...")
            for statement in migration_sql.split(";"):
                stmt = statement.strip()
                if stmt:
                    conn.execute(text(stmt))

            trans.commit()
            print("transaction_type 字段添加成功！")
        except Exception as exc:
            trans.rollback()
            print(f"迁移失败: {exc}")
            raise


if __name__ == "__main__":
    add_transaction_type_column()
