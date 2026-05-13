from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SchemaContractTests(unittest.TestCase):
    def test_schema_sql_is_mysql57_compatible_without_foreign_keys(self):
        schema_path = ROOT / "migrations" / "001_create_agent_mgmt_tables.sql"

        self.assertTrue(schema_path.exists(), "schema migration must exist")
        sql = schema_path.read_text(encoding="utf-8").lower()

        self.assertNotIn("foreign key", sql)
        self.assertNotIn("constraint ", sql)
        self.assertNotIn("json", sql)
        self.assertIn("agent_mgmt_agent", sql)
        self.assertIn("created_by_user_id", sql)
        self.assertIn("created_by_username", sql)
        self.assertIn("updated_by_user_id", sql)
        self.assertIn("updated_by_username", sql)
        self.assertIn("unique key uq_agent_name", sql)
        self.assertIn("unique key uq_scenario_name", sql)

    def test_schema_uses_ordinary_indexes_for_manual_relationships(self):
        schema_path = ROOT / "migrations" / "001_create_agent_mgmt_tables.sql"

        self.assertTrue(schema_path.exists(), "schema migration must exist")
        sql = schema_path.read_text(encoding="utf-8").lower()

        self.assertIn("key ix_agent_version_agent_id", sql)
        self.assertIn("key ix_scenario_version_scenario_id", sql)
        self.assertIn("key ix_execution_log_scenario_id", sql)


if __name__ == "__main__":
    unittest.main()
