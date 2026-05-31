#!/usr/bin/env python3
"""移除分类规则 transaction_type 的 all 选项"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

from config.settings import settings


def remove_all_transaction_type():
    engine = create_engine(settings.DATABASE_URL)
    migration_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(migration_dir, "remove_all_from_classification_rule_transaction_type.sql")

    with open(sql_path, "r", encoding="utf-8") as f:
        migration_sql = f.read()

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            result = conn.execute(
                text(
                    """
                    SELECT pg_get_constraintdef(oid) AS constraint_def
                    FROM pg_constraint
                    WHERE conname = 'check_classification_rule_transaction_type'
                    """
                )
            )
            row = result.fetchone()
            if row and "'all'" not in row.constraint_def:
                print("transaction_type 约束已不含 all，跳过迁移")
                trans.commit()
                return

            print("移除 classification_rules.transaction_type 的 all 选项...")
            for statement in migration_sql.split(";"):
                stmt = statement.strip()
                if stmt:
                    conn.execute(text(stmt))

            trans.commit()
            print("迁移完成！")
        except Exception as exc:
            trans.rollback()
            print(f"迁移失败: {exc}")
            raise


if __name__ == "__main__":
    remove_all_transaction_type()
