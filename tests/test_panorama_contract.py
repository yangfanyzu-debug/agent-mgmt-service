from pathlib import Path
import ast
import unittest


ROOT = Path(__file__).resolve().parents[1]


def _route_decorator(decorator):
    if not isinstance(decorator, ast.Call):
        return None
    func = decorator.func
    if not isinstance(func, ast.Attribute):
        return None
    if not isinstance(func.value, ast.Name) or func.value.id != "app":
        return None
    if func.attr not in {"get", "post", "put", "delete"}:
        return None
    if not decorator.args:
        return None
    route_arg = decorator.args[0]
    if not isinstance(route_arg, ast.Constant) or not isinstance(route_arg.value, str):
        return None
    return func.attr, route_arg.value


def _contains_get_current_user_dependency(node):
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if not isinstance(func, ast.Name) or func.id != "Depends":
            continue
        if child.args and isinstance(child.args[0], ast.Name) and child.args[0].id == "get_current_user":
            return True
    return False


def _handler_requires_current_user(handler):
    defaults = list(handler.args.defaults) + [item for item in handler.args.kw_defaults if item is not None]
    if any(_contains_get_current_user_dependency(default) for default in defaults):
        return True

    for decorator in handler.decorator_list:
        route = _route_decorator(decorator)
        if route is None:
            continue
        for keyword in decorator.keywords:
            if keyword.arg == "dependencies" and _contains_get_current_user_dependency(keyword.value):
                return True
    return False


class PanoramaContractTests(unittest.TestCase):
    def test_panorama_migration_defines_mysql57_tables_without_json_or_foreign_keys(self):
        migration = ROOT / "migrations" / "008_panorama_tables.sql"
        self.assertTrue(migration.exists(), "panorama migration must exist")

        sql = migration.read_text(encoding="utf-8").lower()
        for table in (
            "agent_mgmt_panorama_layer",
            "agent_mgmt_panorama_node",
            "agent_mgmt_panorama_tag",
            "agent_mgmt_panorama_node_tag",
            "agent_mgmt_panorama_agent_slot",
            "agent_mgmt_panorama_scenario_slot",
        ):
            self.assertIn("create table if not exists `{}`".format(table), sql)

        self.assertNotIn("foreign key", sql)
        self.assertNotIn("constraint ", sql)
        self.assertNotIn(" json", sql)
        self.assertIn("on duplicate key update", sql)
        self.assertIn("planner_agent", sql)
        self.assertIn("es_expert_agent", sql)
        self.assertIn("alert_analysis", sql)

    def test_init_schema_runs_panorama_migration(self):
        source = (ROOT / "app" / "core" / "db.py").read_text(encoding="utf-8")
        self.assertIn("008_panorama_tables.sql", source)
        self.assertIn('_run_migration(cursor, "008_panorama_tables.sql")', source)

    def test_panorama_schemas_exist_in_pydantic_v1_style(self):
        source = (ROOT / "app" / "schemas.py").read_text(encoding="utf-8")
        for name in (
            "PanoramaLayerCreate",
            "PanoramaLayerUpdate",
            "PanoramaLayerOut",
            "PanoramaNodeCreate",
            "PanoramaNodeUpdate",
            "PanoramaNodeOut",
            "PanoramaTagCreate",
            "PanoramaTagUpdate",
            "PanoramaTagOut",
            "PanoramaNodeTagAssign",
            "PanoramaAgentSlotCreate",
            "PanoramaAgentSlotUpdate",
            "PanoramaAgentSlotOut",
            "PanoramaScenarioSlotCreate",
            "PanoramaScenarioSlotUpdate",
            "PanoramaScenarioSlotOut",
        ):
            self.assertRegex(source, r"class\s+{}\(BaseModel\):".format(name))
        self.assertNotIn("model_config", source)
        self.assertNotIn("model_rebuild", source)

    def test_panorama_store_uses_pymysql_cursor_and_no_skill_ready_file_reads(self):
        store_path = ROOT / "app" / "services" / "panorama_store.py"
        self.assertTrue(store_path.exists(), "panorama_store.py must exist")

        source = store_path.read_text(encoding="utf-8")
        self.assertIn("from app.core.db import db_cursor", source)
        self.assertNotIn("sqlalchemy", source.lower())
        self.assertNotIn("is_ready", source)
        self.assertNotIn("Path(", source)
        self.assertIn("def resolve_deploy_status(row):", source)
        self.assertIn('return "planned"', source)
        self.assertIn('return "inactive"', source)
        self.assertIn('return "deployed"', source)
        self.assertIn('"ready": 0', source)

    def test_panorama_routes_are_registered_and_authenticated(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        handlers = {}
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                route = _route_decorator(decorator)
                if route is not None:
                    handlers[route] = node

        for method, route in (
            ("get", "/panorama/tree"),
            ("get", "/panorama/stats"),
            ("get", "/panorama/layers"),
            ("post", "/panorama/layers"),
            ("put", "/panorama/layers/{layer_id}"),
            ("delete", "/panorama/layers/{layer_id}"),
            ("get", "/panorama/nodes"),
            ("post", "/panorama/nodes"),
            ("put", "/panorama/nodes/{node_id}"),
            ("delete", "/panorama/nodes/{node_id}"),
            ("post", "/panorama/nodes/{node_id}/tags"),
            ("delete", "/panorama/nodes/{node_id}/tags/{tag_id}"),
            ("get", "/panorama/tags"),
            ("post", "/panorama/tags"),
            ("put", "/panorama/tags/{tag_id}"),
            ("delete", "/panorama/tags/{tag_id}"),
            ("get", "/panorama/nodes/{node_id}/slots"),
            ("post", "/panorama/nodes/{node_id}/agent-slots"),
            ("put", "/panorama/agent-slots/{slot_id}"),
            ("delete", "/panorama/agent-slots/{slot_id}"),
            ("post", "/panorama/nodes/{node_id}/scenario-slots"),
            ("put", "/panorama/scenario-slots/{slot_id}"),
            ("delete", "/panorama/scenario-slots/{slot_id}"),
        ):
            handler = handlers.get((method, route))
            self.assertIsNotNone(handler, "{} {} route must be registered".format(method.upper(), route))
            self.assertTrue(
                _handler_requires_current_user(handler),
                "{} {} route must require get_current_user".format(method.upper(), route),
            )

        self.assertNotIn("/panorama/page", source)
        self.assertNotIn("/panorama/echarts.min.js", source)


if __name__ == "__main__":
    unittest.main()
