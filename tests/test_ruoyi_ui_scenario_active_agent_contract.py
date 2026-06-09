from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
UI_ROOT_CANDIDATES = (
    ROOT.parent / "ruoyi-cloud-ops" / "ruoyi-ui",
    Path("/opt/ruoyi-cloud-ops/source/ruoyi-ui"),
)
UI_ROOT = next((path for path in UI_ROOT_CANDIDATES if path.exists()), UI_ROOT_CANDIDATES[0])
SCENARIOS_VIEW = UI_ROOT / "src" / "views" / "agentMgmt" / "scenarios" / "index.vue"


class RuoyiScenarioActiveAgentContractTests(unittest.TestCase):
    def test_scenario_agent_preview_uses_active_agent_content(self):
        source = SCENARIOS_VIEW.read_text(encoding="utf-8")

        self.assertIn("agentRuntimeContent(agent)", source)
        self.assertIn("return agent.active_content || agent.content || ''", source)
        self.assertIn("const content = this.agentRuntimeContent(agent)", source)
        self.assertIn("this.parseYamlList(content, 'skills')", source)
        self.assertIn("this.parseYamlField(content, 'role')", source)
        self.assertNotIn("this.parseYamlList(agent.content, 'skills')", source)
        self.assertNotIn("this.parseYamlField(agent.content, 'role')", source)


if __name__ == "__main__":
    unittest.main()
