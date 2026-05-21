# Scenario Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Scenario card copy action that opens the existing create wizard prefilled from the source scenario's current configuration.

**Architecture:** This is a frontend-only change. The scenario card `更多` menu adds a `复制` command, the existing scenario wizard gets a copy mode, and saving continues to use `createScenario` so the backend creates a new draft scenario with `v1`.

**Tech Stack:** Vue 2 single-file component, Element UI dropdown/dialog controls, existing RuoYi request wrappers, Python unittest contract tests.

---

## File Structure

- Modify `/Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/src/views/agentMgmt/scenarios/index.vue`
  - Add `复制` to the scenario card `更多` menu.
  - Add copy mode state to the existing scenario wizard.
  - Add `openCopy(row)` to load source scenario details and prefill the form.
  - Route the `copy` dropdown command through `handleMore`.
- Modify `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_ruoyi_ui_scenario_agent_drawer_contract.py`
  - Add contract assertions for the copy menu, copy mode, copied fields, cleared name/id, and create-only save path.

## Task 1: Contract Test For Scenario Copy Flow

**Files:**
- Modify: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_ruoyi_ui_scenario_agent_drawer_contract.py`
- Test: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_ruoyi_ui_scenario_agent_drawer_contract.py`

- [ ] **Step 1: Add failing test assertions**

Add these assertions inside `test_quick_create_agent_drawer_requires_category_code`, after the existing drawer assertions:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m unittest tests/test_ruoyi_ui_scenario_agent_drawer_contract.py
```

Expected: `FAIL` because `command="copy"` and `openCopy(row)` do not exist yet.

## Task 2: Add Copy Mode To Scenario Wizard

**Files:**
- Modify: `/Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/src/views/agentMgmt/scenarios/index.vue`
- Test: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_ruoyi_ui_scenario_agent_drawer_contract.py`

- [ ] **Step 1: Add copy menu entry**

In the scenario card dropdown menu, change:

```vue
<el-dropdown-item command="versions">历史版本</el-dropdown-item>
<el-dropdown-item command="delete" :disabled="!row.can_edit || row.status === 'active'">删除</el-dropdown-item>
```

to:

```vue
<el-dropdown-item command="versions">历史版本</el-dropdown-item>
<el-dropdown-item command="copy">复制</el-dropdown-item>
<el-dropdown-item command="delete" :disabled="!row.can_edit || row.status === 'active'">删除</el-dropdown-item>
```

- [ ] **Step 2: Add copy state to the empty scenario form**

Change `emptyForm()` from:

```js
return {
  id: null,
  scenario_name: '',
  description: '',
  sub_type_hint: '',
  keyword_hint: '',
  skill_selector_dims: [],
  planner: '',
  experts: []
}
```

to:

```js
return {
  id: null,
  copySourceId: null,
  scenario_name: '',
  description: '',
  sub_type_hint: '',
  keyword_hint: '',
  skill_selector_dims: [],
  planner: '',
  experts: []
}
```

- [ ] **Step 3: Make the dialog title show copy mode**

Change `dialogTitle()` from:

```js
if (this.readonly) return '查看场景'
return this.form.id ? '编辑场景' : '新增场景'
```

to:

```js
if (this.readonly) return '查看场景'
if (this.form.id) return '编辑场景'
return this.form.copySourceId ? '复制场景' : '新增场景'
```

- [ ] **Step 4: Add `openCopy(row)`**

Add this method after `openEdit(row, readonly)`:

```js
async openCopy(row) {
  const data = await getScenario(row.id)
  const related = this.parseJson(data.related_agents, null)
  if (!related || typeof related !== 'object') {
    this.$message.warning('当前场景配置无法复制')
    return
  }
  this.readonly = false
  this.wizardStep = 0
  this.nameStatus = ''
  this.nameMessage = ''
  this.form = {
    ...this.emptyForm(),
    id: null,
    copySourceId: data.id,
    scenario_name: '',
    description: data.description || '',
    sub_type_hint: data.sub_type_hint || '',
    keyword_hint: data.keyword_hint || '',
    skill_selector_dims: this.parseJson(data.skill_selector_dims, []),
    planner: related.planner || '',
    experts: (related.experts || []).filter(item => item.enabled !== false).map(item => item.name)
  }
  this.dialogVisible = true
}
```

- [ ] **Step 5: Route the dropdown command**

Change `handleMore(command, row)` from:

```js
if (command === 'versions') this.openVersions(row)
if (command === 'delete') this.remove(row)
```

to:

```js
if (command === 'versions') this.openVersions(row)
if (command === 'copy') this.openCopy(row)
if (command === 'delete') this.remove(row)
```

- [ ] **Step 6: Run the focused contract test**

Run:

```bash
python3 -m unittest tests/test_ruoyi_ui_scenario_agent_drawer_contract.py
```

Expected: `OK`.

## Task 3: Full Verification And Deployment

**Files:**
- Verify: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_ruoyi_ui_scenario_agent_drawer_contract.py`
- Verify: `/Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/dist`
- Deploy source: `/opt/ruoyi-cloud-ops/source/ruoyi-ui/src/views/agentMgmt/scenarios/index.vue`
- Deploy static assets: `/opt/middleware-stack/data/nginx-html`

- [ ] **Step 1: Run all backend contract tests**

Run:

```bash
python3 -m unittest discover -s tests
```

Expected: all tests pass.

- [ ] **Step 2: Build the frontend**

Run:

```bash
npm run build:prod
```

from:

```bash
/Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui
```

Expected: build completes. Existing asset-size warnings are acceptable.

- [ ] **Step 3: Back up the remote frontend directory**

Run:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'ts=$(date +%Y%m%d%H%M%S); backup=/opt/middleware-stack/data/nginx-html-backups/ruoyi-ui-$ts; mkdir -p /opt/middleware-stack/data/nginx-html-backups; cp -a /opt/middleware-stack/data/nginx-html "$backup"; printf "%s\n" "$backup"'
```

Expected: prints a backup path under `/opt/middleware-stack/data/nginx-html-backups`.

- [ ] **Step 4: Sync source file**

Run:

```bash
scp -o BatchMode=yes -o StrictHostKeyChecking=no /Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/src/views/agentMgmt/scenarios/index.vue root@43.135.134.42:/opt/ruoyi-cloud-ops/source/ruoyi-ui/src/views/agentMgmt/scenarios/index.vue
```

Expected: exit code `0`.

- [ ] **Step 5: Deploy built static assets**

Run:

```bash
tar -C /Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/dist --no-xattrs -czf - . | ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'tmp=/tmp/ruoyi-ui-dist-scenario-copy.tgz; cat > $tmp; cd /opt/middleware-stack/data/nginx-html; rm -rf index.html index.html.gz favicon.ico robots.txt html static styles; tar -xzf $tmp; rm -f $tmp'
```

Expected: exit code `0`.

- [ ] **Step 6: Verify remote route and static content**

Run:

```bash
curl -I -sS http://43.135.134.42/agent-mgmt/scenarios
```

Expected: `HTTP/1.1 200 OK`.

Run:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'grep -n "command=\"copy\"\\|openCopy(row)\\|复制场景\\|当前场景配置无法复制" /opt/ruoyi-cloud-ops/source/ruoyi-ui/src/views/agentMgmt/scenarios/index.vue'
```

Expected: source lines showing the copy menu, `openCopy(row)`, copy title, and copy failure warning.

Run:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'grep -R -l "复制场景\\|当前场景配置无法复制" /opt/middleware-stack/data/nginx-html/static/js /opt/middleware-stack/data/nginx-html/static/css 2>/dev/null | head -20'
```

Expected: at least one static JS file path.

Run:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'test -d /opt/middleware-stack/data/nginx-html/dblens && test -d /opt/middleware-stack/data/nginx-html/skill-ide && printf "other-static-apps-present\n"'
```

Expected: `other-static-apps-present`.

## Self-Review

- Spec coverage: The plan covers the card menu entry, current scenario configuration source, cleared name, create wizard reuse, create API path, read-only copy allowance, error message, and tests.
- Placeholder scan: No deferred implementation notes remain.
- Type consistency: The planned fields use existing Vue form fields plus `copySourceId`; method names match the planned assertions and template command.
