from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class VersionContractTests(unittest.TestCase):
    def test_agent_versions_snapshot_tags_for_full_rollback(self):
        sql = (ROOT / "migrations" / "001_create_agent_mgmt_tables.sql").read_text(encoding="utf-8").lower()
        store = (ROOT / "app" / "services" / "store.py").read_text(encoding="utf-8").lower()

        agent_version_block = re.search(r"create table if not exists `agent_mgmt_agent_version` \((.*?)\) engine=", sql, re.S)
        self.assertIsNotNone(agent_version_block)
        self.assertIn("`tags` varchar(500)", agent_version_block.group(1))
        self.assertIn("`is_active` tinyint(1)", agent_version_block.group(1))
        self.assertIn("`activated_at` datetime", agent_version_block.group(1))
        self.assertIsNotNone(re.search(r"insert into \{agent_version_table\}.*?\(agent_id,\s*version,\s*content,\s*tags,", store, re.S))
        self.assertIsNotNone(re.search(r"update \{agent_table\} set content=%s,\s*tags=%s,", store, re.S))

    def test_agent_table_tracks_latest_and_active_versions_separately(self):
        sql = (ROOT / "migrations" / "001_create_agent_mgmt_tables.sql").read_text(encoding="utf-8").lower()
        db = (ROOT / "app" / "core" / "db.py").read_text(encoding="utf-8").lower()
        store = (ROOT / "app" / "services" / "store.py").read_text(encoding="utf-8").lower()

        agent_block = re.search(r"create table if not exists `agent_mgmt_agent` \((.*?)\) engine=", sql, re.S)
        self.assertIsNotNone(agent_block)
        for column in ("active_version", "active_content", "active_tags"):
            self.assertIn(f"`{column}`", agent_block.group(1))
            self.assertIn(column, db)

        activate_block = re.search(r"def activate_agent_version\(agent_id, version_id, user\):(.*?)def rollback_agent", store, re.S)
        self.assertIsNotNone(activate_block)
        activate_source = activate_block.group(1)
        self.assertIn("active_version=%s", activate_source)
        self.assertIn("status=%s", activate_source)
        self.assertIn('"active"', activate_source)
        self.assertIn("set is_active=0 where agent_id=%s", activate_source)
        self.assertIn("affected_scenarios", activate_source)

    def test_scenario_versions_snapshot_mutable_fields_for_full_rollback(self):
        sql = (ROOT / "migrations" / "001_create_agent_mgmt_tables.sql").read_text(encoding="utf-8").lower()
        store = (ROOT / "app" / "services" / "store.py").read_text(encoding="utf-8").lower()

        scenario_version_block = re.search(r"create table if not exists `agent_mgmt_scenario_version` \((.*?)\) engine=", sql, re.S)
        self.assertIsNotNone(scenario_version_block)
        for column in ("description", "sub_type_hint", "keyword_hint", "skill_selector_dims", "related_agents"):
            self.assertIn(f"`{column}`", scenario_version_block.group(1))

        self.assertIsNotNone(re.search(r"insert into \{scenario_version_table\}.*?description,\s*sub_type_hint,\s*keyword_hint,\s*skill_selector_dims,\s*related_agents,", store, re.S))
        self.assertIsNotNone(re.search(r"update \{scenario_table\}.*?description=%s,sub_type_hint=%s,keyword_hint=%s,skill_selector_dims=%s,\s*related_agents=%s,content=%s,", store, re.S))

    def test_version_routes_require_current_user_headers(self):
        main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")

        self.assertIn("def list_agent_versions(agent_id: int, user: CurrentUser = Depends(get_current_user))", main)
        self.assertIn("def activate_agent_version(agent_id: int, version_id: int, user: CurrentUser = Depends(get_current_user))", main)
        self.assertIn("def list_agent_related_scenarios(agent_id: int, user: CurrentUser = Depends(get_current_user))", main)
        self.assertIn("def list_scenario_versions(scenario_id: int, user: CurrentUser = Depends(get_current_user))", main)


if __name__ == "__main__":
    unittest.main()
