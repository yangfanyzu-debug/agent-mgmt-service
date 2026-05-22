# Public Scenario Runtime APIs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two unauthenticated public scenario runtime APIs and generate their interface documentation.

**Architecture:** Keep public runtime APIs separate from authenticated management APIs by using `/public/scenarios` paths and dedicated store functions. The detail endpoint strictly assembles active scenario configuration from active Agent versions, parsing Agent YAML into a stable response shape.

**Tech Stack:** FastAPI, Pydantic v1, PyMySQL, PyYAML, Python unittest contract tests, Markdown API docs.

---

## File Structure

- Modify `app/schemas.py`
  - Add public request and response models.
- Modify `app/services/store.py`
  - Add JSON/YAML helpers for public runtime output.
  - Add `list_public_scenarios()`.
  - Add `get_public_scenario_detail(name)`.
- Modify `app/main.py`
  - Import public schemas.
  - Add unauthenticated `POST /public/scenarios`.
  - Add unauthenticated `POST /public/scenarios/detail`.
- Create `tests/test_public_scenario_runtime_contract.py`
  - Contract tests for route auth, path separation, active-only filtering, active Agent content usage, output fields, and strict errors.
- Create `docs/api/public-scenario-runtime-apis.md`
  - User-facing API documentation for both public endpoints.

## Task 1: Public Runtime Contract Tests

**Files:**
- Create: `tests/test_public_scenario_runtime_contract.py`
- Test: `tests/test_public_scenario_runtime_contract.py`

- [ ] **Step 1: Add failing contract tests**

Create `tests/test_public_scenario_runtime_contract.py`:

```python
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
        self.assertIn("backstory_extra: str", schemas)
        self.assertNotIn("routing_rules", schemas)

    def test_public_store_uses_active_runtime_configuration(self):
        store = (ROOT / "app" / "services" / "store.py").read_text(encoding="utf-8")

        self.assertIn("def list_public_scenarios():", store)
        self.assertIn("def get_public_scenario_detail(name):", store)
        self.assertIn("WHERE status='active'", store)
        self.assertIn("scenario_name=%s AND status='active'", store)
        self.assertIn("active_content", store)
        self.assertIn("content = agent.get(\"active_content\") or agent.get(\"content\")", store)
        self.assertIn("Scenario planner is required", store)
        self.assertIn("Scenario agents are not active:", store)
        self.assertIn("Invalid agent config:", store)
        self.assertIn('"backstory_extra":', store)
        self.assertNotIn('"routing_rules":', store)

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
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python3 -m unittest tests/test_public_scenario_runtime_contract.py
```

Expected: `FAIL` or `ERROR` because schemas, routes, store functions, and docs do not exist yet.

## Task 2: Schemas And Routes

**Files:**
- Modify: `app/schemas.py`
- Modify: `app/main.py`
- Test: `tests/test_public_scenario_runtime_contract.py`

- [ ] **Step 1: Add public schemas**

Add these classes after `ScenarioUpdate` in `app/schemas.py`:

```python
class PublicScenarioListIn(BaseModel):
    pass


class PublicScenarioSummary(BaseModel):
    name: str
    description: str
    sub_type_hint: str
    keyword_hint: str


class PublicScenarioListOut(BaseModel):
    scenarios: List[PublicScenarioSummary]
    total: int


class PublicScenarioDetailIn(BaseModel):
    name: str


class PublicAgentConfig(BaseModel):
    name: str
    role: str
    goal: str
    backstory_extra: str
    skills: List[str]


class PublicScenarioDetailOut(BaseModel):
    name: str
    description: str
    sub_type_hint: str
    keyword_hint: str
    skill_selector_dims: List[str]
    planner: PublicAgentConfig
    experts: List[PublicAgentConfig]
```

- [ ] **Step 2: Import schemas in `app/main.py`**

Change the schema import block to include:

```python
    PublicScenarioDetailIn,
    PublicScenarioDetailOut,
    PublicScenarioListIn,
    PublicScenarioListOut,
```

- [ ] **Step 3: Add public routes before authenticated scenario routes**

Add these routes after `check_scenario_name` and before `@app.get("/scenarios")`:

```python
@app.post("/public/scenarios", response_model=PublicScenarioListOut)
def list_public_scenarios(_: PublicScenarioListIn):
    return store.list_public_scenarios()


@app.post("/public/scenarios/detail", response_model=PublicScenarioDetailOut)
def get_public_scenario_detail(req: PublicScenarioDetailIn):
    try:
        detail = store.get_public_scenario_detail(req.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not detail:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return detail
```

- [ ] **Step 4: Run focused test and observe remaining failures**

Run:

```bash
python3 -m unittest tests/test_public_scenario_runtime_contract.py
```

Expected: still fails because store functions and docs are missing.

## Task 3: Public Store Functions

**Files:**
- Modify: `app/services/store.py`
- Test: `tests/test_public_scenario_runtime_contract.py`

- [ ] **Step 1: Add YAML parsing helpers**

Add these helpers after `_normalize_agent_row(row)`:

```python
def _json_list(value):
    parsed = _json_loads(value, [])
    return parsed if isinstance(parsed, list) else []


def _json_object(value):
    parsed = _json_loads(value, {})
    return parsed if isinstance(parsed, dict) else {}


def _clean_string(value):
    return value if isinstance(value, str) else ""


def _normalize_skills(value):
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _parse_public_agent_config(agent):
    content = agent.get("active_content") or agent.get("content")
    if not content:
        raise ValueError("Invalid agent config: {}".format(agent.get("agent_name")))
    try:
        parsed = yaml.safe_load(content) or {}
    except yaml.YAMLError as exc:
        raise ValueError("Invalid agent config: {}".format(agent.get("agent_name"))) from exc
    if not isinstance(parsed, dict):
        raise ValueError("Invalid agent config: {}".format(agent.get("agent_name")))
    return {
        "name": agent.get("agent_name") or "",
        "role": _clean_string(parsed.get("role")),
        "goal": _clean_string(parsed.get("goal")),
        "backstory_extra": _clean_string(parsed.get("backstory_extra") or parsed.get("backstory")),
        "skills": _normalize_skills(parsed.get("skills")),
    }
```

- [ ] **Step 2: Add `list_public_scenarios()`**

Add this function before authenticated `list_scenarios(user, scope, status)`:

```python
def list_public_scenarios():
    with db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT scenario_name,description,sub_type_hint,keyword_hint
              FROM {SCENARIO_TABLE}
             WHERE status='active'
             ORDER BY updated_at DESC
            """
        )
        rows = cursor.fetchall()
    scenarios = []
    for row in rows:
        scenarios.append({
            "name": row["scenario_name"],
            "description": row.get("description") or "",
            "sub_type_hint": row.get("sub_type_hint") or "",
            "keyword_hint": row.get("keyword_hint") or "",
        })
    return {"scenarios": scenarios, "total": len(scenarios)}
```

- [ ] **Step 3: Add `get_public_scenario_detail(name)`**

Add this function after `list_public_scenarios()`:

```python
def get_public_scenario_detail(name):
    with db_cursor() as cursor:
        scenario = _select_one(
            cursor,
            f"SELECT * FROM {SCENARIO_TABLE} WHERE scenario_name=%s AND status='active'",
            (name,),
        )
        if not scenario:
            return None
        related = _json_object(scenario.get("related_agents"))
        planner_name = related.get("planner")
        if not planner_name:
            raise ValueError("Scenario planner is required")
        expert_names = [
            item.get("name")
            for item in related.get("experts", [])
            if isinstance(item, dict) and item.get("enabled", True) and item.get("name")
        ]
        names = [planner_name] + expert_names
        placeholders = ",".join(["%s"] * len(names))
        cursor.execute(
            f"SELECT * FROM {AGENT_TABLE} WHERE agent_name IN ({placeholders})",
            tuple(names),
        )
        agents = cursor.fetchall()

    agent_by_name = {agent["agent_name"]: _normalize_agent_row(agent) for agent in agents}
    missing_or_inactive = [
        agent_name
        for agent_name in names
        if agent_name not in agent_by_name or agent_by_name[agent_name].get("status") != "active"
    ]
    if missing_or_inactive:
        raise ValueError("Scenario agents are not active: {}".format(", ".join(missing_or_inactive)))

    return {
        "name": scenario["scenario_name"],
        "description": scenario.get("description") or "",
        "sub_type_hint": scenario.get("sub_type_hint") or "",
        "keyword_hint": scenario.get("keyword_hint") or "",
        "skill_selector_dims": _json_list(scenario.get("skill_selector_dims")),
        "planner": _parse_public_agent_config(agent_by_name[planner_name]),
        "experts": [_parse_public_agent_config(agent_by_name[expert_name]) for expert_name in expert_names],
    }
```

- [ ] **Step 4: Run focused contract test**

Run:

```bash
python3 -m unittest tests/test_public_scenario_runtime_contract.py
```

Expected: still fails only because API documentation is missing.

## Task 4: Interface Documentation

**Files:**
- Create: `docs/api/public-scenario-runtime-apis.md`
- Test: `tests/test_public_scenario_runtime_contract.py`

- [ ] **Step 1: Create API docs**

Create `docs/api/public-scenario-runtime-apis.md`:

```markdown
# Public Scenario Runtime APIs

这两个接口供意图识别和运行时获取场景配置使用，均无需鉴权。接口只返回已激活场景，并且详情中的 Agent 配置来自 Agent 的已激活版本字段 `active_content`，没有已激活版本内容时回退到 `content`。

## POST /public/scenarios

获取所有可用场景的名称和描述。

### Request

```json
{}
```

### Response 200

```json
{
  "scenarios": [
    {
      "name": "alert_analysis",
      "description": "告警根因分析多智能体",
      "sub_type_hint": "",
      "keyword_hint": ""
    }
  ],
  "total": 1
}
```

### 字段说明

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `scenarios[].name` | `str` | 场景名称 |
| `scenarios[].description` | `str` | 场景描述 |
| `scenarios[].sub_type_hint` | `str` | 子类型提示，辅助意图识别区分相似场景 |
| `scenarios[].keyword_hint` | `str` | 关键词提示 |
| `total` | `int` | 返回数量 |

## POST /public/scenarios/detail

获取指定场景完整配置，包含 Planner Agent 和所有启用的 Expert Agent 配置。不返回 routing_rules。

### Request

```json
{
  "name": "alert_analysis"
}
```

### Response 200

```json
{
  "name": "alert_analysis",
  "description": "告警根因分析多智能体",
  "sub_type_hint": "",
  "keyword_hint": "",
  "skill_selector_dims": [],
  "planner": {
    "name": "alert_planner",
    "role": "...",
    "goal": "...",
    "backstory_extra": "...",
    "skills": ["alert_sop_guide"]
  },
  "experts": [
    {
      "name": "es_expert_agent",
      "role": "...",
      "goal": "...",
      "backstory_extra": "",
      "skills": ["es_cluster_check"]
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `str` | 场景名称 |
| `description` | `str` | 场景描述 |
| `sub_type_hint` | `str` | 子类型提示 |
| `keyword_hint` | `str` | 关键词提示 |
| `skill_selector_dims` | `list[str]` | Skill 选择维度 |
| `planner.name` | `str` | Planner Agent 名称 |
| `planner.role` | `str` | Planner 角色定义 |
| `planner.goal` | `str` | Planner 目标描述 |
| `planner.backstory_extra` | `str` | Planner 背景补充 |
| `planner.skills` | `list[str]` | Planner 挂载的 Skill 名称列表 |
| `experts[].name` | `str` | Expert Agent 名称 |
| `experts[].role` | `str` | Expert 角色定义 |
| `experts[].goal` | `str` | Expert 目标描述 |
| `experts[].backstory_extra` | `str` | Expert 背景补充 |
| `experts[].skills` | `list[str]` | Expert 挂载的 Skill 名称列表 |

### 错误响应

| HTTP 状态 | detail | 说明 |
| --- | --- | --- |
| `404` | `Scenario not found` | 场景不存在或未激活 |
| `400` | `Scenario planner is required` | 场景没有配置 Planner |
| `400` | `Scenario agents are not active: name1, name2` | 关联 Agent 不存在或未激活 |
| `400` | `Invalid agent config: agent_name` | Agent 没有可用配置或 YAML 无法解析为对象 |

## curl 示例

```bash
curl -fsS -X POST http://43.135.134.42:8300/public/scenarios -H 'Content-Type: application/json' -d '{}'
curl -fsS -X POST http://43.135.134.42:8300/public/scenarios/detail -H 'Content-Type: application/json' -d '{"name":"alert_analysis"}'
```
```

- [ ] **Step 2: Run focused contract test**

Run:

```bash
python3 -m unittest tests/test_public_scenario_runtime_contract.py
```

Expected: `OK`.

## Task 5: Full Verification And Remote Deployment

**Files:**
- Verify: `app/main.py`
- Verify: `app/schemas.py`
- Verify: `app/services/store.py`
- Verify: `docs/api/public-scenario-runtime-apis.md`
- Deploy: `/opt/agent-mgmt-service`

- [ ] **Step 1: Run all tests**

Run:

```bash
python3 -m unittest discover -s tests
```

Expected: all tests pass.

- [ ] **Step 2: Sync backend files and docs to remote**

Run:

```bash
rsync -av app/main.py app/schemas.py app/services/store.py docs/api/public-scenario-runtime-apis.md tests/test_public_scenario_runtime_contract.py root@43.135.134.42:/opt/agent-mgmt-service/
```

Expected: files transfer successfully. If `rsync` is not available, use `scp` for each file to its matching remote path.

- [ ] **Step 3: Restart remote service**

Run:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'cd /opt/agent-mgmt-service && ./start.sh restart && ./start.sh status'
```

Expected: service status reports running.

- [ ] **Step 4: Verify public list endpoint without auth**

Run:

```bash
curl -fsS -X POST http://43.135.134.42:8300/public/scenarios -H 'Content-Type: application/json' -d '{}'
```

Expected: JSON with `scenarios` and `total`.

- [ ] **Step 5: Verify public detail endpoint without auth**

Use a scenario name from Step 4:

```bash
curl -fsS -X POST http://43.135.134.42:8300/public/scenarios/detail -H 'Content-Type: application/json' -d '{"name":"alert_analysis"}'
```

Expected: JSON with `planner`, `experts`, and no `routing_rules`, or a strict `400/404` if no active runtime-ready scenario exists.
