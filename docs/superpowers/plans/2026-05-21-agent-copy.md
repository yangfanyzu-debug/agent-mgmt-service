# Agent Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an Agent card copy action that opens the existing create wizard prefilled from the source Agent's active configuration.

**Architecture:** This is a frontend-only change. The card menu adds a copy command, the existing wizard gets a copy mode, and saving continues to use `createAgent` so the backend creates a new draft Agent with `v1`.

**Tech Stack:** Vue 2 single-file component, Element UI dropdown/dialog controls, existing RuoYi request wrappers, Python unittest contract tests.

---

## File Structure

- Modify `/Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/src/views/agentMgmt/agents/index.vue`
  - Add `复制` to the card `更多` menu.
  - Add copy mode state to the existing create wizard.
  - Add `openCopy(row)` to load source Agent details and prefill the form from `active_content` / `active_tags`.
  - Route the `copy` dropdown command through `handleMore`.
- Modify `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_ruoyi_ui_agent_card_version_contract.py`
  - Add contract assertions for the copy menu, copy mode, active-field preference, cleared name/id, and create-only save path.

## Task 1: Contract Test For Copy Flow

**Files:**
- Modify: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_ruoyi_ui_agent_card_version_contract.py`
- Test: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_ruoyi_ui_agent_card_version_contract.py`

- [ ] **Step 1: Add failing test assertions**

Add these assertions inside `test_agent_card_activation_is_version_scoped_only`, after the existing version activation assertions:

```python
        self.assertIn('<el-dropdown-item command="copy">复制</el-dropdown-item>', source)
        self.assertIn("if (command === 'copy') this.openCopy(row)", source)
        self.assertIn("openCopy(row)", source)
        self.assertIn("return this.form.copySourceId ? '复制 Agent' : '新增 Agent'", source)
        self.assertIn("const content = data.active_content || data.content", source)
        self.assertIn("tags: data.active_tags || data.tags || ''", source)
        self.assertIn("agent_name: ''", source)
        self.assertIn("id: null", source)
        self.assertIn("copySourceId: data.id", source)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m unittest tests/test_ruoyi_ui_agent_card_version_contract.py
```

Expected: `FAIL` because `command="copy"` and `openCopy(row)` do not exist yet.

## Task 2: Add Copy Mode To Agent Wizard

**Files:**
- Modify: `/Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/src/views/agentMgmt/agents/index.vue`
- Test: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_ruoyi_ui_agent_card_version_contract.py`

- [ ] **Step 1: Add copy menu entry**

In the card dropdown menu, change:

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

- [ ] **Step 2: Add copy state to the empty form**

Change `emptyForm()` from:

```js
return { id: null, agent_name: '', type: 'expert', role: '', goal: '', backstory: '', skills: [], tags: '', content: '' }
```

to:

```js
return { id: null, copySourceId: null, agent_name: '', type: 'expert', role: '', goal: '', backstory: '', skills: [], tags: '', content: '' }
```

- [ ] **Step 3: Make the dialog title show copy mode**

Change `dialogTitle()` from:

```js
if (this.readonly) return '查看 Agent'
return this.form.id ? '编辑 Agent' : '新增 Agent'
```

to:

```js
if (this.readonly) return '查看 Agent'
if (this.form.id) return '编辑 Agent'
return this.form.copySourceId ? '复制 Agent' : '新增 Agent'
```

- [ ] **Step 4: Keep type locked during copy**

Change the type selector disabled bindings from:

```vue
:disabled="form.id || readonly"
```

to:

```vue
:disabled="form.id || form.copySourceId || readonly"
```

There are two type buttons, one for Expert and one for Planner. Update both.

- [ ] **Step 5: Guard type switching during copy**

Change `setAgentType(type)` from:

```js
if (this.form.id || this.readonly) return
this.form.type = type
```

to:

```js
if (this.form.id || this.form.copySourceId || this.readonly) return
this.form.type = type
```

- [ ] **Step 6: Add `openCopy(row)`**

Add this method after `openEdit(row, readonly)`:

```js
async openCopy(row) {
  const data = await getAgent(row.id)
  const content = data.active_content || data.content
  if (!content) {
    this.$message.warning('当前 Agent 没有可复制的生效配置')
    return
  }
  this.readonly = false
  this.wizardStep = 0
  this.nameStatus = ''
  this.nameMessage = ''
  this.newSkill = ''
  this.form = {
    ...this.emptyForm(),
    ...this.parseAgentYaml(content, data.type),
    id: null,
    copySourceId: data.id,
    agent_name: '',
    type: data.type,
    tags: data.active_tags || data.tags || '',
    content
  }
  this.dialogVisible = true
}
```

- [ ] **Step 7: Route the dropdown command**

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

- [ ] **Step 8: Run the focused contract test**

Run:

```bash
python3 -m unittest tests/test_ruoyi_ui_agent_card_version_contract.py
```

Expected: `OK`.

## Task 3: Full Verification And Deployment

**Files:**
- Verify: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_ruoyi_ui_agent_card_version_contract.py`
- Verify: `/Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/dist`
- Deploy source: `/opt/ruoyi-cloud-ops/source/ruoyi-ui/src/views/agentMgmt/agents/index.vue`
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
scp -o BatchMode=yes -o StrictHostKeyChecking=no /Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/src/views/agentMgmt/agents/index.vue root@43.135.134.42:/opt/ruoyi-cloud-ops/source/ruoyi-ui/src/views/agentMgmt/agents/index.vue
```

Expected: exit code `0`.

- [ ] **Step 5: Deploy built static assets**

Run:

```bash
tar -C /Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/dist --no-xattrs -czf - . | ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'tmp=/tmp/ruoyi-ui-dist-agent-copy.tgz; cat > $tmp; cd /opt/middleware-stack/data/nginx-html; rm -rf index.html index.html.gz favicon.ico robots.txt html static styles; tar -xzf $tmp; rm -f $tmp'
```

Expected: exit code `0`.

- [ ] **Step 6: Verify remote route and static content**

Run:

```bash
curl -I -sS http://43.135.134.42/agent-mgmt/agents
```

Expected: `HTTP/1.1 200 OK`.

Run:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'grep -n "command=\"copy\"\\|openCopy(row)\\|复制 Agent\\|active_content || data.content" /opt/ruoyi-cloud-ops/source/ruoyi-ui/src/views/agentMgmt/agents/index.vue'
```

Expected: source lines showing the copy menu, `openCopy(row)`, copy title, and active-content preference.

Run:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'grep -R -l "复制 Agent\\|当前 Agent 没有可复制的生效配置" /opt/middleware-stack/data/nginx-html/static/js /opt/middleware-stack/data/nginx-html/static/css 2>/dev/null | head -20'
```

Expected: at least one static JS file path.

Run:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'test -d /opt/middleware-stack/data/nginx-html/dblens && test -d /opt/middleware-stack/data/nginx-html/skill-ide && printf "other-static-apps-present\n"'
```

Expected: `other-static-apps-present`.

## Self-Review

- Spec coverage: The plan covers the card menu entry, active configuration source, cleared name, create wizard reuse, create API path, and tests.
- Placeholder scan: No `TBD`, `TODO`, or deferred implementation notes remain.
- Type consistency: The planned fields use existing Vue form fields plus `copySourceId`, and the method names match the planned assertions.
