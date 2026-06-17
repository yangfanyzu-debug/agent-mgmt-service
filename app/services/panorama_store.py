from datetime import datetime
import json
from typing import Any, Dict, List, Optional

import yaml

from app.core.db import db_cursor
from app.services import store


LAYER_TABLE = "agent_mgmt_panorama_layer"
NODE_TABLE = "agent_mgmt_panorama_node"
TAG_TABLE = "agent_mgmt_panorama_tag"
NODE_TAG_TABLE = "agent_mgmt_panorama_node_tag"
AGENT_SLOT_TABLE = "agent_mgmt_panorama_agent_slot"
SCENARIO_SLOT_TABLE = "agent_mgmt_panorama_scenario_slot"


def _now():
    return datetime.now()


def _json_text(value):
    return json.dumps(value, ensure_ascii=False) if value is not None else None


def _json_object(value):
    if not value:
        return None
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _select_one(cursor, sql, params=()):
    cursor.execute(sql, params)
    return cursor.fetchone()


def _select_all(cursor, sql, params=()):
    cursor.execute(sql, params)
    return cursor.fetchall()


def _clean_update_payload(data, allowed):
    payload = data.dict(exclude_unset=True)
    return {key: value for key, value in payload.items() if key in allowed}


def resolve_deploy_status(row):
    if not row:
        return "planned"
    if row.get("status") == "active":
        return "deployed"
    return "inactive"


def _parse_agent_skills(agent, cursor=None):
    if not agent:
        return []
    content = agent.get("active_content") or agent.get("content") or ""
    try:
        parsed = yaml.safe_load(content) or {}
    except yaml.YAMLError:
        return []
    skills = parsed.get("skills")
    if isinstance(skills, str):
        skills = [skills]
    if not isinstance(skills, list):
        return []
    result = []
    for item in skills:
        if not isinstance(item, str) or not item:
            continue
        entry = {"name": item, "is_ready": False}
        if cursor is not None:
            cursor.execute("SELECT status FROM skills WHERE title = %s", (item,))
            row = cursor.fetchone()
            if row and row.get("status") == "published":
                entry["is_ready"] = True
        result.append(entry)
    return result


def list_layers():
    with db_cursor() as cursor:
        return _select_all(cursor, f"SELECT * FROM {LAYER_TABLE} ORDER BY display_order ASC, id ASC")


def create_layer(data):
    now = _now()
    style_config = _json_text(data.style_config)
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            f"""
            INSERT INTO {LAYER_TABLE}
              (name, description, display_order, color, show_label, style_config, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (data.name, data.description, data.display_order, data.color, 1 if data.show_label else 0, style_config, now, now),
        )
        layer_id = cursor.lastrowid
    return get_layer(layer_id)


def get_layer(layer_id):
    with db_cursor() as cursor:
        return _select_one(cursor, f"SELECT * FROM {LAYER_TABLE} WHERE id=%s", (layer_id,))


def update_layer(layer_id, data):
    payload = _clean_update_payload(data, {"name", "description", "display_order", "color", "show_label", "style_config"})
    if "show_label" in payload:
        payload["show_label"] = 1 if payload["show_label"] else 0
    if "style_config" in payload:
        payload["style_config"] = _json_text(payload["style_config"])
    return _update_row(LAYER_TABLE, layer_id, payload)


def delete_layer(layer_id):
    return _delete_row(LAYER_TABLE, layer_id)


def list_nodes():
    with db_cursor() as cursor:
        return _select_all(cursor, f"SELECT * FROM {NODE_TABLE} ORDER BY sort_order ASC, id ASC")


def create_node(data):
    now = _now()
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            f"""
            INSERT INTO {NODE_TABLE}
              (parent_id, layer_id, name, description, sort_order, data_binding_type, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (data.parent_id, data.layer_id, data.name, data.description, data.sort_order, data.data_binding_type, now, now),
        )
        node_id = cursor.lastrowid
    return get_node(node_id)


def get_node(node_id):
    with db_cursor() as cursor:
        return _select_one(cursor, f"SELECT * FROM {NODE_TABLE} WHERE id=%s", (node_id,))


def update_node(node_id, data):
    payload = _clean_update_payload(data, {"parent_id", "layer_id", "name", "description", "sort_order", "data_binding_type"})
    return _update_row(NODE_TABLE, node_id, payload)


def delete_node(node_id):
    with db_cursor(commit=True) as cursor:
        cursor.execute(f"DELETE FROM {AGENT_SLOT_TABLE} WHERE node_id=%s", (node_id,))
        cursor.execute(f"DELETE FROM {SCENARIO_SLOT_TABLE} WHERE node_id=%s", (node_id,))
        cursor.execute(f"DELETE FROM {NODE_TAG_TABLE} WHERE node_id=%s", (node_id,))
        cursor.execute(f"DELETE FROM {NODE_TABLE} WHERE id=%s", (node_id,))
        return cursor.rowcount > 0


def list_tags():
    with db_cursor() as cursor:
        return _select_all(cursor, f"SELECT * FROM {TAG_TABLE} ORDER BY id ASC")


def create_tag(data):
    now = _now()
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            f"""
            INSERT INTO {TAG_TABLE}
              (name, description, border_color, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (data.name, data.description, data.border_color, now, now),
        )
        tag_id = cursor.lastrowid
    return get_tag(tag_id)


def get_tag(tag_id):
    with db_cursor() as cursor:
        return _select_one(cursor, f"SELECT * FROM {TAG_TABLE} WHERE id=%s", (tag_id,))


def update_tag(tag_id, data):
    payload = _clean_update_payload(data, {"name", "description", "border_color"})
    return _update_row(TAG_TABLE, tag_id, payload)


def delete_tag(tag_id):
    with db_cursor(commit=True) as cursor:
        cursor.execute(f"DELETE FROM {NODE_TAG_TABLE} WHERE tag_id=%s", (tag_id,))
        cursor.execute(f"DELETE FROM {TAG_TABLE} WHERE id=%s", (tag_id,))
        return cursor.rowcount > 0


def assign_node_tag(node_id, tag_id):
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            f"INSERT IGNORE INTO {NODE_TAG_TABLE} (node_id, tag_id, created_at) VALUES (%s, %s, %s)",
            (node_id, tag_id, _now()),
        )
    return True


def remove_node_tag(node_id, tag_id):
    with db_cursor(commit=True) as cursor:
        cursor.execute(f"DELETE FROM {NODE_TAG_TABLE} WHERE node_id=%s AND tag_id=%s", (node_id, tag_id))
        return cursor.rowcount > 0


def list_node_slots(node_id):
    with db_cursor() as cursor:
        return {
            "agent_slots": _select_all(cursor, f"SELECT * FROM {AGENT_SLOT_TABLE} WHERE node_id=%s ORDER BY sort_order ASC, id ASC", (node_id,)),
            "scenario_slots": _select_all(cursor, f"SELECT * FROM {SCENARIO_SLOT_TABLE} WHERE node_id=%s ORDER BY sort_order ASC, id ASC", (node_id,)),
        }


def create_agent_slot(node_id, data):
    return _create_slot(AGENT_SLOT_TABLE, node_id, data)


def update_agent_slot(slot_id, data):
    payload = _clean_update_payload(data, {"display_name", "match_name", "description", "sort_order"})
    return _update_row(AGENT_SLOT_TABLE, slot_id, payload)


def delete_agent_slot(slot_id):
    return _delete_row(AGENT_SLOT_TABLE, slot_id)


def create_scenario_slot(node_id, data):
    return _create_slot(SCENARIO_SLOT_TABLE, node_id, data)


def update_scenario_slot(slot_id, data):
    payload = _clean_update_payload(data, {"display_name", "match_name", "description", "sort_order"})
    return _update_row(SCENARIO_SLOT_TABLE, slot_id, payload)


def delete_scenario_slot(slot_id):
    return _delete_row(SCENARIO_SLOT_TABLE, slot_id)


def _create_slot(table, node_id, data):
    now = _now()
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            f"""
            INSERT INTO {table}
              (node_id, display_name, match_name, description, sort_order, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (node_id, data.display_name, data.match_name, data.description, data.sort_order, now, now),
        )
        slot_id = cursor.lastrowid
    with db_cursor() as cursor:
        return _select_one(cursor, f"SELECT * FROM {table} WHERE id=%s", (slot_id,))


def _update_row(table, row_id, payload):
    if not payload:
        with db_cursor() as cursor:
            return _select_one(cursor, f"SELECT * FROM {table} WHERE id=%s", (row_id,))
    payload["updated_at"] = _now()
    parts = ", ".join(f"{key}=%s" for key in payload)
    values = list(payload.values()) + [row_id]
    with db_cursor(commit=True) as cursor:
        cursor.execute(f"UPDATE {table} SET {parts} WHERE id=%s", values)
        if cursor.rowcount == 0:
            return None
    with db_cursor() as cursor:
        return _select_one(cursor, f"SELECT * FROM {table} WHERE id=%s", (row_id,))


def _delete_row(table, row_id):
    with db_cursor(commit=True) as cursor:
        cursor.execute(f"DELETE FROM {table} WHERE id=%s", (row_id,))
        return cursor.rowcount > 0


def get_panorama_tree():
    return get_tree()


def get_tree():
    with db_cursor() as cursor:
        nodes = _select_all(cursor, f"SELECT * FROM {NODE_TABLE} ORDER BY sort_order ASC, id ASC")
        if not nodes:
            return None
        layer_map = {row["id"]: row for row in _select_all(cursor, f"SELECT * FROM {LAYER_TABLE}")}
        tags_by_node = _load_tags_by_node(cursor)
        agent_slots_by_node = _load_agent_slots_by_node(cursor)
        scenario_slots_by_node = _load_scenario_slots_by_node(cursor)
        children_by_parent = {}
        for node in nodes:
            children_by_parent.setdefault(node.get("parent_id"), []).append(node)
        roots = sorted(children_by_parent.get(None, []), key=lambda item: (item.get("sort_order") or 0, item.get("id") or 0))
        if not roots:
            return None
        return _build_tree_node(cursor, roots[0], children_by_parent, layer_map, tags_by_node, agent_slots_by_node, scenario_slots_by_node)


def _load_tags_by_node(cursor):
    rows = _select_all(
        cursor,
        f"""
        SELECT nt.node_id, t.id, t.name, t.border_color
          FROM {NODE_TAG_TABLE} nt
          JOIN {TAG_TABLE} t ON t.id = nt.tag_id
         ORDER BY t.id ASC
        """,
    )
    result = {}
    for row in rows:
        result.setdefault(row["node_id"], []).append({"id": row["id"], "name": row["name"], "border_color": row["border_color"]})
    return result


def _load_agent_slots_by_node(cursor):
    rows = _select_all(cursor, f"SELECT * FROM {AGENT_SLOT_TABLE} ORDER BY sort_order ASC, id ASC")
    result = {}
    for row in rows:
        result.setdefault(row["node_id"], []).append(row)
    return result


def _load_scenario_slots_by_node(cursor):
    rows = _select_all(cursor, f"SELECT * FROM {SCENARIO_SLOT_TABLE} ORDER BY sort_order ASC, id ASC")
    result = {}
    for row in rows:
        result.setdefault(row["node_id"], []).append(row)
    return result


def _build_tree_node(cursor, node, children_by_parent, layer_map, tags_by_node, agent_slots_by_node, scenario_slots_by_node):
    layer = layer_map.get(node.get("layer_id"))
    children = sorted(children_by_parent.get(node["id"], []), key=lambda item: (item.get("sort_order") or 0, item.get("id") or 0))
    return {
        "id": node["id"],
        "name": node["name"],
        "description": node.get("description"),
        "data_binding_type": node.get("data_binding_type") or "none",
        "layer": _format_layer(layer),
        "tags": tags_by_node.get(node["id"], []),
        "agent_slots": [_resolve_agent_slot(cursor, item) for item in agent_slots_by_node.get(node["id"], [])],
        "scenario_slots": [_resolve_scenario_slot(cursor, item) for item in scenario_slots_by_node.get(node["id"], [])],
        "children": [_build_tree_node(cursor, child, children_by_parent, layer_map, tags_by_node, agent_slots_by_node, scenario_slots_by_node) for child in children],
    }


def _format_layer(layer):
    if not layer:
        return None
    return {
        "id": layer["id"],
        "name": layer["name"],
        "description": layer.get("description"),
        "display_order": layer.get("display_order") or 0,
        "color": layer.get("color") or "#7F77DD",
        "show_label": bool(layer.get("show_label")),
        "style_config": _json_object(layer.get("style_config")),
        "created_at": layer.get("created_at"),
        "updated_at": layer.get("updated_at"),
    }


def _resolve_agent_slot(cursor, slot):
    agent = _select_one(cursor, f"SELECT * FROM {store.AGENT_TABLE} WHERE agent_name=%s", (slot["match_name"],))
    return {
        "slot_id": slot["id"],
        "display_name": slot["display_name"],
        "match_name": slot["match_name"],
        "description": slot.get("description"),
        "status": resolve_deploy_status(agent),
        "skills": _parse_agent_skills(agent, cursor),
    }


def _resolve_scenario_slot(cursor, slot):
    scenario = _select_one(cursor, f"SELECT * FROM {store.SCENARIO_TABLE} WHERE scenario_name=%s", (slot["match_name"],))
    agents = []
    if scenario and scenario.get("status") == "active":
        agents = _scenario_agents(cursor, scenario)
    return {
        "slot_id": slot["id"],
        "display_name": slot["display_name"],
        "match_name": slot["match_name"],
        "description": slot.get("description"),
        "status": resolve_deploy_status(scenario),
        "agents": agents,
    }


def _scenario_agents(cursor, scenario):
    related = store._json_loads(scenario.get("related_agents"), {})
    names = []
    planner = related.get("planner")
    if planner:
        names.append(planner)
    for item in related.get("experts", []):
        if item.get("enabled", True) and item.get("name"):
            names.append(item["name"])
    result = []
    for name in names:
        agent = _select_one(cursor, f"SELECT * FROM {store.AGENT_TABLE} WHERE agent_name=%s", (name,))
        result.append({
            "slot_id": None,
            "display_name": name,
            "match_name": name,
            "description": None,
            "status": resolve_deploy_status(agent),
            "skills": _parse_agent_skills(agent, cursor),
        })
    return result


def get_panorama_stats():
    return get_stats()


def get_stats():
    with db_cursor() as cursor:
        scenario_slots = _select_all(cursor, f"SELECT * FROM {SCENARIO_SLOT_TABLE}")
        agent_slots = _select_all(cursor, f"SELECT * FROM {AGENT_SLOT_TABLE}")
        scenario_deployed = 0
        for slot in scenario_slots:
            scenario = _select_one(cursor, f"SELECT status FROM {store.SCENARIO_TABLE} WHERE scenario_name=%s", (slot["match_name"],))
            if scenario and scenario.get("status") == "active":
                scenario_deployed += 1

        agent_deployed = 0
        agent_inactive = 0
        skill_names = set()
        for slot in agent_slots:
            agent = _select_one(cursor, f"SELECT * FROM {store.AGENT_TABLE} WHERE agent_name=%s", (slot["match_name"],))
            if agent:
                if agent.get("status") == "active":
                    agent_deployed += 1
                else:
                    agent_inactive += 1
                for skill in _parse_agent_skills(agent, cursor):
                    skill_names.add(skill["name"])

        return {
            "scenarios": {"designed": len(scenario_slots), "deployed": scenario_deployed},
            "agents": {"designed": len(agent_slots), "deployed": agent_deployed, "inactive": agent_inactive},
            "skills": {"total": len(skill_names), "ready": 0},
            "by_node": _node_agent_coverage(cursor),
        }


def _node_agent_coverage(cursor):
    nodes = _select_all(cursor, f"SELECT id, name FROM {NODE_TABLE} WHERE data_binding_type='agent' ORDER BY sort_order ASC, id ASC")
    result = []
    for node in nodes:
        slots = _select_all(cursor, f"SELECT * FROM {AGENT_SLOT_TABLE} WHERE node_id=%s", (node["id"],))
        designed = len(slots)
        if not designed:
            continue
        deployed = 0
        for slot in slots:
            agent = _select_one(cursor, f"SELECT status FROM {store.AGENT_TABLE} WHERE agent_name=%s", (slot["match_name"],))
            if agent and agent.get("status") == "active":
                deployed += 1
        result.append({
            "node_id": node["id"],
            "node_name": node["name"],
            "agents_designed": designed,
            "agents_deployed": deployed,
            "coverage_pct": int(deployed / designed * 100) if designed else 0,
        })
    return sorted(result, key=lambda item: item["coverage_pct"], reverse=True)
