from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


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
        for route in (
            '@app.get("/panorama/tree")',
            '@app.get("/panorama/stats")',
            '@app.get("/panorama/layers")',
            '@app.post("/panorama/layers"',
            '@app.put("/panorama/layers/{layer_id}")',
            '@app.delete("/panorama/layers/{layer_id}")',
            '@app.get("/panorama/nodes")',
            '@app.post("/panorama/nodes"',
            '@app.put("/panorama/nodes/{node_id}")',
            '@app.delete("/panorama/nodes/{node_id}")',
            '@app.post("/panorama/nodes/{node_id}/tags")',
            '@app.delete("/panorama/nodes/{node_id}/tags/{tag_id}")',
            '@app.get("/panorama/tags")',
            '@app.post("/panorama/tags"',
            '@app.put("/panorama/tags/{tag_id}")',
            '@app.delete("/panorama/tags/{tag_id}")',
            '@app.get("/panorama/nodes/{node_id}/slots")',
            '@app.post("/panorama/nodes/{node_id}/agent-slots"',
            '@app.put("/panorama/agent-slots/{slot_id}")',
            '@app.delete("/panorama/agent-slots/{slot_id}")',
            '@app.post("/panorama/nodes/{node_id}/scenario-slots"',
            '@app.put("/panorama/scenario-slots/{slot_id}")',
            '@app.delete("/panorama/scenario-slots/{slot_id}")',
        ):
            self.assertIn(route, source)

        panorama_section = source[source.index('@app.get("/panorama/tree")'):]
        self.assertGreaterEqual(len(re.findall(r"Depends\(get_current_user\)", panorama_section)), 20)
        self.assertNotIn("/panorama/page", source)
        self.assertNotIn("/panorama/echarts.min.js", source)


if __name__ == "__main__":
    unittest.main()
