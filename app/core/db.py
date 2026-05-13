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
