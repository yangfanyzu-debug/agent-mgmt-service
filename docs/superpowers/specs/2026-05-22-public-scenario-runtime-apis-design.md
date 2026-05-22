# Public Scenario Runtime APIs Design

## Goal

Add two unauthenticated backend APIs for runtime intent recognition and scenario execution lookup:

- `POST /public/scenarios`
- `POST /public/scenarios/detail`

These APIs are separate from the authenticated management APIs. They expose only active, runtime-ready scenario configuration.

## Existing Context

The current service already has authenticated management routes:

- `GET /scenarios` lists scenarios for the UI.
- `POST /scenarios` creates a scenario.
- Scenario rows store `scenario_name`, `description`, `sub_type_hint`, `keyword_hint`, `skill_selector_dims`, `related_agents`, `status`, and generated YAML `content`.
- Agent rows store mutable content plus active-version fields: `active_version`, `active_content`, and `active_tags`.

Because `POST /scenarios` is already used for creation, the new public list API must not reuse that path.

## API Contract

### `POST /public/scenarios`

Request body:

```json
{}
```

Response:

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

Rules:

- Return only `agent_mgmt_scenario.status = 'active'`.
- Sort by `updated_at DESC`.
- Map `scenario_name` to `name`.
- Return empty strings for nullable text fields.
- Do not require authentication.

### `POST /public/scenarios/detail`

Request body:

```json
{
  "name": "alert_analysis"
}
```

Response:

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

Rules:

- Lookup by `scenario_name` and require `status = 'active'`.
- Parse `skill_selector_dims` as JSON. Invalid or empty values become `[]`.
- Parse `related_agents` as JSON.
- Require a planner name.
- Include enabled experts from `related_agents.experts`; an empty expert list is allowed.
- All referenced agents must exist and have `status = 'active'`.
- Use `active_content || content` as the agent configuration source.
- Parse agent YAML into `role`, `goal`, `backstory_extra`, and `skills`.
- Missing `role`, `goal`, or `backstory_extra` returns `""`.
- Missing `skills` returns `[]`.
- Do not return `routing_rules`.
- Do not require authentication.

## Error Handling

The detail API is strict. It should return clear errors instead of partial configuration.

- Scenario missing or inactive: `404`, detail `Scenario not found`.
- Missing planner in `related_agents`: `400`, detail `Scenario planner is required`.
- Referenced agent missing or inactive: `400`, detail `Scenario agents are not active: name1, name2`.
- Agent has no usable content: `400`, detail `Invalid agent config: agent_name`.
- Agent YAML cannot be parsed into a mapping: `400`, detail `Invalid agent config: agent_name`.

Missing optional agent fields are not errors because the response shape stays stable with empty strings and arrays.

## Implementation Shape

Add public request and response schemas in `app/schemas.py`:

- `PublicScenarioListIn`
- `PublicScenarioSummary`
- `PublicScenarioListOut`
- `PublicScenarioDetailIn`
- `PublicAgentConfig`
- `PublicScenarioDetailOut`

Add store functions in `app/services/store.py`:

- `list_public_scenarios()`
- `get_public_scenario_detail(name)`

Use small private helpers for parsing:

- JSON list/object parsing with defaults.
- Agent YAML parsing using the existing `yaml` dependency.
- Agent lookup by name for planner plus enabled experts.

Add routes in `app/main.py`:

- `@app.post("/public/scenarios", response_model=PublicScenarioListOut)`
- `@app.post("/public/scenarios/detail", response_model=PublicScenarioDetailOut)`

These routes must not accept `CurrentUser` and must not use `Depends(get_current_user)`.

## Testing

Add contract tests covering:

- Both public routes exist and do not contain `Depends(get_current_user)`.
- Existing authenticated `POST /scenarios` creation route remains in place.
- Public list uses `status='active'`.
- Detail lookup uses `status='active'`.
- Detail uses `active_content` before falling back to `content`.
- Detail returns `backstory_extra` and does not return `routing_rules`.
- Strict error strings for missing planner, inactive/missing agents, and invalid agent config are present.

Run:

```bash
python3 -m unittest discover -s tests
```

## Deployment

After implementation and tests:

1. Sync backend code to `/opt/agent-mgmt-service` on `43.135.134.42`.
2. Restart the service with `/opt/agent-mgmt-service/start.sh restart`.
3. Verify without authentication:

```bash
curl -fsS -X POST http://43.135.134.42:8300/public/scenarios -H 'Content-Type: application/json' -d '{}'
curl -fsS -X POST http://43.135.134.42:8300/public/scenarios/detail -H 'Content-Type: application/json' -d '{"name":"alert_analysis"}'
```
