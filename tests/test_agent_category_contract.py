from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentCategoryContractTests(unittest.TestCase):
    def test_schema_defines_agent_category_tree_table_and_seed_data(self):
        sql = (ROOT / "migrations" / "001_create_agent_mgmt_tables.sql").read_text(encoding="utf-8").lower()

        self.assertIn("create table if not exists `agent_mgmt_agent_category`", sql)
        self.assertIn("`parent_id` int default null", sql)
        self.assertIn("`category_code` varchar(100) not null", sql)
        self.assertIn("unique key uq_agent_category_code", sql)
        self.assertIn("insert ignore into `agent_mgmt_agent_category`", sql)
        self.assertIn("'alert_analysis'", sql)

    def test_backend_exposes_authenticated_category_tree_api(self):
        main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        store = (ROOT / "app" / "services" / "store.py").read_text(encoding="utf-8")

        self.assertIn('@app.get("/agent-categories")', main)
        self.assertIn("def list_agent_categories(user: CurrentUser = Depends(get_current_user))", main)
        self.assertIn("def list_agent_categories():", store)
        self.assertIn("def _build_category_tree(rows):", store)

    def test_agent_list_accepts_category_code_filter(self):
        main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        store = (ROOT / "app" / "services" / "store.py").read_text(encoding="utf-8")

        self.assertIn("category_codes: str = Query(None)", main)
        self.assertIn("store.list_agents(user, scope, status, type, category_codes)", main)
        self.assertIn("def list_agents(user, scope, status, agent_type, category_codes=None):", store)
        self.assertIn("tags IN (", store)
        self.assertIn("def _split_codes(value):", store)

    def test_agent_create_requires_category_tags(self):
        schemas = (ROOT / "app" / "schemas.py").read_text(encoding="utf-8")
        store = (ROOT / "app" / "services" / "store.py").read_text(encoding="utf-8")

        self.assertIn("tags: str", schemas)
        self.assertIn("def validate_tags(cls, value):", schemas)
        self.assertIn("_ensure_category_exists(cursor, req.tags)", store)


if __name__ == "__main__":
    unittest.main()
