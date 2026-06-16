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
    with db_cursor(commit=True) as cursor:
        _run_migration(cursor, "001_create_agent_mgmt_tables.sql")
        _run_migration(cursor, "008_panorama_tables.sql")
        _ensure_column(cursor, "agent_mgmt_agent", "active_version", "VARCHAR(40) DEFAULT NULL AFTER `version`")
        _ensure_column(cursor, "agent_mgmt_agent", "active_content", "MEDIUMTEXT DEFAULT NULL AFTER `active_version`")
        _ensure_column(cursor, "agent_mgmt_agent", "active_tags", "VARCHAR(500) DEFAULT NULL AFTER `active_content`")
        _ensure_column(cursor, "agent_mgmt_agent_version", "tags", "VARCHAR(500) DEFAULT NULL AFTER `content`")
        _ensure_column(cursor, "agent_mgmt_agent_version", "is_active", "TINYINT(1) NOT NULL DEFAULT 0 AFTER `created_at`")
        _ensure_column(cursor, "agent_mgmt_agent_version", "activated_by_user_id", "BIGINT(20) DEFAULT NULL AFTER `is_active`")
        _ensure_column(cursor, "agent_mgmt_agent_version", "activated_by_username", "VARCHAR(100) DEFAULT NULL AFTER `activated_by_user_id`")
        _ensure_column(cursor, "agent_mgmt_agent_version", "activated_at", "DATETIME DEFAULT NULL AFTER `activated_by_username`")
        _ensure_column(cursor, "agent_mgmt_scenario_version", "description", "TEXT DEFAULT NULL AFTER `content`")
        _ensure_column(cursor, "agent_mgmt_scenario_version", "sub_type_hint", "VARCHAR(500) DEFAULT NULL AFTER `description`")
        _ensure_column(cursor, "agent_mgmt_scenario_version", "keyword_hint", "VARCHAR(500) DEFAULT NULL AFTER `sub_type_hint`")
        _ensure_column(cursor, "agent_mgmt_scenario_version", "skill_selector_dims", "VARCHAR(500) DEFAULT NULL AFTER `keyword_hint`")
        _ensure_column(cursor, "agent_mgmt_scenario_version", "related_agents", "TEXT DEFAULT NULL AFTER `skill_selector_dims`")
        _backfill_agent_active_versions(cursor)


def _run_migration(cursor, filename):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS `agent_mgmt_schema_migration` (
          `filename` VARCHAR(191) NOT NULL,
          `executed_at` DATETIME NOT NULL,
          PRIMARY KEY (`filename`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent management schema migrations'
        """
    )
    cursor.execute(
        "SELECT `filename` FROM `agent_mgmt_schema_migration` WHERE `filename` = %s",
        (filename,),
    )
    if cursor.fetchone():
        return

    migration = Path(__file__).resolve().parents[2] / "migrations" / filename
    statements = [part.strip() for part in migration.read_text(encoding="utf-8-sig").split(";") if part.strip()]
    for statement in statements:
        cursor.execute(statement)
    cursor.execute(
        "INSERT INTO `agent_mgmt_schema_migration` (`filename`, `executed_at`) VALUES (%s, NOW())",
        (filename,),
    )


def _ensure_column(cursor, table, column, ddl):
    cursor.execute(f"SHOW COLUMNS FROM `{table}` LIKE %s", (column,))
    if cursor.fetchone():
        return
    cursor.execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {ddl}")


def _backfill_agent_active_versions(cursor):
    cursor.execute(
        """
        UPDATE `agent_mgmt_agent`
           SET active_version = version,
               active_content = content,
               active_tags = tags
         WHERE active_version IS NULL
        """
    )
    cursor.execute(
        """
        INSERT INTO `agent_mgmt_agent_version`
          (agent_id, version, content, tags, created_by_user_id, created_by_username,
           created_at, is_active, activated_by_user_id, activated_by_username, activated_at)
        SELECT a.id, a.active_version, a.active_content, a.active_tags,
               a.updated_by_user_id, a.updated_by_username, a.updated_at,
               1, a.updated_by_user_id, a.updated_by_username, a.updated_at
          FROM `agent_mgmt_agent` a
         WHERE a.active_version IS NOT NULL
           AND NOT EXISTS (
             SELECT 1
               FROM `agent_mgmt_agent_version` v
              WHERE v.agent_id = a.id
                AND v.version = a.active_version
           )
        """
    )
    cursor.execute(
        """
        UPDATE `agent_mgmt_agent_version` v
        JOIN `agent_mgmt_agent` a
          ON a.id = v.agent_id
         AND a.active_version = v.version
           SET v.is_active = 1
         WHERE v.is_active = 0
        """
    )
