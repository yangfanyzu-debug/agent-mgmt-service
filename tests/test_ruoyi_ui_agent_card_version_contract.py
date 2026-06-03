from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
UI_ROOT = ROOT.parent / "ruoyi-cloud-ops" / "ruoyi-ui"
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


if __name__ == "__main__":
    unittest.main()
