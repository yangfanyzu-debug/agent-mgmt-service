from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
UI_ROOT_CANDIDATES = (
    ROOT.parent / "ruoyi-cloud-ops" / "ruoyi-ui",
    Path("/opt/ruoyi-cloud-ops/source/ruoyi-ui"),
)
UI_ROOT = next((path for path in UI_ROOT_CANDIDATES if path.exists()), UI_ROOT_CANDIDATES[0])
AGENTS_VIEW = UI_ROOT / "src" / "views" / "agentMgmt" / "agents" / "index.vue"


class RuoyiAgentCardVersionContractTests(unittest.TestCase):
    def test_agent_card_activation_is_version_scoped_only(self):
        source = AGENTS_VIEW.read_text(encoding="utf-8")

        self.assertNotIn("@click=\"activate(row)\"", source)
        self.assertNotRegex(source, r"\bactivateAgent\s*,")
        self.assertNotRegex(source, r"async\s+activate\s*\(row\)")
        self.assertIn("@click=\"activateVersion(version)\"", source)
        self.assertIn("activateAgentVersion", source)
        self.assertIn("激活此版本", source)
        self.assertNotIn("设为生效", source)
        self.assertIn("pendingVersion(row)", source)
        self.assertIn("displayVersion(version.version)", source)
        self.assertIn("<span>激活版本</span>", source)
        self.assertIn("<span>待激活版本</span>", source)
        self.assertIn("{{ pendingVersion(row) }}", source)
        self.assertNotIn("<span>最新版本</span>", source)
        self.assertNotIn("生效版本", source)
        self.assertNotIn("待生效版本", source)
        self.assertIn("isVersionActivationDisabled(version)", source)
        self.assertIn("versionTarget.status === 'active'", source)
        self.assertIn("versionTarget.status === 'inactive'", source)
        self.assertIn('<el-dropdown-item command="copy">复制</el-dropdown-item>', source)
        self.assertIn("if (command === 'copy') this.openCopy(row)", source)
        self.assertIn("openCopy(row)", source)
        self.assertIn("return this.form.copySourceId ? '复制 Agent' : '新增 Agent'", source)
        self.assertIn("const content = data.active_content || data.content", source)
        self.assertIn("tags: data.active_tags || data.tags || ''", source)
        self.assertIn("agent_name: ''", source)
        self.assertIn("id: null", source)
        self.assertIn("copySourceId: data.id", source)
        self.assertIn("formatYamlValue(key, value)", source)
        self.assertIn("return [`${key}: ${text}`]", source)
        self.assertIn("return [`${key}: \"\"`]", source)
        self.assertIn("return [`${key}: |`", source)
        self.assertIn("goal: this.formatYamlValue('goal', data.goal)", source)
        self.assertIn("backstory: this.formatYamlValue('backstory', data.backstory)", source)
        self.assertNotIn("goal: >", source)
        self.assertNotIn("backstory: >", source)
        self.assertNotIn("const goalOp", source)
        form_step = re.search(
            r"<div v-show=\"wizardStep === 0\" class=\"wizard-left\">([\s\S]*?)<div v-show=\"wizardStep === 1\"",
            source,
        )
        self.assertIsNotNone(form_step)
        self.assertLess(form_step.group(1).index("分类标签"), form_step.group(1).index("Role"))
        self.assertLess(form_step.group(1).index("分类标签"), form_step.group(1).index("Goal"))

        confirm_step = re.search(
            r"<div v-show=\"wizardStep === 1\" class=\"wizard-left\">([\s\S]*?)<div class=\"wizard-right\">",
            source,
        )
        self.assertIsNotNone(confirm_step)
        self.assertIn("<div class=\"sum-lbl\">Goal</div>", confirm_step.group(1))
        self.assertIn("{{ form.goal || '-' }}", confirm_step.group(1))

        version_dialog = re.search(
            r"<el-dialog title=\"历史版本\"[\s\S]*?</el-dialog>",
            source,
        )
        self.assertIsNotNone(version_dialog)
        self.assertIn("@click=\"activateVersion(version)\"", version_dialog.group(0))
        self.assertIn(':disabled="isVersionActivationDisabled(version)"', version_dialog.group(0))
        self.assertNotIn(':disabled="isVersionActive(version)', version_dialog.group(0))

    def test_agent_card_status_text_avoids_activation_wording(self):
        source = AGENTS_VIEW.read_text(encoding="utf-8")

        self.assertIn("statusText(status)", source)
        self.assertIn("active: '可用'", source)
        self.assertNotIn("active: '已激活'", source)
        self.assertIn("this.$message.success(`Agent 已激活版本 ${version.version}`)", source)
        self.assertNotIn("生效", source)

    def test_agent_yaml_parser_accepts_indented_multiline_goal_and_backstory(self):
        source = AGENTS_VIEW.read_text(encoding="utf-8")

        self.assertIn("readYamlField(raw, key)", source)
        self.assertIn("readIndentedYamlBlock(lines, startIndex)", source)
        self.assertIn("goal: this.readYamlField(raw, 'goal')", source)
        self.assertIn("backstory: this.readYamlField(raw, 'backstory')", source)
        self.assertIn("line.match(/^([A-Za-z_][A-Za-z0-9_-]*):/", source)
        self.assertIn("return this.cleanYamlFieldValue(block.lines.join('\\n'))", source)
        self.assertIn("｜", source)
        self.assertIn("['>', '|', '｜', '&gt;', '&vert;']", source)


if __name__ == "__main__":
    unittest.main()
