from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
UI_ROOT_CANDIDATES = (
    ROOT.parent / "ruoyi-cloud-ops" / "ruoyi-ui",
    Path("/opt/ruoyi-cloud-ops/source/ruoyi-ui"),
)
UI_ROOT = next((path for path in UI_ROOT_CANDIDATES if path.exists()), UI_ROOT_CANDIDATES[0])
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
        self.assertIn('prop="id" label="ID"', source)
        self.assertIn('prop="run_id"', source)
        self.assertIn('label="runid"', source)
        self.assertIn("系统", source)
        self.assertIn("告警", source)
        self.assertIn("告警源", source)
        self.assertIn("生成时间", source)
        self.assertIn("查看详情", source)
        self.assertIn("openHtmlByRun", source)
        self.assertIn("getLogHtmlByRun", source)
        self.assertIn("writeHtmlTab", source)
        self.assertIn("alert_source: ''", source)
        self.assertIn("query.alert_source", source)
        self.assertIn("extra(row).alert_source || '-'", source)
        expected_order = (
            'prop="id" label="ID"',
            'prop="scenario_name" label="场景"',
            'label="系统"',
            'label="告警"',
            'prop="created_at" label="生成时间"',
            'prop="run_id" label="runid"',
            'prop="log_name" label="日志名称"',
            'label="操作"',
        )
        positions = [source.index(item) for item in expected_order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('prop="remark" label="备注"', source)
        self.assertNotIn('class="log-card"', source)
        self.assertNotIn('class="log-list"', source)

    def test_logs_page_keeps_twenty_rows_inside_fixed_height_table(self):
        source = LOGS_VIEW.read_text(encoding="utf-8")

        self.assertIn(':height="logTableHeight"', source)
        self.assertIn("logTableHeight()", source)
        self.assertIn("return 'calc(100vh - 335px)'", source)
        self.assertIn('class="am-scroll log-table-wrap"', source)
        self.assertIn('class="log-pagination"', source)
        self.assertIn(".log-table-wrap", source)
        self.assertIn(".log-pagination", source)


if __name__ == "__main__":
    unittest.main()
