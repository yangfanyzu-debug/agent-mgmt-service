# LLM Call Stats Design

## Goal

Add LLM call observability to Agent Management:

- Store per-call LLM details in a new `llm_call_log` table.
- Add `run_id` to `agent_mgmt_execution_log` so execution logs and LLM calls can be correlated.
- Expose read-only LLM statistics APIs.
- Add a RuoYi Agent Management menu page for LLM statistics.
- Insert one-time demo data into the remote test database after deployment.

This change does not add an LLM call write API. LLM callers will write directly to the database or use a later integration.

## Existing Context

The backend service already has:

- `agent_mgmt_execution_log` for execution logs.
- Public log query endpoints in `app/main.py`.
- Log query and stats functions in `app/services/store.py`.
- MySQL 5.7-compatible schema migrations without foreign keys or JSON columns.

The RuoYi frontend already has Agent Management pages under:

- `/agent-mgmt/agents`
- `/agent-mgmt/scenarios`
- `/agent-mgmt/logs`
- `/agent-mgmt/overview`

The original standalone page at `/Users/yangfan/Downloads/no_five_ai_development_20260601/frontend/agent_mgmt.html` includes an LLM statistics page with:

- Overall summary.
- Per-model and per-role tables.
- Recent failure records.
- Scenario/run-level aggregation.
- A run detail drawer.
- Links from `run_id` to execution log HTML.

## Database Design

Update the base migration `migrations/001_create_agent_mgmt_tables.sql` so fresh installs include the new schema.

Add table:

```sql
CREATE TABLE IF NOT EXISTS `llm_call_log` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `run_id` VARCHAR(36) NOT NULL COMMENT '请求唯一标识，关联同一次处理的所有调用',
  `scenario_name` VARCHAR(200) NOT NULL DEFAULT 'unknown' COMMENT '场景名称',
  `agent_role` VARCHAR(200) NOT NULL COMMENT '调用角色：意图识别/规划Agent/专家名/轮询预编译/轮询评估',
  `call_index` INT NOT NULL COMMENT '本次请求内的LLM调用序号',
  `model` VARCHAR(100) NOT NULL DEFAULT 'unknown' COMMENT '模型名称',
  `status` ENUM('success','failed') NOT NULL COMMENT '最终状态（重试耗尽仍失败=failed）',
  `latency_ms` INT DEFAULT NULL COMMENT '耗时毫秒（从首次发起到最终响应），失败时可能为NULL',
  `retry_count` INT NOT NULL DEFAULT 0 COMMENT '重试次数（0=一次成功）',
  `error_type` VARCHAR(50) DEFAULT NULL COMMENT '失败时的错误分类：rate_limit/network/other',
  `error_msg` VARCHAR(500) DEFAULT NULL COMMENT '失败时的错误信息',
  `input_tokens` INT DEFAULT NULL COMMENT '输入token数（模型返回时记录）',
  `output_tokens` INT DEFAULT NULL COMMENT '输出token数（模型返回时记录）',
  `extra_data` TEXT DEFAULT NULL COMMENT '附加数据JSON，如 {"system_id":"app01","alert_key":"A-001"}',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '调用时间',
  PRIMARY KEY (`id`),
  KEY ix_llm_call_log_run_id (`run_id`),
  KEY ix_llm_call_log_scenario (`scenario_name`),
  KEY ix_llm_call_log_model (`model`),
  KEY ix_llm_call_log_status (`status`),
  KEY ix_llm_call_log_created_at (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LLM 调用明细表';
```

Update `agent_mgmt_execution_log`:

- Add nullable `run_id VARCHAR(36) DEFAULT NULL` after `id`.
- Add index `ix_agent_mgmt_execution_log_run_id (run_id)`.

Add incremental migration `migrations/005_llm_call_logs.sql` for existing deployments:

- `CREATE TABLE IF NOT EXISTS llm_call_log`.
- Add `agent_mgmt_execution_log.run_id` only if missing.
- Add `ix_agent_mgmt_execution_log_run_id` only if missing.
- Add `llm_call_log.extra_data` only if the table already existed without it.

The migration must remain MySQL 5.7-compatible. Do not use JSON columns, CTEs, or `IF NOT EXISTS` column syntax unsupported by MySQL 5.7. Use `INFORMATION_SCHEMA` checks plus prepared statements where needed.

## Backend API Design

Add read-only APIs under the existing Agent Management backend. These routes match the current log-query style and do not add `Depends(get_current_user)` in the FastAPI service. When called through RuoYi, the Gateway still applies token checks.

### `GET /llm-stats/summary`

Query parameters:

- `days`: integer, default `7`, allowed range `1..30`.

Returns:

```json
{
  "total_calls": 120,
  "total_failures": 4,
  "success_rate": "96.7%",
  "avg_latency_ms": 1850,
  "by_model": {
    "gpt-4.1": {
      "calls": 80,
      "failures": 2,
      "avg_latency_ms": 2100,
      "total_input_tokens": 120000,
      "total_output_tokens": 32000
    }
  },
  "by_role": {
    "规划Agent": {
      "calls": 30,
      "failures": 1,
      "avg_latency_ms": 2400
    }
  }
}
```

Calculations:

- Filter by `created_at >= NOW() - INTERVAL days DAY`.
- `success_rate = (total_calls - total_failures) / total_calls`.
- Average latency ignores `NULL` latency rows.
- Token sums treat `NULL` as `0`.

### `GET /llm-stats/failures`

Query parameters:

- `days`: default `7`, allowed range `1..30`.
- `page`: default `1`.
- `page_size`: default `50`, max `100`.

Returns paginated failed rows:

```json
{
  "total": 2,
  "page": 1,
  "page_size": 50,
  "items": [
    {
      "id": 10,
      "run_id": "uuid",
      "scenario_name": "alert_analysis",
      "agent_role": "规划Agent",
      "model": "gpt-4.1",
      "retry_count": 2,
      "error_type": "rate_limit",
      "error_msg": "quota exceeded",
      "created_at": "2026-06-03 10:00:00"
    }
  ]
}
```

### `GET /llm-stats/by-run/{run_id}`

Returns call detail and run-level summary:

```json
{
  "run_id": "uuid",
  "scenario_name": "alert_analysis",
  "total_calls": 5,
  "total_failures": 1,
  "total_latency_ms": 8800,
  "calls": [
    {
      "call_index": 1,
      "agent_role": "意图识别",
      "model": "gpt-4.1-mini",
      "status": "success",
      "latency_ms": 900,
      "retry_count": 0,
      "error_type": null,
      "error_msg": null,
      "input_tokens": 1000,
      "output_tokens": 200,
      "created_at": "2026-06-03 10:00:00"
    }
  ]
}
```

Rules:

- Sort calls by `call_index ASC, id ASC`.
- If no calls exist, return an empty `calls` list and zero summary values.
- `total_latency_ms` sums non-null latency values.

### `GET /llm-stats/by-scenario`

Query parameters:

- `days`: default `7`, allowed range `1..30`.
- `only_failures`: boolean, default `false`.
- `scenario_name`: optional exact match.
- `keyword`: optional text match against `run_id`, `scenario_name`, and `extra_data`.

Returns one row per `run_id`:

```json
[
  {
    "run_id": "uuid",
    "scenario_name": "alert_analysis",
    "created_at": "2026-06-03 10:00:00",
    "total_calls": 5,
    "failures": 1,
    "success_rate": "80.0%",
    "avg_latency_ms": 1760,
    "total_latency_ms": 8800,
    "extra_data": {
      "system_id": "app01",
      "alert_key": "A-001"
    }
  }
]
```

Rules:

- Group by `run_id`.
- Use the earliest `created_at` as row time.
- Use the first non-empty `scenario_name`.
- Parse the first non-empty valid JSON `extra_data`; invalid JSON becomes `{}`.
- `only_failures=true` keeps groups with at least one failed call.
- `keyword` uses SQL `LIKE` against `run_id`, `scenario_name`, and `extra_data`.

### `GET /logs/by-run/{run_id}/html`

Returns execution log HTML linked to a run:

- Find the newest row in `agent_mgmt_execution_log` where `run_id=%s`.
- Return `html_content` as `HTMLResponse`.
- If no row or no HTML exists, return `404`.

## Frontend Design

Add a fifth Agent Management menu page:

- Menu name: `LLM 统计`
- Route: `/agent-mgmt/llm-stats`
- Component: `/Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/src/views/agentMgmt/llmStats/index.vue`
- API methods: `/Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/src/api/agentMgmt/index.js`

The page should use Vue 2 and Element UI patterns already used by the Agent Management pages. Do not embed the original standalone HTML directly.

### Page Structure

Top bar:

- Title: `LLM 调用统计`
- Subtitle: `模型资源使用与故障分析`
- Time range select: 1, 3, 7, 14, 30 days.
- Refresh button.

Tabs:

- `整体统计`
- `场景维度`

Overall tab:

- Summary cards:
  - Total calls.
  - Success rate.
  - Failure count.
  - Average latency.
- Table: per-model distribution.
- Table: per-role distribution.
- Table: recent failure records.
- Click failure `run_id` to open the LLM call detail drawer.

Scenario tab:

- Filters:
  - All requests / only failed requests.
  - Scenario exact filter.
  - Keyword filter for alert key, system id, or raw `extra_data`.
  - Exact `run_id` input that opens the detail drawer.
- Table grouped by run:
  - time
  - scenario
  - related extra info
  - run_id
  - call count
  - failures
  - success rate
  - average latency
  - total latency
  - status badge
- Click `run_id` to open execution log HTML.
- Click call count to open LLM call detail drawer.

Drawer:

- Title includes `run_id`.
- Summary shows scenario, call count, failure count, and total latency.
- Table lists call index, role, model, status, latency, retry count, error, input tokens, output tokens, and created time.

Empty and error states:

- Use `el-empty` for no data.
- Show concise inline failure text for API loading failures.
- Keep the layout usable when the demo database has no records.

## Demo Data

After deploying to the remote test server, insert demo data directly into the remote database once. Do not add demo rows to migrations.

Demo data should include:

- 3 to 5 `run_id` values.
- Timestamps within the last 7 days.
- At least two scenario names, such as `alert_analysis` and `log_diagnosis`.
- Multiple models:
  - `gpt-4.1`
  - `gpt-4.1-mini`
  - `deepseek-chat`
- Multiple roles:
  - `意图识别`
  - `规划Agent`
  - `es_expert_agent`
  - `hbase_expert_agent`
- Success and failed calls.
- `retry_count > 0`.
- `error_type` values:
  - `rate_limit`
  - `network`
  - `other`
- `extra_data` with `system_id`, `alert_key`, and optionally `alert_source`.
- Matching `agent_mgmt_execution_log` rows with the same `run_id` and usable `html_content`.

The demo insert should be executed manually during deployment. It should be idempotent enough for the remote test database by deleting rows for a fixed demo run-id prefix or checking fixed run IDs before insert.

## Testing

Backend contract tests:

- Base migration defines `llm_call_log`.
- Incremental migration exists and is MySQL 5.7-compatible.
- `agent_mgmt_execution_log` includes `run_id` and an index.
- FastAPI exposes all LLM stats routes.
- LLM stats routes do not use `Depends(get_current_user)`.
- Store functions exist:
  - `llm_stats_summary(days)`
  - `llm_stats_failures(days, page, page_size)`
  - `llm_stats_by_run(run_id)`
  - `llm_stats_by_scenario(days, only_failures, scenario_name, keyword)`
  - `get_log_html_by_run(run_id)`
- Store uses `llm_call_log`, groups by `run_id`, and parses `extra_data`.

Frontend contract tests:

- API wrapper exports all LLM stats methods.
- New `llmStats/index.vue` exists.
- The page contains the two expected tabs.
- It calls the new API wrapper methods.
- It has the run detail drawer.
- It can open log HTML by run ID.

Verification commands:

```bash
python3 -m unittest discover -s tests
npm run build:prod
```

Deployment verification:

- Run migration on remote database.
- Restart backend service.
- Build and deploy RuoYi UI.
- Insert remote demo data.
- Verify:

```bash
curl -fsS 'http://43.135.134.42/prod-api/agent-mgmt-api/llm-stats/summary?days=7'
curl -fsS 'http://43.135.134.42/prod-api/agent-mgmt-api/llm-stats/failures?days=7&page=1&page_size=5'
curl -fsS 'http://43.135.134.42/prod-api/agent-mgmt-api/llm-stats/by-scenario?days=7'
```

Then manually check `/agent-mgmt/llm-stats` in the browser.
