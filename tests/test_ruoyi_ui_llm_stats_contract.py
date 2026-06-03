from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
UI_ROOT = ROOT.parent / "ruoyi-cloud-ops" / "ruoyi-ui"
API_FILE = UI_ROOT / "src" / "api" / "agentMgmt" / "index.js"
LLM_VIEW = UI_ROOT / "src" / "views" / "agentMgmt" / "llmStats" / "index.vue"


class RuoyiLlmStatsContractTests(unittest.TestCase):
    def test_api_exports_llm_stats_methods(self):
        source = API_FILE.read_text(encoding="utf-8")

        self.assertIn("export function getLlmStatsSummary(params)", source)
        self.assertIn("export function listLlmStatsFailures(params)", source)
        self.assertIn("export function getLlmStatsByRun(runId)", source)
        self.assertIn("export function listLlmStatsByScenario(params)", source)
        self.assertIn("export function getLogHtmlByRun(runId)", source)
        self.assertIn("export function logHtmlByRunUrl(runId)", source)
        self.assertIn("`${base}/llm-stats/summary`", source)
        self.assertIn("`${base}/llm-stats/failures`", source)
        self.assertIn("`${base}/llm-stats/by-run/${runId}`", source)
        self.assertIn("`${base}/llm-stats/by-scenario`", source)
        self.assertIn("`${process.env.VUE_APP_BASE_API}${base}/logs/by-run/${runId}/html`", source)

    def test_llm_stats_page_contains_expected_ui_and_calls(self):
        source = LLM_VIEW.read_text(encoding="utf-8")

        self.assertIn("name: 'AgentMgmtLlmStats'", source)
        self.assertIn("LLM 调用统计", source)
        self.assertIn("模型资源使用与故障分析", source)
        self.assertIn("整体统计", source)
        self.assertIn("场景维度", source)
        self.assertIn("总调用", source)
        self.assertIn("成功率", source)
        self.assertIn("失败数", source)
        self.assertIn("平均延迟", source)
        self.assertIn("按模型分布", source)
        self.assertIn("按角色分布", source)
        self.assertIn("最近失败记录", source)
        self.assertIn("LLM 调用详情", source)
        self.assertIn("getLlmStatsSummary", source)
        self.assertIn("listLlmStatsFailures", source)
        self.assertIn("getLlmStatsByRun", source)
        self.assertIn("listLlmStatsByScenario", source)
        self.assertIn("getLogHtmlByRun", source)
        self.assertIn("openRunDrawer", source)
        self.assertIn("openLogByRun", source)
        self.assertIn("el-drawer", source)
        self.assertIn("runIdQuery", source)
        self.assertIn("only_failures", source)

    def test_llm_stats_page_explains_latency_and_uses_wide_drawer(self):
        source = LLM_VIEW.read_text(encoding="utf-8")

        self.assertIn("所有LLM调用的端到端耗时均值，包含网络往返、模型推理及排队等待时间", source)
        self.assertIn("该模型所有LLM调用的端到端耗时均值", source)
        self.assertIn("该角色所有LLM调用的端到端耗时均值", source)
        self.assertIn("该请求所有LLM调用的平均耗时", source)
        self.assertIn("该请求所有LLM调用耗时之和", source)
        self.assertIn('size="min(1180px, 92%)"', source)
        self.assertIn('class-name="compact-column"', source)
        self.assertIn('class-name="error-column"', source)

    def test_llm_drawer_uses_readable_column_widths(self):
        source = LLM_VIEW.read_text(encoding="utf-8")

        self.assertIn('prop="agent_role" label="角色" width="145"', source)
        self.assertIn('prop="model" label="模型" width="120"', source)
        self.assertIn('label="状态" width="78"', source)
        self.assertIn('label="延迟" width="86"', source)
        self.assertIn('prop="retry_count" label="重试" width="64"', source)
        self.assertIn('prop="error_msg" label="错误" width="250"', source)
        self.assertIn('prop="input_tokens" label="输入Tokens" width="96"', source)
        self.assertIn('prop="output_tokens" label="输出Tokens" width="96"', source)
        self.assertIn('prop="created_at" label="时间" width="145"', source)
        self.assertNotIn('label="状态" width="68"', source)
        self.assertNotIn('label="延迟" width="76"', source)
        self.assertNotIn('prop="error_msg" label="错误" min-width="240"', source)

    def test_llm_run_id_opens_execution_log_report_like_logs_page(self):
        source = LLM_VIEW.read_text(encoding="utf-8")

        self.assertIn("async openLogByRun(runId)", source)
        self.assertIn("await getLogHtmlByRun(runId)", source)
        self.assertIn("writeHtmlTab(tab, html)", source)
        self.assertNotIn("window.open(logHtmlByRunUrl(runId)", source)

    def test_drawer_total_latency_tip_precedes_label(self):
        source = LLM_VIEW.read_text(encoding="utf-8")

        self.assertIn(
            '<el-tooltip effect="dark" content="该请求所有LLM调用耗时之和" placement="top">\n'
            '              <i class="el-icon-question latency-tip"></i>\n'
            '            </el-tooltip>\n'
            '            总延迟',
            source,
        )


if __name__ == "__main__":
    unittest.main()
