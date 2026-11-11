#!/usr/bin/env python3
"""Read-only production DB inventory. Does not print credentials or user records.

Execution is intended ONLY inside an authorized private-network Render runtime.
Requires DATABASE_URL from a secret environment variable. No DDL/DML.
"""
import json
import os
import sys
from sqlalchemy import create_engine, text

SQL = {
    "environment": """SELECT current_database() db, current_setting('server_version') pg_version,
                      pg_database_size(current_database()) database_bytes,
                      pg_is_in_recovery() is_replica""",
    "migrations": """SELECT CASE WHEN to_regclass('public.alembic_version') IS NULL
                         THEN '(missing)' ELSE (SELECT version_num FROM public.alembic_version LIMIT 1)
                         END AS alembic_revision""",
    "tables": """SELECT table_name FROM information_schema.tables
                   WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                   ORDER BY table_name""",
    "schema": """SELECT table_name,column_name,data_type,is_nullable
                   FROM information_schema.columns WHERE table_schema='public'
                   ORDER BY table_name,ordinal_position""",
}
def main():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        print("BLOCKED: DATABASE_URL secret not injected.", file=sys.stderr)
        return 2
    engine = create_engine(dsn, connect_args={"connect_timeout": 8}, pool_pre_ping=True)
    result = {}
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                conn.execute(text("SET TRANSACTION READ ONLY"))
                for key, sql in SQL.items():
                    result[key] = [dict(row) for row in conn.execute(text(sql)).mappings()]
                trans.commit()
            except BaseException:
                trans.rollback()
                raise
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0
    except Exception as exc:
        print(f"BLOCKED: read-only inventory failed ({type(exc).__name__}); no connection string printed.", file=sys.stderr)
        return 3
    finally:
        engine.dispose()

if __name__ == "__main__":
    raise SystemExit(main())
