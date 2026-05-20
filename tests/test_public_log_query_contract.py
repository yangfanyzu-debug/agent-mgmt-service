from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PublicLogQueryContractTests(unittest.TestCase):
    def test_alert_key_log_query_is_public(self):
        main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")

        route = re.search(
            r'@app\.get\("/logs/by-alert-key", response_model=ExecutionLogPage\)\s*'
            r"def list_logs_by_alert_key\((.*?)\):",
            main,
            re.S,
        )
        self.assertIsNotNone(route)
        self.assertNotIn("Depends(get_current_user)", route.group(1))

    def test_alert_key_log_query_uses_extra_data_json_field(self):
        store = (ROOT / "app" / "services" / "store.py").read_text(encoding="utf-8")

        self.assertIn("def list_logs_by_alert_key(alert_key, page, page_size):", store)
        self.assertIn("JSON_EXTRACT(extra_data, '$.alert_key')", store)
        self.assertIn("JSON_VALID(extra_data)", store)
        self.assertIn("html_content", store)


if __name__ == "__main__":
    unittest.main()
