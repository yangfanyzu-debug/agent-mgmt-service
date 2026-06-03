from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentYamlContractTests(unittest.TestCase):
    def test_store_validates_agent_yaml_before_persisting(self):
        store = (ROOT / "app" / "services" / "store.py").read_text(encoding="utf-8")

        self.assertIn("def validate_agent_yaml_content(agent_name, content):", store)
        self.assertIn("yaml.safe_load(content)", store)
        self.assertIn("智能体配置校验失败", store)
        self.assertIn("配置内容无法解析，请检查格式", store)
        self.assertIn("配置顶层必须是对象", store)
        self.assertIn("配置字段 role 必填", store)
        self.assertIn("配置字段 goal 必填", store)
        self.assertIn("配置字段 skills 必须是字符串数组", store)
        self.assertIn("配置中的 name 必须与智能体名称一致", store)
        self.assertNotIn("Invalid agent config:", store)
        self.assertNotIn("Agent YAML cannot be parsed", store)
        self.assertIn("validate_agent_yaml_content(req.agent_name, req.content)", store)
        self.assertIn("validate_agent_yaml_content(row[\"agent_name\"], req.content)", store)
        self.assertIn("validate_agent_yaml_content(row[\"agent_name\"], version[\"content\"])", store)

    def test_api_docs_define_standard_agent_yaml_shape(self):
        doc = (ROOT / "docs" / "api" / "public-scenario-runtime-apis.md").read_text(encoding="utf-8")

        self.assertIn("Agent YAML 标准格式", doc)
        self.assertIn("name: alert_planner", doc)
        self.assertIn("role: 规划专家", doc)
        self.assertIn("goal: |", doc)
        self.assertIn("backstory: |", doc)
        self.assertIn("skills:", doc)
        self.assertIn("skills` 必须是字符串数组", doc)
        self.assertIn("标准字段统一使用 `backstory`", doc)
        self.assertIn("智能体配置校验失败：agent_name", doc)
        self.assertNotIn("Invalid agent config: agent_name", doc)


if __name__ == "__main__":
    unittest.main()
