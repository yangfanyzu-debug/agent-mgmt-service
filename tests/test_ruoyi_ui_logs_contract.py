from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
UI_ROOT = ROOT.parent / "ruoyi-cloud-ops" / "ruoyi-ui"
API_FILE = UI_ROOT / "src" / "api" / "agentMgmt" / "index.js"
LOGS_VIEW = UI_ROOT / "src" / "views" / "agentMgmt" / "logs" / "index.vue"


class RuoyiLogsContractTests(unittest.TestCase):
    def test_api_exports_run_id_log_html_method(self):
        source = API_FILE.read_text(encoding="utf-8")

        self.assertIn("export function getLogHtmlByRun(runId)", source)
        self.assertIn("`${base}/logs/by-run/${runId}/html`", source)
        self.assertIn("responseType: 'text'", source)

    def test_logs_page_uses_table_instead_of_cards(self):
        source = LOGS_VIEW.read_text(encoding="utf-8")

        self.assertIn("name: 'AgentMgmtLogs'", source)
        self.assertIn("<el-table", source)
        self.assertIn('prop="run_id"', source)
        self.assertIn('label="run_id"', source)
        self.assertIn("系统", source)
        self.assertIn("告警", source)
        self.assertIn("查看详情", source)
        self.assertIn("openHtmlByRun", source)
        self.assertIn("getLogHtmlByRun", source)
        self.assertIn("writeHtmlTab", source)
        self.assertNotIn('class="log-card"', source)
        self.assertNotIn('class="log-list"', source)


if __name__ == "__main__":
    unittest.main()
