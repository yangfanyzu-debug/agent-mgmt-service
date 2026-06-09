from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ExecutionLogFiltersContractTests(unittest.TestCase):
    def test_logs_route_accepts_alert_source_filter(self):
        main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")

        route = re.search(
            r'@app\.get\("/logs", response_model=ExecutionLogPage\)\s*'
            r"def list_logs\((.*?)\):",
            main,
            re.S,
        )
        self.assertIsNotNone(route)
        self.assertIn("alert_source: str = None", route.group(1))
        self.assertIn("store.list_logs(scenario_name, system_id, alert_key, alert_source, page, page_size)", main)

    def test_log_store_filters_alert_source_from_extra_data_json(self):
        store = (ROOT / "app" / "services" / "store.py").read_text(encoding="utf-8")

        self.assertIn("def list_logs(scenario_name, system_id, alert_key, alert_source, page, page_size):", store)
        self.assertIn("JSON_EXTRACT(extra_data, '$.alert_source')", store)
        self.assertIn("JSON_VALID(extra_data)", store)
        self.assertIn("alert_source_expr", store)
        self.assertIn("where.append(f\"{alert_source_expr}=%s\")", store)


if __name__ == "__main__":
    unittest.main()
