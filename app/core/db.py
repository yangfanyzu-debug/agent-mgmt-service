from contextlib import contextmanager
from pathlib import Path

import pymysql
from pymysql.cursors import DictCursor

from app.core.config import settings


def connect():
    return pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        charset=settings.db_charset,
        cursorclass=DictCursor,
        autocommit=False,
    )


@contextmanager
def db_cursor(commit=False):
    conn = connect()
    try:
        with conn.cursor() as cursor:
            yield cursor
        if commit:
            conn.commit()
        else:
            conn.rollback()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema():
    migration = Path(__file__).resolve().parents[2] / "migrations" / "001_create_agent_mgmt_tables.sql"
    statements = [part.strip() for part in migration.read_text(encoding="utf-8").split(";") if part.strip()]
    with db_cursor(commit=True) as cursor:
        for statement in statements:
            cursor.execute(statement)
        _ensure_column(cursor, "agent_mgmt_agent_version", "tags", "VARCHAR(500) DEFAULT NULL AFTER `content`")
        _ensure_column(cursor, "agent_mgmt_scenario_version", "description", "TEXT DEFAULT NULL AFTER `content`")
        _ensure_column(cursor, "agent_mgmt_scenario_version", "sub_type_hint", "VARCHAR(500) DEFAULT NULL AFTER `description`")
        _ensure_column(cursor, "agent_mgmt_scenario_version", "keyword_hint", "VARCHAR(500) DEFAULT NULL AFTER `sub_type_hint`")
        _ensure_column(cursor, "agent_mgmt_scenario_version", "skill_selector_dims", "VARCHAR(500) DEFAULT NULL AFTER `keyword_hint`")
        _ensure_column(cursor, "agent_mgmt_scenario_version", "related_agents", "TEXT DEFAULT NULL AFTER `skill_selector_dims`")


def _ensure_column(cursor, table, column, ddl):
    cursor.execute(f"SHOW COLUMNS FROM `{table}` LIKE %s", (column,))
    if cursor.fetchone():
        return
    cursor.execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {ddl}")
