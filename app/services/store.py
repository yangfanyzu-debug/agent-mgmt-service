from datetime import datetime
import json
from typing import Any, Dict, Optional, Tuple

import yaml

from app.core.db import db_cursor
from app.core.security import CurrentUser
from app.services.permissions import add_can_edit, ensure_can_edit


AGENT_TABLE = "agent_mgmt_agent"
AGENT_VERSION_TABLE = "agent_mgmt_agent_version"
SCENARIO_TABLE = "agent_mgmt_scenario"
SCENARIO_VERSION_TABLE = "agent_mgmt_scenario_version"
LOG_TABLE = "agent_mgmt_execution_log"


def _now() -> datetime:
    return datetime.now()


def _next_version(current: str) -> str:
    major = 1
    if current and current.startswith("v"):
        prefix = current[1:].split(".", 1)[0]
        if prefix.isdigit():
            major = int(prefix) + 1
    return f"v{major}.{datetime.now().strftime('%Y%m%d%H%M%S')}"


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _scenario_yaml(data):
    related = data.get("related_agents") or {}
    payload = {
        data["scenario_name"]: {
            "description": data.get("description") or "",
            "sub_type_hint": data.get("sub_type_hint") or "",
            "keyword_hint": data.get("keyword_hint") or "",
            "skill_selector_dims": _json_loads(data.get("skill_selector_dims"), []),
            "planner": related.get("planner"),
            "experts": [
                item.get("name")
                for item in related.get("experts", [])
                if item.get("enabled", True)
            ],
        }
    }
    return yaml.dump(payload, allow_unicode=True, default_flow_style=False)


def _select_one(cursor, sql, params=()):
    cursor.execute(sql, params)
    return cursor.fetchone()


def check_name(table, column, name):
    with db_cursor() as cursor:
        row = _select_one(cursor, f"SELECT id FROM {table} WHERE {column}=%s", (name,))
    return row is None


def list_agents(user, scope, status, agent_type):
    where = []
    params = []
    if scope == "mine":
        where.append("created_by_user_id=%s")
        params.append(user.user_id)
    if status:
        where.append("status=%s")
        params.append(status)
    if agent_type:
        where.append("type=%s")
        params.append(agent_type)
    clause = " WHERE " + " AND ".join(where) if where else ""
    with db_cursor() as cursor:
        cursor.execute(f"SELECT * FROM {AGENT_TABLE}{clause} ORDER BY updated_at DESC", tuple(params))
        rows = cursor.fetchall()
    return add_can_edit(rows, user.user_id)


def get_agent(agent_id, user):
    with db_cursor() as cursor:
        row = _select_one(cursor, f"SELECT * FROM {AGENT_TABLE} WHERE id=%s", (agent_id,))
    if row:
        row["can_edit"] = int(row["created_by_user_id"]) == int(user.user_id)
    return row


def create_agent(req, user):
    now = _now()
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            f"""
            INSERT INTO {AGENT_TABLE}
              (agent_name, type, content, status, tags, version,
               created_by_user_id, created_by_username, updated_by_user_id, updated_by_username,
               created_at, updated_at)
            VALUES (%s,%s,%s,'draft',%s,'v1',%s,%s,%s,%s,%s,%s)
            """,
            (
                req.agent_name,
                req.type,
                req.content,
                req.tags,
                user.user_id,
                user.username,
                user.user_id,
                user.username,
                now,
                now,
            ),
        )
        new_id = cursor.lastrowid
    return get_agent(new_id, user)


def update_agent(agent_id, req, user):
    now = _now()
    with db_cursor(commit=True) as cursor:
        row = _select_one(cursor, f"SELECT * FROM {AGENT_TABLE} WHERE id=%s", (agent_id,))
        if not row:
            return None
        ensure_can_edit(row, user.user_id)
        cursor.execute(
            f"""
            INSERT INTO {AGENT_VERSION_TABLE}
              (agent_id, version, content, created_by_user_id, created_by_username, created_at)
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (agent_id, row["version"], row["content"], user.user_id, user.username, now),
        )
        cursor.execute(
            f"""
            UPDATE {AGENT_TABLE}
               SET content=%s,tags=%s,version=%s,updated_by_user_id=%s,
                   updated_by_username=%s,updated_at=%s
             WHERE id=%s
            """,
            (req.content, req.tags, _next_version(row["version"]), user.user_id, user.username, now, agent_id),
        )
    return get_agent(agent_id, user)


def set_agent_status(agent_id, status, user):
    now = _now()
    with db_cursor(commit=True) as cursor:
        row = _select_one(cursor, f"SELECT * FROM {AGENT_TABLE} WHERE id=%s", (agent_id,))
        if not row:
            return None, []
        ensure_can_edit(row, user.user_id)
        blocked = []
        if status == "inactive":
            cursor.execute(f"SELECT scenario_name, related_agents FROM {SCENARIO_TABLE} WHERE status='active'")
            for scenario in cursor.fetchall():
                related = _json_loads(scenario["related_agents"], {})
                names = [related.get("planner")] + [x.get("name") for x in related.get("experts", [])]
                if row["agent_name"] in names:
                    blocked.append(scenario["scenario_name"])
            if blocked:
                return row, blocked
        cursor.execute(
            f"""
            UPDATE {AGENT_TABLE}
               SET status=%s,updated_by_user_id=%s,updated_by_username=%s,updated_at=%s
             WHERE id=%s
            """,
            (status, user.user_id, user.username, now, agent_id),
        )
    return get_agent(agent_id, user), []


def delete_agent(agent_id, user):
    with db_cursor(commit=True) as cursor:
        row = _select_one(cursor, f"SELECT * FROM {AGENT_TABLE} WHERE id=%s", (agent_id,))
        if not row:
            return None
        ensure_can_edit(row, user.user_id)
        if row["status"] == "active":
            return False
        cursor.execute(f"DELETE FROM {AGENT_VERSION_TABLE} WHERE agent_id=%s", (agent_id,))
        cursor.execute(f"DELETE FROM {AGENT_TABLE} WHERE id=%s", (agent_id,))
    return True


def list_agent_versions(agent_id):
    with db_cursor() as cursor:
        cursor.execute(f"SELECT * FROM {AGENT_VERSION_TABLE} WHERE agent_id=%s ORDER BY id DESC", (agent_id,))
        return cursor.fetchall()


def rollback_agent(agent_id, version_id, user):
    now = _now()
    with db_cursor(commit=True) as cursor:
        row = _select_one(cursor, f"SELECT * FROM {AGENT_TABLE} WHERE id=%s", (agent_id,))
        version = _select_one(cursor, f"SELECT * FROM {AGENT_VERSION_TABLE} WHERE id=%s AND agent_id=%s", (version_id, agent_id))
        if not row or not version:
            return None
        ensure_can_edit(row, user.user_id)
        cursor.execute(
            f"INSERT INTO {AGENT_VERSION_TABLE} (agent_id,version,content,created_by_user_id,created_by_username,created_at) VALUES (%s,%s,%s,%s,%s,%s)",
            (agent_id, row["version"], row["content"], user.user_id, user.username, now),
        )
        cursor.execute(
            f"UPDATE {AGENT_TABLE} SET content=%s,version=%s,updated_by_user_id=%s,updated_by_username=%s,updated_at=%s WHERE id=%s",
            (version["content"], _next_version(row["version"]), user.user_id, user.username, now, agent_id),
        )
    return get_agent(agent_id, user)


def list_scenarios(user, scope, status):
    where = []
    params = []
    if scope == "mine":
        where.append("created_by_user_id=%s")
        params.append(user.user_id)
    if status:
        where.append("status=%s")
        params.append(status)
    clause = " WHERE " + " AND ".join(where) if where else ""
    with db_cursor() as cursor:
        cursor.execute(f"SELECT * FROM {SCENARIO_TABLE}{clause} ORDER BY updated_at DESC", tuple(params))
        rows = cursor.fetchall()
    return add_can_edit(rows, user.user_id)


def get_scenario(scenario_id, user):
    with db_cursor() as cursor:
        row = _select_one(cursor, f"SELECT * FROM {SCENARIO_TABLE} WHERE id=%s", (scenario_id,))
    if row:
        row["can_edit"] = int(row["created_by_user_id"]) == int(user.user_id)
    return row


def create_scenario(req, user):
    now = _now()
    skill_dims = _json_text(req.skill_selector_dims or [])
    related = _json_text(req.related_agents)
    content = _scenario_yaml({
        "scenario_name": req.scenario_name,
        "description": req.description,
        "sub_type_hint": req.sub_type_hint,
        "keyword_hint": req.keyword_hint,
        "skill_selector_dims": skill_dims,
        "related_agents": req.related_agents,
    })
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            f"""
            INSERT INTO {SCENARIO_TABLE}
              (scenario_name,description,sub_type_hint,keyword_hint,skill_selector_dims,related_agents,
               content,status,version,created_by_user_id,created_by_username,updated_by_user_id,
               updated_by_username,created_at,updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,'draft','v1',%s,%s,%s,%s,%s,%s)
            """,
            (
                req.scenario_name,
                req.description,
                req.sub_type_hint,
                req.keyword_hint,
                skill_dims,
                related,
                content,
                user.user_id,
                user.username,
                user.user_id,
                user.username,
                now,
                now,
            ),
        )
        new_id = cursor.lastrowid
    return get_scenario(new_id, user)


def update_scenario(scenario_id, req, user):
    now = _now()
    with db_cursor(commit=True) as cursor:
        row = _select_one(cursor, f"SELECT * FROM {SCENARIO_TABLE} WHERE id=%s", (scenario_id,))
        if not row:
            return None
        ensure_can_edit(row, user.user_id)
        current = dict(row)
        if req.description is not None:
            current["description"] = req.description
        if req.sub_type_hint is not None:
            current["sub_type_hint"] = req.sub_type_hint
        if req.keyword_hint is not None:
            current["keyword_hint"] = req.keyword_hint
        if req.skill_selector_dims is not None:
            current["skill_selector_dims"] = _json_text(req.skill_selector_dims)
        if req.related_agents is not None:
            current["related_agents"] = _json_text(req.related_agents)
        content = _scenario_yaml({**current, "related_agents": _json_loads(current["related_agents"], {})})
        cursor.execute(
            f"INSERT INTO {SCENARIO_VERSION_TABLE} (scenario_id,version,content,created_by_user_id,created_by_username,created_at) VALUES (%s,%s,%s,%s,%s,%s)",
            (scenario_id, row["version"], row.get("content") or "", user.user_id, user.username, now),
        )
        cursor.execute(
            f"""
            UPDATE {SCENARIO_TABLE}
               SET description=%s,sub_type_hint=%s,keyword_hint=%s,skill_selector_dims=%s,
                   related_agents=%s,content=%s,version=%s,updated_by_user_id=%s,
                   updated_by_username=%s,updated_at=%s
             WHERE id=%s
            """,
            (
                current.get("description"),
                current.get("sub_type_hint"),
                current.get("keyword_hint"),
                current.get("skill_selector_dims"),
                current.get("related_agents"),
                content,
                _next_version(row["version"]),
                user.user_id,
                user.username,
                now,
                scenario_id,
            ),
        )
    return get_scenario(scenario_id, user)


def set_scenario_status(scenario_id, status, user):
    now = _now()
    with db_cursor(commit=True) as cursor:
        row = _select_one(cursor, f"SELECT * FROM {SCENARIO_TABLE} WHERE id=%s", (scenario_id,))
        if not row:
            return None, []
        ensure_can_edit(row, user.user_id)
        not_ready = []
        if status == "active":
            related = _json_loads(row["related_agents"], {})
            names = [related.get("planner")] + [x.get("name") for x in related.get("experts", []) if x.get("enabled", True)]
            names = [name for name in names if name]
            if names:
                placeholders = ",".join(["%s"] * len(names))
                cursor.execute(f"SELECT agent_name,status FROM {AGENT_TABLE} WHERE agent_name IN ({placeholders})", tuple(names))
                status_by_name = {item["agent_name"]: item["status"] for item in cursor.fetchall()}
                not_ready = [name for name in names if status_by_name.get(name) != "active"]
            if not_ready:
                return row, not_ready
        cursor.execute(
            f"UPDATE {SCENARIO_TABLE} SET status=%s,updated_by_user_id=%s,updated_by_username=%s,updated_at=%s WHERE id=%s",
            (status, user.user_id, user.username, now, scenario_id),
        )
    return get_scenario(scenario_id, user), []


def delete_scenario(scenario_id, user):
    with db_cursor(commit=True) as cursor:
        row = _select_one(cursor, f"SELECT * FROM {SCENARIO_TABLE} WHERE id=%s", (scenario_id,))
        if not row:
            return None
        ensure_can_edit(row, user.user_id)
        if row["status"] == "active":
            return False
        cursor.execute(f"DELETE FROM {SCENARIO_VERSION_TABLE} WHERE scenario_id=%s", (scenario_id,))
        cursor.execute(f"DELETE FROM {SCENARIO_TABLE} WHERE id=%s", (scenario_id,))
    return True


def list_scenario_versions(scenario_id):
    with db_cursor() as cursor:
        cursor.execute(f"SELECT * FROM {SCENARIO_VERSION_TABLE} WHERE scenario_id=%s ORDER BY id DESC", (scenario_id,))
        return cursor.fetchall()


def rollback_scenario(scenario_id, version_id, user):
    now = _now()
    with db_cursor(commit=True) as cursor:
        row = _select_one(cursor, f"SELECT * FROM {SCENARIO_TABLE} WHERE id=%s", (scenario_id,))
        version = _select_one(cursor, f"SELECT * FROM {SCENARIO_VERSION_TABLE} WHERE id=%s AND scenario_id=%s", (version_id, scenario_id))
        if not row or not version:
            return None
        ensure_can_edit(row, user.user_id)
        cursor.execute(
            f"INSERT INTO {SCENARIO_VERSION_TABLE} (scenario_id,version,content,created_by_user_id,created_by_username,created_at) VALUES (%s,%s,%s,%s,%s,%s)",
            (scenario_id, row["version"], row.get("content") or "", user.user_id, user.username, now),
        )
        cursor.execute(
            f"UPDATE {SCENARIO_TABLE} SET content=%s,version=%s,updated_by_user_id=%s,updated_by_username=%s,updated_at=%s WHERE id=%s",
            (version["content"], _next_version(row["version"]), user.user_id, user.username, now, scenario_id),
        )
    return get_scenario(scenario_id, user)


def list_logs(scenario_name, system_id, alert_key, page, page_size):
    where = []
    params = []
    if scenario_name:
        where.append("scenario_name=%s")
        params.append(scenario_name)
    if system_id:
        where.append("extra_data LIKE %s")
        params.append(f'%"{system_id}"%')
    if alert_key:
        where.append("extra_data LIKE %s")
        params.append(f"%{alert_key}%")
    clause = " WHERE " + " AND ".join(where) if where else ""
    offset = (page - 1) * page_size
    with db_cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) AS total FROM {LOG_TABLE}{clause}", tuple(params))
        total = cursor.fetchone()["total"]
        cursor.execute(
            f"SELECT id,scenario_id,scenario_name,log_name,extra_data,remark,created_at FROM {LOG_TABLE}{clause} ORDER BY created_at DESC LIMIT %s OFFSET %s",
            tuple(params + [page_size, offset]),
        )
        items = cursor.fetchall()
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def log_stats(scenario_name):
    where = " WHERE scenario_name=%s" if scenario_name else ""
    params = (scenario_name,) if scenario_name else ()
    with db_cursor() as cursor:
        cursor.execute(f"SELECT scenario_name,extra_data FROM {LOG_TABLE}{where}", params)
        rows = cursor.fetchall()
    grouped = {}
    for row in rows:
        name = row["scenario_name"]
        stat = grouped.setdefault(name, {"scenario_name": name, "total": 0, "by_system": {}, "by_alert_source": {}})
        stat["total"] += 1
        extra = _json_loads(row.get("extra_data"), {})
        sys_id = extra.get("system_id") or "unknown"
        source = extra.get("alert_source") or extra.get("source") or "unknown"
        stat["by_system"][sys_id] = stat["by_system"].get(sys_id, 0) + 1
        stat["by_alert_source"][source] = stat["by_alert_source"].get(source, 0) + 1
    result = []
    for stat in grouped.values():
        result.append({
            "scenario_name": stat["scenario_name"],
            "total": stat["total"],
            "by_system": [{"system_id": key, "count": value} for key, value in stat["by_system"].items()],
            "by_alert_source": [{"alert_source": key, "count": value} for key, value in stat["by_alert_source"].items()],
        })
    return result


def get_log_html(log_id):
    with db_cursor() as cursor:
        return _select_one(cursor, f"SELECT html_content FROM {LOG_TABLE} WHERE id=%s", (log_id,))
