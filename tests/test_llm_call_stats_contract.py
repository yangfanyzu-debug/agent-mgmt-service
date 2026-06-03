from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LlmCallStatsContractTests(unittest.TestCase):
    def test_base_schema_defines_llm_call_log_and_execution_run_id(self):
        migration = (ROOT / "migrations" / "001_create_agent_mgmt_tables.sql").read_text(encoding="utf-8")

        self.assertIn("SET NAMES utf8mb4", migration)
        self.assertIn("CREATE TABLE IF NOT EXISTS `agent_mgmt_llm_call_log`", migration)
        self.assertIn("`run_id` VARCHAR(36) NOT NULL", migration)
        self.assertIn("`scenario_name` VARCHAR(200) NOT NULL DEFAULT 'unknown'", migration)
        self.assertIn("`agent_role` VARCHAR(200) NOT NULL", migration)
        self.assertIn("`call_index` INT NOT NULL", migration)
        self.assertIn("`model` VARCHAR(100) NOT NULL DEFAULT 'unknown'", migration)
        self.assertIn("`status` ENUM('success','failed') NOT NULL", migration)
        self.assertIn("`latency_ms` INT DEFAULT NULL", migration)
        self.assertIn("`retry_count` INT NOT NULL DEFAULT 0", migration)
        self.assertIn("`error_type` VARCHAR(50) DEFAULT NULL", migration)
        self.assertIn("`error_msg` VARCHAR(500) DEFAULT NULL", migration)
        self.assertIn("`input_tokens` INT DEFAULT NULL", migration)
        self.assertIn("`output_tokens` INT DEFAULT NULL", migration)
        self.assertIn("`extra_data` TEXT DEFAULT NULL", migration)
        self.assertIn("KEY ix_agent_mgmt_llm_call_log_run_id (`run_id`)", migration)
        self.assertIn("KEY ix_agent_mgmt_llm_call_log_scenario (`scenario_name`)", migration)
        self.assertIn("KEY ix_agent_mgmt_llm_call_log_model (`model`)", migration)
        self.assertIn("KEY ix_agent_mgmt_llm_call_log_status (`status`)", migration)
        self.assertIn("KEY ix_agent_mgmt_llm_call_log_created_at (`created_at`)", migration)
        self.assertRegex(
            migration,
            r"CREATE TABLE IF NOT EXISTS `agent_mgmt_execution_log` \(\s*`id` INT NOT NULL AUTO_INCREMENT,\s*`run_id` VARCHAR\(36\) DEFAULT NULL",
        )
        self.assertIn("KEY ix_agent_mgmt_execution_log_run_id (`run_id`)", migration)

    def test_incremental_migration_is_mysql57_safe(self):
        migration = (ROOT / "migrations" / "005_llm_call_logs.sql").read_text(encoding="utf-8")

        self.assertIn("SET NAMES utf8mb4", migration)
        self.assertIn("CREATE TABLE IF NOT EXISTS `agent_mgmt_llm_call_log`", migration)
        self.assertIn("INFORMATION_SCHEMA.COLUMNS", migration)
        self.assertIn("INFORMATION_SCHEMA.STATISTICS", migration)
        self.assertIn("ADD COLUMN `run_id` VARCHAR(36) DEFAULT NULL", migration)
        self.assertIn("ADD INDEX ix_agent_mgmt_execution_log_run_id (`run_id`)", migration)
        self.assertIn("ADD COLUMN `extra_data` TEXT DEFAULT NULL", migration)
        self.assertIn("PREPARE stmt FROM", migration)
        self.assertNotIn("ADD COLUMN IF NOT EXISTS", migration)
        self.assertNotIn("ADD INDEX IF NOT EXISTS", migration)

    def test_comment_repair_migration_preserves_schema_and_fixes_mojibake_comments(self):
        migration = (ROOT / "migrations" / "006_fix_llm_call_log_comments.sql").read_text(encoding="utf-8")

        self.assertIn("SET NAMES utf8mb4", migration)
        self.assertIn("ALTER TABLE `agent_mgmt_llm_call_log`", migration)
        self.assertIn("COMMENT = 'LLM 调用明细表'", migration)
        self.assertIn("MODIFY COLUMN `run_id` VARCHAR(36) NOT NULL COMMENT '请求唯一标识，关联同一次处理的所有调用'", migration)
        self.assertIn("MODIFY COLUMN `scenario_name` VARCHAR(200) NOT NULL DEFAULT 'unknown' COMMENT '场景名称'", migration)
        self.assertIn("MODIFY COLUMN `status` ENUM('success','failed') NOT NULL COMMENT '最终状态（重试耗尽仍失败=failed）'", migration)
        self.assertIn("MODIFY COLUMN `extra_data` TEXT DEFAULT NULL COMMENT '附加数据文本，如", migration)
        self.assertIn("ALTER TABLE `agent_mgmt_execution_log`", migration)
        self.assertIn("MODIFY COLUMN `run_id` VARCHAR(36) DEFAULT NULL COMMENT '请求唯一标识，关联 agent_mgmt_llm_call_log'", migration)

    def test_rename_migration_moves_existing_llm_call_log_to_agent_namespace(self):
        migration = (ROOT / "migrations" / "007_rename_llm_call_log.sql").read_text(encoding="utf-8")

        self.assertIn("SET NAMES utf8mb4", migration)
        self.assertIn("TABLE_NAME = 'llm_call_log'", migration)
        self.assertIn("TABLE_NAME = 'agent_mgmt_llm_call_log'", migration)
        self.assertIn("RENAME TABLE `llm_call_log` TO `agent_mgmt_llm_call_log`", migration)
        self.assertIn("ix_llm_call_log_run_id", migration)
        self.assertIn("ix_agent_mgmt_llm_call_log_run_id", migration)
        self.assertIn("RENAME INDEX", migration)
        self.assertIn("ALTER TABLE `agent_mgmt_execution_log`", migration)
        self.assertIn("COMMENT '请求唯一标识，关联 agent_mgmt_llm_call_log'", migration)

    def test_routes_are_read_only_and_unauthenticated_like_log_queries(self):
        main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")

        routes = (
            (r'@app\.get\("/llm-stats/summary"\)\s*def llm_stats_summary\((.*?)\):', "llm_stats_summary"),
            (r'@app\.get\("/llm-stats/failures", response_model=ExecutionLogPage\)\s*def llm_stats_failures\((.*?)\):', "llm_stats_failures"),
            (r'@app\.get\("/llm-stats/by-run/\{run_id\}"\)\s*def llm_stats_by_run\((.*?)\):', "llm_stats_by_run"),
            (r'@app\.get\("/llm-stats/by-scenario"\)\s*def llm_stats_by_scenario\((.*?)\):', "llm_stats_by_scenario"),
            (r'@app\.get\("/logs/by-run/\{run_id\}/html", response_class=HTMLResponse\)\s*def get_log_html_by_run\((.*?)\):', "get_log_html_by_run"),
        )
        for pattern, route_name in routes:
            match = re.search(pattern, main, re.S)
            self.assertIsNotNone(match, route_name)
            self.assertNotIn("Depends(get_current_user)", match.group(1), route_name)

        self.assertIn("store.llm_stats_summary(days)", main)
        self.assertIn("store.llm_stats_failures(days, page, page_size)", main)
        self.assertIn("store.llm_stats_by_run(run_id)", main)
        self.assertIn("page: int = Query(1, ge=1)", main)
        self.assertIn("page_size: int = Query(20, ge=1, le=100)", main)
        self.assertIn("store.llm_stats_by_scenario(days, only_failures, scenario_name, keyword, page, page_size)", main)
        self.assertIn("store.get_log_html_by_run(run_id)", main)

    def test_store_defines_expected_llm_aggregation_functions(self):
        store = (ROOT / "app" / "services" / "store.py").read_text(encoding="utf-8")

        self.assertIn('LLM_CALL_LOG_TABLE = "agent_mgmt_llm_call_log"', store)
        for function_name in (
            "llm_stats_summary",
            "llm_stats_failures",
            "llm_stats_by_run",
            "llm_stats_by_scenario",
            "get_log_html_by_run",
        ):
            self.assertIn(f"def {function_name}(", store)

        self.assertIn("COUNT(*) AS total_calls", store)
        self.assertIn("SUM(status='failed') AS total_failures", store)
        self.assertIn("AVG(latency_ms) AS avg_latency_ms", store)
        self.assertIn("SUM(input_tokens) AS total_input_tokens", store)
        self.assertIn("SUM(output_tokens) AS total_output_tokens", store)
        self.assertIn("GROUP BY model", store)
        self.assertIn("GROUP BY agent_role", store)
        self.assertIn("GROUP BY c.run_id", store)
        self.assertIn("ORDER BY created_at DESC", store)
        self.assertIn("def llm_stats_by_scenario(days, only_failures=False, scenario_name=None, keyword=None, page=1, page_size=20):", store)
        self.assertIn("SELECT COUNT(*) AS total FROM (", store)
        self.assertIn("LIMIT %s OFFSET %s", store)
        self.assertIn('"items": rows', store)
        self.assertIn('"total": _safe_int(total_row.get("total"))', store)


if __name__ == "__main__":
    unittest.main()
