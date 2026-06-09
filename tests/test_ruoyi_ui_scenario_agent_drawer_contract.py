from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
UI_ROOT_CANDIDATES = (
    ROOT.parent / "ruoyi-cloud-ops" / "ruoyi-ui",
    Path("/opt/ruoyi-cloud-ops/source/ruoyi-ui"),
)
UI_ROOT = next((path for path in UI_ROOT_CANDIDATES if path.exists()), UI_ROOT_CANDIDATES[0])
SCENARIOS_VIEW = UI_ROOT / "src" / "views" / "agentMgmt" / "scenarios" / "index.vue"


class RuoyiScenarioAgentDrawerContractTests(unittest.TestCase):
    def test_quick_create_agent_drawer_requires_category_code(self):
        source = SCENARIOS_VIEW.read_text(encoding="utf-8")

        self.assertIn("listAgentCategories", source)
        self.assertIn('v-model="drawerForm.tags"', source)
        self.assertIn("categoryOptions", source)
        self.assertIn("categoryProps", source)
        self.assertIn(':append-to-body="false"', source)
        self.assertIn('popper-class="agent-drawer-category-popper"', source)
        self.assertIn("agent-drawer-category-popper", source)
        self.assertIn("tags: ''", source)
        self.assertIn("请填写分类标签", source)
        self.assertIn("tags: this.drawerForm.tags", source)
        self.assertNotIn("tags: '自定义'", source)
        self.assertIn('<el-dropdown-item command="copy">复制</el-dropdown-item>', source)
        self.assertIn("if (command === 'copy') this.openCopy(row)", source)
        self.assertIn("openCopy(row)", source)
        self.assertIn("return this.form.copySourceId ? '复制场景' : '新增场景'", source)
        self.assertIn("copySourceId: null", source)
        self.assertIn("copySourceId: data.id", source)
        self.assertIn("scenario_name: ''", source)
        self.assertIn("id: null", source)
        self.assertIn("description: data.description || ''", source)
        self.assertIn("sub_type_hint: data.sub_type_hint || ''", source)
        self.assertIn("keyword_hint: data.keyword_hint || ''", source)
        self.assertIn("skill_selector_dims: this.parseJson(data.skill_selector_dims, [])", source)
        self.assertIn("planner: related.planner || ''", source)
        self.assertIn("experts: (related.experts || []).filter(item => item.enabled !== false).map(item => item.name)", source)
        self.assertIn("当前场景配置无法复制", source)

    def test_quick_create_agent_template_uses_standard_yaml_scalars(self):
        source = SCENARIOS_VIEW.read_text(encoding="utf-8")

        self.assertIn("Agent 配置 <span", source)
        self.assertIn(">YAML</span>", source)
        self.assertIn("'goal: |'", source)
        self.assertIn("'backstory: |'", source)
        self.assertIn("skills: []", source)
        self.assertNotIn("'goal: >'", source)
        self.assertNotIn("'backstory: >'", source)
        self.assertIn("标准格式：顶层包含 name、role、goal、backstory、skills", source)

    def test_quick_create_agent_normalizes_and_validates_pasted_yaml_before_save(self):
        source = SCENARIOS_VIEW.read_text(encoding="utf-8")

        self.assertIn("normalizeDrawerAgentYaml(content)", source)
        self.assertIn("readDrawerYamlField(raw, key)", source)
        self.assertIn("readDrawerIndentedYamlBlock(lines, startIndex)", source)
        self.assertIn("｜", source)
        self.assertIn("['>', '|', '｜', '&gt;', '&vert;']", source)
        self.assertIn("normalizedContent = this.normalizeDrawerAgentYaml(this.drawerForm.content)", source)
        self.assertIn("content: normalizedContent", source)
        self.assertIn("this.drawerForm.content = normalizedContent", source)
        self.assertIn("Agent 配置 YAML 中 goal 不能为空", source)
        self.assertIn("Agent 配置 YAML 中 role 不能为空", source)
        self.assertIn("Agent 配置 YAML 中 skills 必须是 YAML 数组", source)
        self.assertIn("goal: |", source)
        self.assertIn("backstory: |", source)


if __name__ == "__main__":
    unittest.main()
