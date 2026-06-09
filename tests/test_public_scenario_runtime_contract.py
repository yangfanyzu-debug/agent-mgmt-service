from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PublicScenarioRuntimeContractTests(unittest.TestCase):
    def test_public_routes_are_post_and_unauthenticated(self):
        main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")

        list_route = re.search(
            r'@app\.post\("/public/scenarios", response_model=PublicScenarioListOut\)\s*'
            r"def list_public_scenarios\((.*?)\):",
            main,
            re.S,
        )
        self.assertIsNotNone(list_route)
        self.assertNotIn("Depends(get_current_user)", list_route.group(1))

        detail_route = re.search(
            r'@app\.post\("/public/scenarios/detail", response_model=PublicScenarioDetailOut\)\s*'
            r"def get_public_scenario_detail\((.*?)\):",
            main,
            re.S,
        )
        self.assertIsNotNone(detail_route)
        self.assertNotIn("Depends(get_current_user)", detail_route.group(1))

        self.assertIn('@app.post("/scenarios", status_code=201)', main)
        self.assertIn("def create_scenario(req: ScenarioCreate, user: CurrentUser = Depends(get_current_user))", main)

    def test_public_schemas_define_stable_response_shape(self):
        schemas = (ROOT / "app" / "schemas.py").read_text(encoding="utf-8")

        for name in (
            "PublicScenarioListIn",
            "PublicScenarioSummary",
            "PublicScenarioListOut",
            "PublicScenarioDetailIn",
            "PublicAgentConfig",
            "PublicScenarioDetailOut",
        ):
            self.assertIn(f"class {name}(BaseModel):", schemas)

        self.assertIn("scenarios: List[PublicScenarioSummary]", schemas)
        self.assertIn("total: int", schemas)
        self.assertIn("planner: PublicAgentConfig", schemas)
        self.assertIn("experts: List[PublicAgentConfig]", schemas)
        self.assertIn("backstory: str", schemas)
        self.assertNotIn("backstory_extra: str", schemas)
        self.assertNotIn("routing_rules", schemas)

    def test_public_store_uses_active_runtime_configuration(self):
        store = (ROOT / "app" / "services" / "store.py").read_text(encoding="utf-8")

        self.assertIn("def list_public_scenarios():", store)
        self.assertIn("def get_public_scenario_detail(name):", store)
        self.assertIn("WHERE status='active'", store)
        self.assertIn("scenario_name=%s AND status='active'", store)
        self.assertIn("active_content", store)
        self.assertIn('runtime_content = agent.get("active_content")', store)
        self.assertIn("validate_agent_yaml_content(agent.get(\"agent_name\"), runtime_content)", store)
        self.assertIn("Scenario planner is required", store)
        self.assertIn("Scenario agents are not active:", store)
        self.assertIn("智能体配置校验失败", store)
        self.assertIn("def validate_agent_yaml_content(agent_name, content):", store)
        self.assertIn("配置顶层必须是对象", store)
        self.assertIn("配置字段 role 必填", store)
        self.assertIn("配置字段 goal 必填", store)
        self.assertIn("配置字段 skills 必须是字符串数组", store)
        self.assertIn("validate_agent_yaml_content(req.agent_name, req.content)", store)
        self.assertIn('"backstory":', store)
        self.assertIn('parsed.get("backstory") or parsed.get("backstory_extra")', store)
        self.assertNotIn('"routing_rules":', store)

    def test_agent_activation_routes_translate_invalid_yaml_to_400(self):
        main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")

        for call in (
            'store.set_agent_status(agent_id, "active", user)',
            "store.activate_agent_version(agent_id, version_id, user)",
            "store.rollback_agent(agent_id, req.version_id, user)",
        ):
            route_block = re.search(
                r"try:\s+.*?"
                + re.escape(call)
                + r".*?except ValueError as exc:\s+"
                + re.escape('raise HTTPException(status_code=400, detail=str(exc)) from exc'),
                main,
                re.S,
            )
            self.assertIsNotNone(route_block)

    def test_api_documentation_exists_for_public_runtime_endpoints(self):
        doc = (ROOT / "docs" / "api" / "public-scenario-runtime-apis.md").read_text(encoding="utf-8")

        self.assertIn("POST /public/scenarios", doc)
        self.assertIn("POST /public/scenarios/detail", doc)
        self.assertIn("无需鉴权", doc)
        self.assertIn("只返回已激活场景", doc)
        self.assertIn("active_content", doc)
        self.assertIn("不返回 routing_rules", doc)


if __name__ == "__main__":
    unittest.main()
