# LLM Call Stats Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add LLM call statistics storage, read-only stats APIs, a RuoYi Agent Management LLM statistics page, and one-time remote demo data.

**Architecture:** The backend adds MySQL 5.7-compatible schema changes plus read-only aggregation functions over `llm_call_log`, keeping the service-level routes unauthenticated like existing log query routes. The frontend adds one new Agent Management page (`/agent-mgmt/llm-stats`) built with Vue 2 and Element UI, consuming the new API wrapper methods. Deployment runs the migration, registers the RuoYi dynamic menu, restarts the backend, builds/deploys the RuoYi UI, and inserts demo rows only in the remote test database.

**Tech Stack:** FastAPI, PyMySQL, MySQL 5.7 SQL, Python unittest contract tests, Vue 2, Element UI, RuoYi request wrapper, Nginx/RuoYi Gateway remote deployment.

---

## File Structure

- Modify `/Users/yangfan/workspace/codex/agent-mgmt-service/migrations/001_create_agent_mgmt_tables.sql`
  - Add `llm_call_log`.
  - Add `run_id` and `ix_agent_mgmt_execution_log_run_id` to `agent_mgmt_execution_log`.
- Create `/Users/yangfan/workspace/codex/agent-mgmt-service/migrations/005_llm_call_logs.sql`
  - Incremental migration for deployed databases.
- Modify `/Users/yangfan/workspace/codex/agent-mgmt-service/app/services/store.py`
  - Add LLM stats aggregation functions.
  - Add execution-log lookup by `run_id`.
- Modify `/Users/yangfan/workspace/codex/agent-mgmt-service/app/main.py`
  - Add LLM stats routes and log HTML route by `run_id`.
- Create `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_llm_call_stats_contract.py`
  - Backend schema/API/store contract coverage.
- Modify `/Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/src/api/agentMgmt/index.js`
  - Add LLM stats API wrapper methods.
- Create `/Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/src/views/agentMgmt/llmStats/index.vue`
  - New LLM statistics page.
- Create `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_ruoyi_ui_llm_stats_contract.py`
  - Frontend source contract coverage from the backend test suite.
- Remote RuoYi `sys_menu` data
  - Ensure an Agent Management child menu named `LLM 统计` points to component `agentMgmt/llmStats/index`.

## Task 1: Backend Contract Tests

**Files:**
- Create: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_llm_call_stats_contract.py`
- Test: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_llm_call_stats_contract.py`

- [ ] **Step 1: Add failing backend contract tests**

Create `tests/test_llm_call_stats_contract.py`:

```python
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LlmCallStatsContractTests(unittest.TestCase):
    def test_schema_defines_llm_call_log_and_execution_run_id(self):
        sql = (ROOT / "migrations" / "001_create_agent_mgmt_tables.sql").read_text(encoding="utf-8").lower()

        self.assertIn("create table if not exists `llm_call_log`", sql)
        for column in (
            "`run_id` varchar(36) not null",
            "`scenario_name` varchar(200) not null default 'unknown'",
            "`agent_role` varchar(200) not null",
            "`call_index` int not null",
            "`model` varchar(100) not null default 'unknown'",
            "`status` enum('success','failed') not null",
            "`latency_ms` int default null",
            "`retry_count` int not null default 0",
            "`error_type` varchar(50) default null",
            "`error_msg` varchar(500) default null",
            "`input_tokens` int default null",
            "`output_tokens` int default null",
            "`extra_data` text default null",
        ):
            self.assertIn(column, sql)
        for index in (
            "key ix_llm_call_log_run_id (`run_id`)",
            "key ix_llm_call_log_scenario (`scenario_name`)",
            "key ix_llm_call_log_model (`model`)",
            "key ix_llm_call_log_status (`status`)",
            "key ix_llm_call_log_created_at (`created_at`)",
        ):
            self.assertIn(index, sql)

        execution_block = re.search(r"create table if not exists `agent_mgmt_execution_log` \((.*?)\) engine=", sql, re.S)
        self.assertIsNotNone(execution_block)
        self.assertIn("`run_id` varchar(36) default null", execution_block.group(1))
        self.assertIn("key ix_agent_mgmt_execution_log_run_id (`run_id`)", execution_block.group(1))

    def test_incremental_migration_is_mysql57_safe(self):
        path = ROOT / "migrations" / "005_llm_call_logs.sql"
        self.assertTrue(path.exists())
        sql = path.read_text(encoding="utf-8").lower()

        self.assertIn("create table if not exists `llm_call_log`", sql)
        self.assertIn("information_schema.columns", sql)
        self.assertIn("information_schema.statistics", sql)
        self.assertIn("alter table `agent_mgmt_execution_log` add column `run_id`", sql)
        self.assertIn("alter table `agent_mgmt_execution_log` add index `ix_agent_mgmt_execution_log_run_id`", sql)
        self.assertIn("alter table `llm_call_log` add column `extra_data`", sql)
        self.assertNotIn("add column if not exists", sql)
        self.assertNotIn("json", sql)
        self.assertNotIn(" with ", sql)

    def test_routes_are_read_only_and_match_log_auth_style(self):
        main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")

        routes = [
            (r'@app\.get\("/llm-stats/summary"\)\s*def llm_stats_summary\((.*?)\):', "llm_stats_summary"),
            (r'@app\.get\("/llm-stats/failures", response_model=ExecutionLogPage\)\s*def llm_stats_failures\((.*?)\):', "llm_stats_failures"),
            (r'@app\.get\("/llm-stats/by-run/\{run_id\}"\)\s*def llm_stats_by_run\((.*?)\):', "llm_stats_by_run"),
            (r'@app\.get\("/llm-stats/by-scenario"\)\s*def llm_stats_by_scenario\((.*?)\):', "llm_stats_by_scenario"),
            (r'@app\.get\("/logs/by-run/\{run_id\}/html", response_class=HTMLResponse\)\s*def get_log_html_by_run\((.*?)\):', "get_log_html_by_run"),
        ]
        for pattern, fn_name in routes:
            route = re.search(pattern, main, re.S)
            self.assertIsNotNone(route, fn_name)
            self.assertNotIn("Depends(get_current_user)", route.group(1))

        self.assertIn("store.llm_stats_summary(days)", main)
        self.assertIn("store.llm_stats_failures(days, page, page_size)", main)
        self.assertIn("store.llm_stats_by_run(run_id)", main)
        self.assertIn("store.llm_stats_by_scenario(days, only_failures, scenario_name, keyword)", main)
        self.assertIn("store.get_log_html_by_run(run_id)", main)

    def test_store_exposes_llm_stats_aggregations(self):
        store = (ROOT / "app" / "services" / "store.py").read_text(encoding="utf-8")

        for fn in (
            "def llm_stats_summary(days):",
            "def llm_stats_failures(days, page, page_size):",
            "def llm_stats_by_run(run_id):",
            "def llm_stats_by_scenario(days, only_failures, scenario_name, keyword):",
            "def get_log_html_by_run(run_id):",
        ):
            self.assertIn(fn, store)

        self.assertIn("LLM_CALL_LOG_TABLE", store)
        self.assertIn('"llm_call_log"', store)
        self.assertIn("created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)", store)
        self.assertIn("GROUP BY run_id", store)
        self.assertIn("status='failed'", store)
        self.assertIn("_safe_json_object", store)
        self.assertIn("success_rate", store)
        self.assertIn("total_input_tokens", store)
        self.assertIn("total_output_tokens", store)
        self.assertIn("SELECT html_content FROM", store)
        self.assertIn("WHERE run_id=%s", store)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run backend contract test and verify red**

Run:

```bash
python3 -m unittest tests/test_llm_call_stats_contract.py
```

Expected: failures because the migration, routes, and store functions do not exist yet.

## Task 2: Schema And Migration

**Files:**
- Modify: `/Users/yangfan/workspace/codex/agent-mgmt-service/migrations/001_create_agent_mgmt_tables.sql`
- Create: `/Users/yangfan/workspace/codex/agent-mgmt-service/migrations/005_llm_call_logs.sql`
- Test: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_llm_call_stats_contract.py`

- [ ] **Step 1: Update base schema**

In `migrations/001_create_agent_mgmt_tables.sql`, change the execution log table so it includes `run_id` immediately after `id`:

```sql
CREATE TABLE IF NOT EXISTS `agent_mgmt_execution_log` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `run_id` VARCHAR(36) DEFAULT NULL COMMENT '请求唯一标识，关联 llm_call_log',
  `scenario_id` INT DEFAULT NULL,
  `scenario_name` VARCHAR(200) NOT NULL DEFAULT 'unknown',
  `log_name` VARCHAR(500) NOT NULL DEFAULT '',
  `extra_data` TEXT DEFAULT NULL,
  `remark` VARCHAR(500) DEFAULT NULL,
  `html_content` LONGTEXT DEFAULT NULL,
  `created_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  KEY ix_agent_mgmt_execution_log_run_id (`run_id`),
  KEY ix_execution_log_scenario_id (`scenario_id`),
  KEY ix_execution_log_scenario_name (`scenario_name`),
  KEY ix_execution_log_created_at (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent management execution logs';
```

Add the new table after `agent_mgmt_execution_log`:

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

- [ ] **Step 2: Add incremental migration**

Create `migrations/005_llm_call_logs.sql`:

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

SET @col_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_execution_log'
     AND COLUMN_NAME = 'run_id'
);
SET @sql := IF(
  @col_exists = 0,
  'ALTER TABLE `agent_mgmt_execution_log` ADD COLUMN `run_id` VARCHAR(36) DEFAULT NULL COMMENT ''请求唯一标识，关联 llm_call_log'' AFTER `id`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_execution_log'
     AND INDEX_NAME = 'ix_agent_mgmt_execution_log_run_id'
);
SET @sql := IF(
  @idx_exists = 0,
  'ALTER TABLE `agent_mgmt_execution_log` ADD INDEX `ix_agent_mgmt_execution_log_run_id` (`run_id`)',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @llm_extra_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'llm_call_log'
     AND COLUMN_NAME = 'extra_data'
);
SET @sql := IF(
  @llm_extra_exists = 0,
  'ALTER TABLE `llm_call_log` ADD COLUMN `extra_data` TEXT DEFAULT NULL COMMENT ''附加数据JSON，如 {"system_id":"app01","alert_key":"A-001"}'' AFTER `output_tokens`',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
```

- [ ] **Step 3: Run backend contract test and observe remaining failures**

Run:

```bash
python3 -m unittest tests/test_llm_call_stats_contract.py
```

Expected: schema assertions pass; route/store assertions still fail.

## Task 3: Backend Store Aggregations

**Files:**
- Modify: `/Users/yangfan/workspace/codex/agent-mgmt-service/app/services/store.py`
- Test: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_llm_call_stats_contract.py`

- [ ] **Step 1: Add table constant and helper functions**

In `app/services/store.py`, add the table constant next to `LOG_TABLE`:

```python
LLM_CALL_LOG_TABLE = "llm_call_log"
```

Add these helpers before `list_logs(...)`:

```python
def _safe_int(value, default=0):
    return int(value) if value is not None else default


def _format_rate(successes, total):
    if not total:
        return "0%"
    return "{:.1f}%".format((successes / float(total)) * 100)


def _safe_json_object(value):
    parsed = _json_loads(value, {})
    return parsed if isinstance(parsed, dict) else {}
```

- [ ] **Step 2: Add `llm_stats_summary(days)`**

Add this function before `list_logs(...)`:

```python
def llm_stats_summary(days):
    with db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT COUNT(*) AS total_calls,
                   SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS total_failures,
                   AVG(latency_ms) AS avg_latency_ms
              FROM {LLM_CALL_LOG_TABLE}
             WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """,
            (days,),
        )
        summary = cursor.fetchone() or {}
        cursor.execute(
            f"""
            SELECT model,
                   COUNT(*) AS calls,
                   SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failures,
                   AVG(latency_ms) AS avg_latency_ms,
                   SUM(COALESCE(input_tokens, 0)) AS total_input_tokens,
                   SUM(COALESCE(output_tokens, 0)) AS total_output_tokens
              FROM {LLM_CALL_LOG_TABLE}
             WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
             GROUP BY model
             ORDER BY calls DESC, model ASC
            """,
            (days,),
        )
        model_rows = cursor.fetchall()
        cursor.execute(
            f"""
            SELECT agent_role,
                   COUNT(*) AS calls,
                   SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failures,
                   AVG(latency_ms) AS avg_latency_ms
              FROM {LLM_CALL_LOG_TABLE}
             WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
             GROUP BY agent_role
             ORDER BY calls DESC, agent_role ASC
            """,
            (days,),
        )
        role_rows = cursor.fetchall()

    total_calls = _safe_int(summary.get("total_calls"))
    total_failures = _safe_int(summary.get("total_failures"))
    by_model = {}
    for row in model_rows:
        by_model[row["model"] or "unknown"] = {
            "calls": _safe_int(row.get("calls")),
            "failures": _safe_int(row.get("failures")),
            "avg_latency_ms": _safe_int(row.get("avg_latency_ms")),
            "total_input_tokens": _safe_int(row.get("total_input_tokens")),
            "total_output_tokens": _safe_int(row.get("total_output_tokens")),
        }
    by_role = {}
    for row in role_rows:
        by_role[row["agent_role"] or "unknown"] = {
            "calls": _safe_int(row.get("calls")),
            "failures": _safe_int(row.get("failures")),
            "avg_latency_ms": _safe_int(row.get("avg_latency_ms")),
        }
    return {
        "total_calls": total_calls,
        "total_failures": total_failures,
        "success_rate": _format_rate(total_calls - total_failures, total_calls),
        "avg_latency_ms": _safe_int(summary.get("avg_latency_ms")),
        "by_model": by_model,
        "by_role": by_role,
    }
```

- [ ] **Step 3: Add failures, by-run, by-scenario, and log HTML functions**

Add these functions after `llm_stats_summary(days)`:

```python
def llm_stats_failures(days, page, page_size):
    offset = (page - 1) * page_size
    with db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT COUNT(*) AS total
              FROM {LLM_CALL_LOG_TABLE}
             WHERE status='failed'
               AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """,
            (days,),
        )
        total = _safe_int(cursor.fetchone()["total"])
        cursor.execute(
            f"""
            SELECT id,run_id,scenario_name,agent_role,model,retry_count,error_type,error_msg,created_at
              FROM {LLM_CALL_LOG_TABLE}
             WHERE status='failed'
               AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
             ORDER BY created_at DESC,id DESC
             LIMIT %s OFFSET %s
            """,
            (days, page_size, offset),
        )
        items = cursor.fetchall()
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def llm_stats_by_run(run_id):
    with db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT id,run_id,scenario_name,agent_role,call_index,model,status,latency_ms,
                   retry_count,error_type,error_msg,input_tokens,output_tokens,created_at
              FROM {LLM_CALL_LOG_TABLE}
             WHERE run_id=%s
             ORDER BY call_index ASC,id ASC
            """,
            (run_id,),
        )
        calls = cursor.fetchall()
    if not calls:
        return {
            "run_id": run_id,
            "scenario_name": "",
            "total_calls": 0,
            "total_failures": 0,
            "total_latency_ms": 0,
            "calls": [],
        }
    total_failures = sum(1 for call in calls if call.get("status") == "failed")
    total_latency = sum(_safe_int(call.get("latency_ms")) for call in calls)
    scenario_name = next((call.get("scenario_name") for call in calls if call.get("scenario_name")), "")
    return {
        "run_id": run_id,
        "scenario_name": scenario_name,
        "total_calls": len(calls),
        "total_failures": total_failures,
        "total_latency_ms": total_latency,
        "calls": calls,
    }


def llm_stats_by_scenario(days, only_failures, scenario_name, keyword):
    where = ["created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)"]
    params = [days]
    if scenario_name:
        where.append("scenario_name=%s")
        params.append(scenario_name)
    if keyword:
        where.append("(run_id LIKE %s OR scenario_name LIKE %s OR extra_data LIKE %s)")
        like = "%{}%".format(keyword)
        params.extend([like, like, like])
    clause = " WHERE " + " AND ".join(where)
    having = " HAVING failures > 0" if only_failures else ""
    with db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT run_id,
                   MIN(created_at) AS created_at,
                   SUBSTRING_INDEX(GROUP_CONCAT(scenario_name ORDER BY created_at ASC SEPARATOR '\\n'), '\\n', 1) AS scenario_name,
                   COUNT(*) AS total_calls,
                   SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failures,
                   AVG(latency_ms) AS avg_latency_ms,
                   SUM(COALESCE(latency_ms, 0)) AS total_latency_ms,
                   SUBSTRING_INDEX(GROUP_CONCAT(COALESCE(extra_data, '') ORDER BY created_at ASC SEPARATOR '\\n'), '\\n', 1) AS extra_data
              FROM {LLM_CALL_LOG_TABLE}
              {clause}
             GROUP BY run_id
             {having}
             ORDER BY created_at DESC
             LIMIT 200
            """,
            tuple(params),
        )
        rows = cursor.fetchall()
    result = []
    for row in rows:
        total_calls = _safe_int(row.get("total_calls"))
        failures = _safe_int(row.get("failures"))
        result.append({
            "run_id": row.get("run_id") or "",
            "scenario_name": row.get("scenario_name") or "unknown",
            "created_at": row.get("created_at"),
            "total_calls": total_calls,
            "failures": failures,
            "success_rate": _format_rate(total_calls - failures, total_calls),
            "avg_latency_ms": _safe_int(row.get("avg_latency_ms")),
            "total_latency_ms": _safe_int(row.get("total_latency_ms")),
            "extra_data": _safe_json_object(row.get("extra_data")),
        })
    return result


def get_log_html_by_run(run_id):
    with db_cursor() as cursor:
        return _select_one(
            cursor,
            f"""
            SELECT html_content
              FROM {LOG_TABLE}
             WHERE run_id=%s
             ORDER BY created_at DESC,id DESC
             LIMIT 1
            """,
            (run_id,),
        )
```

- [ ] **Step 4: Run backend contract test and observe route failures**

Run:

```bash
python3 -m unittest tests/test_llm_call_stats_contract.py
```

Expected: store assertions pass; route assertions still fail.

## Task 4: Backend Routes

**Files:**
- Modify: `/Users/yangfan/workspace/codex/agent-mgmt-service/app/main.py`
- Test: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_llm_call_stats_contract.py`

- [ ] **Step 1: Add LLM stats routes**

Add these routes after `log_stats(scenario_name: str = None)` and before `get_log_html(log_id: int)`:

```python
@app.get("/llm-stats/summary")
def llm_stats_summary(days: int = Query(7, ge=1, le=30)):
    return store.llm_stats_summary(days)


@app.get("/llm-stats/failures", response_model=ExecutionLogPage)
def llm_stats_failures(
    days: int = Query(7, ge=1, le=30),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    return store.llm_stats_failures(days, page, page_size)


@app.get("/llm-stats/by-run/{run_id}")
def llm_stats_by_run(run_id: str):
    return store.llm_stats_by_run(run_id)


@app.get("/llm-stats/by-scenario")
def llm_stats_by_scenario(
    days: int = Query(7, ge=1, le=30),
    only_failures: bool = False,
    scenario_name: str = None,
    keyword: str = None,
):
    return store.llm_stats_by_scenario(days, only_failures, scenario_name, keyword)


@app.get("/logs/by-run/{run_id}/html", response_class=HTMLResponse)
def get_log_html_by_run(run_id: str):
    row = store.get_log_html_by_run(run_id)
    if not row or not row.get("html_content"):
        raise HTTPException(status_code=404, detail="Log not found")
    return row["html_content"]
```

- [ ] **Step 2: Run backend contract test**

Run:

```bash
python3 -m unittest tests/test_llm_call_stats_contract.py
```

Expected: `OK`.

## Task 5: Frontend Contract Tests

**Files:**
- Create: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_ruoyi_ui_llm_stats_contract.py`
- Test: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_ruoyi_ui_llm_stats_contract.py`

- [ ] **Step 1: Add failing frontend contract tests**

Create `tests/test_ruoyi_ui_llm_stats_contract.py`:

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
UI_ROOT = ROOT.parent / "ruoyi-cloud-ops" / "ruoyi-ui"
API_FILE = UI_ROOT / "src" / "api" / "agentMgmt" / "index.js"
LLM_VIEW = UI_ROOT / "src" / "views" / "agentMgmt" / "llmStats" / "index.vue"


class RuoyiLlmStatsContractTests(unittest.TestCase):
    def test_api_exports_llm_stats_methods(self):
        source = API_FILE.read_text(encoding="utf-8")

        self.assertIn("export function getLlmStatsSummary(params)", source)
        self.assertIn("export function listLlmStatsFailures(params)", source)
        self.assertIn("export function getLlmStatsByRun(runId)", source)
        self.assertIn("export function listLlmStatsByScenario(params)", source)
        self.assertIn("export function logHtmlByRunUrl(runId)", source)
        self.assertIn("`${base}/llm-stats/summary`", source)
        self.assertIn("`${base}/llm-stats/failures`", source)
        self.assertIn("`${base}/llm-stats/by-run/${runId}`", source)
        self.assertIn("`${base}/llm-stats/by-scenario`", source)
        self.assertIn("`${process.env.VUE_APP_BASE_API}${base}/logs/by-run/${runId}/html`", source)

    def test_llm_stats_page_contains_expected_ui_and_calls(self):
        source = LLM_VIEW.read_text(encoding="utf-8")

        self.assertIn("name: 'AgentMgmtLlmStats'", source)
        self.assertIn("LLM 调用统计", source)
        self.assertIn("模型资源使用与故障分析", source)
        self.assertIn("整体统计", source)
        self.assertIn("场景维度", source)
        self.assertIn("总调用", source)
        self.assertIn("成功率", source)
        self.assertIn("失败数", source)
        self.assertIn("平均延迟", source)
        self.assertIn("按模型分布", source)
        self.assertIn("按角色分布", source)
        self.assertIn("最近失败记录", source)
        self.assertIn("LLM 调用详情", source)
        self.assertIn("getLlmStatsSummary", source)
        self.assertIn("listLlmStatsFailures", source)
        self.assertIn("getLlmStatsByRun", source)
        self.assertIn("listLlmStatsByScenario", source)
        self.assertIn("logHtmlByRunUrl", source)
        self.assertIn("openRunDrawer", source)
        self.assertIn("openLogByRun", source)
        self.assertIn("el-drawer", source)
        self.assertIn("runIdQuery", source)
        self.assertIn("only_failures", source)
```

- [ ] **Step 2: Run frontend contract test and verify red**

Run:

```bash
python3 -m unittest tests/test_ruoyi_ui_llm_stats_contract.py
```

Expected: failure because API methods and `llmStats/index.vue` do not exist yet.

## Task 6: Frontend API Wrapper

**Files:**
- Modify: `/Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/src/api/agentMgmt/index.js`
- Test: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_ruoyi_ui_llm_stats_contract.py`

- [ ] **Step 1: Add LLM stats API methods**

Append these methods to `src/api/agentMgmt/index.js`:

```js
export function getLlmStatsSummary(params) {
  return request({ url: `${base}/llm-stats/summary`, method: 'get', params })
}

export function listLlmStatsFailures(params) {
  return request({ url: `${base}/llm-stats/failures`, method: 'get', params })
}

export function getLlmStatsByRun(runId) {
  return request({ url: `${base}/llm-stats/by-run/${runId}`, method: 'get' })
}

export function listLlmStatsByScenario(params) {
  return request({ url: `${base}/llm-stats/by-scenario`, method: 'get', params })
}

export function logHtmlByRunUrl(runId) {
  return `${process.env.VUE_APP_BASE_API}${base}/logs/by-run/${runId}/html`
}
```

- [ ] **Step 2: Run frontend contract test and observe page failure**

Run:

```bash
python3 -m unittest tests/test_ruoyi_ui_llm_stats_contract.py
```

Expected: API assertions pass; view assertions still fail.

## Task 7: Frontend LLM Stats Page

**Files:**
- Create: `/Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/src/views/agentMgmt/llmStats/index.vue`
- Test: `/Users/yangfan/workspace/codex/agent-mgmt-service/tests/test_ruoyi_ui_llm_stats_contract.py`

- [ ] **Step 1: Create the Vue component**

Create `src/views/agentMgmt/llmStats/index.vue` with this structure:

```vue
<template>
  <div class="app-container agent-mgmt-page">
    <div class="am-topbar">
      <div>
        <span class="am-title">LLM 调用统计</span>
        <span class="am-sub">模型资源使用与故障分析</span>
      </div>
      <div class="am-actions">
        <el-select v-model="days" size="mini" class="days-select" @change="refreshCurrent">
          <el-option :value="1" label="最近1天" />
          <el-option :value="3" label="最近3天" />
          <el-option :value="7" label="最近7天" />
          <el-option :value="14" label="最近14天" />
          <el-option :value="30" label="最近30天" />
        </el-select>
        <el-button size="mini" icon="el-icon-refresh" @click="refreshCurrent">刷新</el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="llm-tabs" @tab-click="onTabChange">
      <el-tab-pane label="整体统计" name="overall">
        <div v-loading="overallLoading" class="am-scroll">
          <div v-if="overallError" class="error-text">{{ overallError }}</div>
          <div class="stat-grid">
            <div class="stat-card">
              <span>总调用</span>
              <strong>{{ summary.total_calls || 0 }}</strong>
            </div>
            <div class="stat-card">
              <span>成功率</span>
              <strong :class="successRateClass">{{ summary.success_rate || '0%' }}</strong>
            </div>
            <div class="stat-card clickable" @click="scrollToFailures">
              <span>失败数</span>
              <strong class="danger">{{ summary.total_failures || 0 }}</strong>
            </div>
            <div class="stat-card">
              <span>平均延迟</span>
              <strong>{{ formatLatency(summary.avg_latency_ms) }}</strong>
            </div>
          </div>

          <div class="table-grid">
            <section>
              <div class="section-title">按模型分布</div>
              <el-table :data="modelRows" size="mini" border>
                <el-table-column prop="name" label="模型" min-width="140" />
                <el-table-column prop="calls" label="调用" width="80" />
                <el-table-column prop="failures" label="失败" width="80" />
                <el-table-column label="成功率" width="90">
                  <template slot-scope="{ row }">{{ row.success_rate }}</template>
                </el-table-column>
                <el-table-column label="平均延迟" width="100">
                  <template slot-scope="{ row }">{{ formatLatency(row.avg_latency_ms) }}</template>
                </el-table-column>
                <el-table-column prop="total_input_tokens" label="输入Tokens" width="120" />
                <el-table-column prop="total_output_tokens" label="输出Tokens" width="120" />
              </el-table>
            </section>

            <section>
              <div class="section-title">按角色分布</div>
              <el-table :data="roleRows" size="mini" border>
                <el-table-column prop="name" label="角色" min-width="150" />
                <el-table-column prop="calls" label="调用" width="80" />
                <el-table-column prop="failures" label="失败" width="80" />
                <el-table-column label="成功率" width="90">
                  <template slot-scope="{ row }">{{ row.success_rate }}</template>
                </el-table-column>
                <el-table-column label="平均延迟" width="100">
                  <template slot-scope="{ row }">{{ formatLatency(row.avg_latency_ms) }}</template>
                </el-table-column>
              </el-table>
            </section>
          </div>

          <section ref="failuresSection" class="fail-section">
            <div class="section-title">最近失败记录</div>
            <el-table v-if="failures.length" :data="failures" size="mini" border>
              <el-table-column prop="created_at" label="时间" width="160" />
              <el-table-column prop="scenario_name" label="场景" min-width="130" />
              <el-table-column prop="agent_role" label="角色" min-width="130" />
              <el-table-column prop="model" label="模型" width="130" />
              <el-table-column prop="retry_count" label="重试" width="70" />
              <el-table-column prop="error_type" label="错误类型" width="100" />
              <el-table-column prop="error_msg" label="错误信息" min-width="220" show-overflow-tooltip />
              <el-table-column label="run_id" width="190">
                <template slot-scope="{ row }">
                  <el-button type="text" class="mono-link" @click="openRunDrawer(row.run_id)">{{ row.run_id }}</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="无失败记录" />
          </section>
        </div>
      </el-tab-pane>

      <el-tab-pane label="场景维度" name="scenario">
        <div class="filterbar">
          <el-select v-model="scenarioQuery.onlyFailures" size="mini" class="filter-small" @change="loadScenario">
            <el-option :value="false" label="全部请求" />
            <el-option :value="true" label="仅含失败" />
          </el-select>
          <el-select v-model="scenarioQuery.scenario_name" size="mini" clearable filterable placeholder="全部场景" @change="loadScenario">
            <el-option v-for="name in scenarioNames" :key="name" :label="name" :value="name" />
          </el-select>
          <el-input v-model.trim="scenarioQuery.keyword" size="mini" clearable placeholder="告警单号 / 系统ID" @keyup.enter.native="loadScenario" />
          <el-input v-model.trim="runIdQuery" size="mini" clearable class="run-input" placeholder="精确查询 run_id" @keyup.enter.native="openRunDrawer(runIdQuery)" />
          <el-button size="mini" type="primary" icon="el-icon-search" @click="loadScenario">查询</el-button>
        </div>
        <div v-loading="scenarioLoading" class="am-scroll">
          <div v-if="scenarioError" class="error-text">{{ scenarioError }}</div>
          <el-table v-if="scenarioRows.length" :data="scenarioRows" size="mini" border>
            <el-table-column prop="created_at" label="时间" width="160" />
            <el-table-column prop="scenario_name" label="场景" min-width="130" />
            <el-table-column label="关联信息" min-width="160">
              <template slot-scope="{ row }">{{ extraText(row.extra_data) }}</template>
            </el-table-column>
            <el-table-column label="run_id" width="190">
              <template slot-scope="{ row }">
                <el-button type="text" class="mono-link" @click="openLogByRun(row.run_id)">{{ row.run_id }}</el-button>
              </template>
            </el-table-column>
            <el-table-column label="LLM调用数" width="100">
              <template slot-scope="{ row }">
                <el-button type="text" @click="openRunDrawer(row.run_id)">{{ row.total_calls }}</el-button>
              </template>
            </el-table-column>
            <el-table-column prop="failures" label="失败数" width="80" />
            <el-table-column prop="success_rate" label="成功率" width="90" />
            <el-table-column label="平均延迟" width="100">
              <template slot-scope="{ row }">{{ formatLatency(row.avg_latency_ms) }}</template>
            </el-table-column>
            <el-table-column label="总延迟" width="100">
              <template slot-scope="{ row }">{{ formatLatency(row.total_latency_ms) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template slot-scope="{ row }">
                <el-tag size="mini" :type="row.failures > 0 ? 'danger' : 'success'">{{ row.failures > 0 ? row.failures + ' 失败' : '全部成功' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="无匹配数据" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-drawer :visible.sync="drawerVisible" size="860px" custom-class="llm-drawer" :title="drawerTitle">
      <div v-loading="drawerLoading" class="drawer-body">
        <div v-if="drawerError" class="error-text">{{ drawerError }}</div>
        <div v-if="drawerData" class="drawer-summary">
          <span>场景 <strong>{{ drawerData.scenario_name || '-' }}</strong></span>
          <span>调用 <strong>{{ drawerData.total_calls }}</strong></span>
          <span>失败 <strong class="danger">{{ drawerData.total_failures }}</strong></span>
          <span>总延迟 <strong>{{ formatLatency(drawerData.total_latency_ms) }}</strong></span>
        </div>
        <el-table v-if="drawerCalls.length" :data="drawerCalls" size="mini" border>
          <el-table-column prop="call_index" label="#" width="50" />
          <el-table-column prop="agent_role" label="角色" min-width="130" />
          <el-table-column prop="model" label="模型" width="130" />
          <el-table-column label="状态" width="80">
            <template slot-scope="{ row }">
              <span :class="row.status === 'success' ? 'ok' : 'danger'">{{ row.status === 'success' ? 'OK' : 'FAIL' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="延迟" width="90">
            <template slot-scope="{ row }">{{ formatLatency(row.latency_ms) }}</template>
          </el-table-column>
          <el-table-column prop="retry_count" label="重试" width="70" />
          <el-table-column prop="error_msg" label="错误" min-width="180" show-overflow-tooltip />
          <el-table-column prop="input_tokens" label="输入Tokens" width="110" />
          <el-table-column prop="output_tokens" label="输出Tokens" width="110" />
          <el-table-column prop="created_at" label="时间" width="160" />
        </el-table>
        <el-empty v-else description="未找到该 run_id 的记录" />
      </div>
    </el-drawer>
  </div>
</template>
```

The `<script>` must import the new API methods and implement:

```js
import {
  getLlmStatsByRun,
  getLlmStatsSummary,
  listLlmStatsByScenario,
  listLlmStatsFailures,
  logHtmlByRunUrl
} from '@/api/agentMgmt'

export default {
  name: 'AgentMgmtLlmStats',
  data() {
    return {
      days: 7,
      activeTab: 'overall',
      overallLoading: false,
      scenarioLoading: false,
      drawerLoading: false,
      overallError: '',
      scenarioError: '',
      drawerError: '',
      summary: { total_calls: 0, total_failures: 0, success_rate: '0%', avg_latency_ms: 0, by_model: {}, by_role: {} },
      failures: [],
      scenarioRows: [],
      scenarioNames: [],
      scenarioQuery: { onlyFailures: false, scenario_name: '', keyword: '' },
      runIdQuery: '',
      drawerVisible: false,
      drawerRunId: '',
      drawerData: null
    }
  },
  computed: {
    modelRows() {
      return this.objectRows(this.summary.by_model)
    },
    roleRows() {
      return this.objectRows(this.summary.by_role)
    },
    drawerCalls() {
      return this.drawerData && this.drawerData.calls ? this.drawerData.calls : []
    },
    drawerTitle() {
      return this.drawerRunId ? `LLM 调用详情 - ${this.drawerRunId}` : 'LLM 调用详情'
    },
    successRateClass() {
      const rate = parseFloat(this.summary.success_rate || '0')
      if (rate >= 99) return 'ok'
      if (rate >= 95) return 'warn'
      return 'danger'
    }
  },
  created() {
    this.loadOverall()
  },
  methods: {
    objectRows(obj) {
      return Object.keys(obj || {}).map(name => {
        const item = obj[name] || {}
        const calls = item.calls || 0
        const failures = item.failures || 0
        return { name, ...item, success_rate: calls ? (((calls - failures) / calls) * 100).toFixed(1) + '%' : '-' }
      })
    },
    refreshCurrent() {
      if (this.activeTab === 'overall') this.loadOverall()
      else this.loadScenario()
    },
    onTabChange() {
      this.refreshCurrent()
    },
    async loadOverall() {
      this.overallLoading = true
      this.overallError = ''
      try {
        const [summary, failures] = await Promise.all([
          getLlmStatsSummary({ days: this.days }),
          listLlmStatsFailures({ days: this.days, page: 1, page_size: 50 })
        ])
        this.summary = summary || this.summary
        this.failures = failures && failures.items ? failures.items : []
      } catch (e) {
        this.overallError = this.errorText(e)
      } finally {
        this.overallLoading = false
      }
    },
    async loadScenario() {
      this.scenarioLoading = true
      this.scenarioError = ''
      try {
        const rows = await listLlmStatsByScenario({
          days: this.days,
          only_failures: this.scenarioQuery.onlyFailures,
          scenario_name: this.scenarioQuery.scenario_name,
          keyword: this.scenarioQuery.keyword
        })
        this.scenarioRows = Array.isArray(rows) ? rows : []
        this.scenarioNames = Array.from(new Set(this.scenarioRows.map(row => row.scenario_name).filter(Boolean))).sort()
      } catch (e) {
        this.scenarioError = this.errorText(e)
      } finally {
        this.scenarioLoading = false
      }
    },
    async openRunDrawer(runId) {
      if (!runId) return
      this.drawerRunId = runId
      this.drawerVisible = true
      this.drawerLoading = true
      this.drawerError = ''
      this.drawerData = null
      try {
        this.drawerData = await getLlmStatsByRun(runId)
      } catch (e) {
        this.drawerError = this.errorText(e)
      } finally {
        this.drawerLoading = false
      }
    },
    openLogByRun(runId) {
      if (!runId) return
      window.open(logHtmlByRunUrl(runId), '_blank')
    },
    scrollToFailures() {
      if (this.$refs.failuresSection) this.$refs.failuresSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
    },
    formatLatency(value) {
      if (value === null || value === undefined || value === '') return '-'
      const ms = Number(value) || 0
      return ms >= 1000 ? (ms / 1000).toFixed(1) + 's' : `${ms}ms`
    },
    extraText(extra) {
      const data = extra || {}
      const parts = [data.alert_key, data.system_id, data.alert_source].filter(Boolean)
      return parts.length ? parts.join(' / ') : '-'
    },
    errorText(error) {
      const data = error && error.response && error.response.data
      return (data && (data.detail || data.msg || data.message)) || (error && error.message) || '加载失败'
    }
  }
}
```

The `<style scoped>` must define compact admin styles for:

```css
.agent-mgmt-page
.am-topbar
.am-title
.am-sub
.am-actions
.days-select
.llm-tabs
.am-scroll
.stat-grid
.stat-card
.stat-card.clickable
.table-grid
.section-title
.fail-section
.filterbar
.filter-small
.run-input
.drawer-body
.drawer-summary
.mono-link
.ok
.warn
.danger
.error-text
```

- [ ] **Step 2: Run frontend contract test**

Run:

```bash
python3 -m unittest tests/test_ruoyi_ui_llm_stats_contract.py
```

Expected: `OK`.

## Task 8: Full Test And Build Verification

**Files:**
- Verify: backend files and frontend files

- [ ] **Step 1: Run all backend contract tests**

Run:

```bash
python3 -m unittest discover -s tests
```

Expected: all tests pass.

- [ ] **Step 2: Build RuoYi UI**

Run from `/Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui`:

```bash
npm run build:prod
```

Expected: build completes. Existing asset size warnings are acceptable.

## Task 9: Remote Deployment And Demo Data

**Files:**
- Deploy backend: `/opt/agent-mgmt-service`
- Deploy frontend source: `/opt/ruoyi-cloud-ops/source/ruoyi-ui`
- Deploy frontend static: `/opt/middleware-stack/data/nginx-html`

- [ ] **Step 1: Back up remote backend and frontend**

Run:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'ts=$(date +%Y%m%d%H%M%S); mkdir -p /opt/agent-mgmt-service/backups/llm-stats-$ts /opt/middleware-stack/data/nginx-html-backups; cp -a /opt/agent-mgmt-service/app /opt/agent-mgmt-service/migrations /opt/agent-mgmt-service/backups/llm-stats-$ts/; cp -a /opt/middleware-stack/data/nginx-html /opt/middleware-stack/data/nginx-html-backups/ruoyi-ui-llm-stats-$ts; printf "%s\n" "$ts"'
```

Expected: prints a timestamp.

- [ ] **Step 2: Sync backend files**

Run:

```bash
tar -C /Users/yangfan/workspace/codex/agent-mgmt-service --no-xattrs -czf - app/main.py app/services/store.py migrations/001_create_agent_mgmt_tables.sql migrations/005_llm_call_logs.sql tests/test_llm_call_stats_contract.py tests/test_ruoyi_ui_llm_stats_contract.py | ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'cd /opt/agent-mgmt-service && tar -xzf -'
```

Expected: exit code `0`.

- [ ] **Step 3: Sync frontend source files**

Run:

```bash
scp -o BatchMode=yes -o StrictHostKeyChecking=no /Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/src/api/agentMgmt/index.js root@43.135.134.42:/opt/ruoyi-cloud-ops/source/ruoyi-ui/src/api/agentMgmt/index.js
ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'mkdir -p /opt/ruoyi-cloud-ops/source/ruoyi-ui/src/views/agentMgmt/llmStats'
scp -o BatchMode=yes -o StrictHostKeyChecking=no /Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/src/views/agentMgmt/llmStats/index.vue root@43.135.134.42:/opt/ruoyi-cloud-ops/source/ruoyi-ui/src/views/agentMgmt/llmStats/index.vue
```

Expected: exit code `0`.

- [ ] **Step 4: Run migration on remote**

Run:

```bash
base64 -i migrations/005_llm_call_logs.sql | ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'cd /opt/middleware-stack && source .env && base64 -d >/tmp/005_llm_call_logs.sql && docker exec -i mysql57 mysql -uroot -p"$MYSQL_ROOT_PASSWORD" agent_mgmt < /tmp/005_llm_call_logs.sql'
```

Expected: exit code `0`.

- [ ] **Step 5: Restart remote backend**

Run:

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'cd /opt/agent-mgmt-service && ./start.sh restart && ./start.sh status'
```

Expected: service reports running on port `8300`.

- [ ] **Step 6: Deploy built RuoYi static assets**

Run:

```bash
tar -C /Users/yangfan/workspace/codex/ruoyi-cloud-ops/ruoyi-ui/dist --no-xattrs -czf - . | ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'tmp=/tmp/ruoyi-ui-dist-llm-stats.tgz; cat > $tmp; cd /opt/middleware-stack/data/nginx-html; rm -rf index.html index.html.gz favicon.ico robots.txt html static styles; tar -xzf $tmp; rm -f $tmp'
```

Expected: exit code `0`.

- [ ] **Step 7: Register the remote RuoYi menu**

Run a remote SQL script against the RuoYi system database after confirming its configured database name from `/opt/middleware-stack/.env`. For the current deployment this is expected to be `ry-cloud`.

```sql
USE `ry-cloud`;

SET @parent_id := (
  SELECT menu_id
  FROM sys_menu
  WHERE path = 'agent-mgmt' OR menu_name = 'Agent管理'
  ORDER BY parent_id ASC, order_num ASC
  LIMIT 1
);

SET @exists := (
  SELECT COUNT(*)
  FROM sys_menu
  WHERE parent_id = @parent_id AND path = 'llm-stats'
);

SET @insert_sql := IF(
  @parent_id IS NOT NULL AND @exists = 0,
  "INSERT INTO sys_menu (menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
   VALUES ('LLM 统计', @parent_id, 5, 'llm-stats', 'agentMgmt/llmStats/index', NULL, 'LlmStats', 1, 0, 'C', '0', '0', '', 'monitor', 'system', NOW(), 'LLM 调用统计')",
  "SELECT 1"
);
PREPARE stmt FROM @insert_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE sys_menu
SET menu_name = 'LLM 统计',
    component = 'agentMgmt/llmStats/index',
    route_name = 'LlmStats',
    visible = '0',
    status = '0',
    update_time = NOW()
WHERE parent_id = @parent_id AND path = 'llm-stats';
```

Expected: one visible Agent Management child menu exists for `LLM 统计`.

- [ ] **Step 8: Insert remote demo data once**

Run a remote SQL script that deletes fixed demo IDs and reinserts them:

```sql
DELETE FROM llm_call_log WHERE run_id LIKE 'demo-llm-%';
DELETE FROM agent_mgmt_execution_log WHERE run_id LIKE 'demo-llm-%';

INSERT INTO agent_mgmt_execution_log
  (run_id, scenario_id, scenario_name, log_name, extra_data, remark, html_content, created_at)
VALUES
  ('demo-llm-0001', NULL, 'alert_analysis', '告警根因分析 demo', '{"system_id":"app01","alert_key":"A-001","alert_source":"prometheus"}', 'demo llm stats', '<html><body><h2>demo-llm-0001 执行详情</h2><p>告警根因分析完成。</p></body></html>', NOW() - INTERVAL 1 DAY),
  ('demo-llm-0002', NULL, 'alert_analysis', '告警失败重试 demo', '{"system_id":"app02","alert_key":"A-002","alert_source":"zabbix"}', 'demo llm stats', '<html><body><h2>demo-llm-0002 执行详情</h2><p>包含 LLM 失败与重试。</p></body></html>', NOW() - INTERVAL 2 DAY),
  ('demo-llm-0003', NULL, 'log_diagnosis', '日志诊断 demo', '{"system_id":"log01","alert_key":"L-009","alert_source":"elk"}', 'demo llm stats', '<html><body><h2>demo-llm-0003 执行详情</h2><p>日志诊断完成。</p></body></html>', NOW() - INTERVAL 3 DAY);

INSERT INTO llm_call_log
  (run_id, scenario_name, agent_role, call_index, model, status, latency_ms, retry_count, error_type, error_msg, input_tokens, output_tokens, extra_data, created_at)
VALUES
  ('demo-llm-0001', 'alert_analysis', '意图识别', 1, 'gpt-4.1-mini', 'success', 820, 0, NULL, NULL, 980, 180, '{"system_id":"app01","alert_key":"A-001","alert_source":"prometheus"}', NOW() - INTERVAL 1 DAY),
  ('demo-llm-0001', 'alert_analysis', '规划Agent', 2, 'gpt-4.1', 'success', 2100, 0, NULL, NULL, 2600, 620, '{"system_id":"app01","alert_key":"A-001","alert_source":"prometheus"}', NOW() - INTERVAL 1 DAY + INTERVAL 2 MINUTE),
  ('demo-llm-0001', 'alert_analysis', 'es_expert_agent', 3, 'deepseek-chat', 'success', 1550, 0, NULL, NULL, 1800, 420, '{"system_id":"app01","alert_key":"A-001","alert_source":"prometheus"}', NOW() - INTERVAL 1 DAY + INTERVAL 4 MINUTE),
  ('demo-llm-0002', 'alert_analysis', '意图识别', 1, 'gpt-4.1-mini', 'success', 760, 0, NULL, NULL, 900, 140, '{"system_id":"app02","alert_key":"A-002","alert_source":"zabbix"}', NOW() - INTERVAL 2 DAY),
  ('demo-llm-0002', 'alert_analysis', '规划Agent', 2, 'gpt-4.1', 'failed', NULL, 3, 'rate_limit', 'quota exceeded after retries', 2400, NULL, '{"system_id":"app02","alert_key":"A-002","alert_source":"zabbix"}', NOW() - INTERVAL 2 DAY + INTERVAL 1 MINUTE),
  ('demo-llm-0002', 'alert_analysis', 'hbase_expert_agent', 3, 'deepseek-chat', 'failed', 3300, 1, 'network', 'upstream timeout', 1500, 0, '{"system_id":"app02","alert_key":"A-002","alert_source":"zabbix"}', NOW() - INTERVAL 2 DAY + INTERVAL 3 MINUTE),
  ('demo-llm-0003', 'log_diagnosis', '意图识别', 1, 'gpt-4.1-mini', 'success', 690, 0, NULL, NULL, 740, 110, '{"system_id":"log01","alert_key":"L-009","alert_source":"elk"}', NOW() - INTERVAL 3 DAY),
  ('demo-llm-0003', 'log_diagnosis', '规划Agent', 2, 'gpt-4.1', 'success', 1880, 0, NULL, NULL, 2200, 530, '{"system_id":"log01","alert_key":"L-009","alert_source":"elk"}', NOW() - INTERVAL 3 DAY + INTERVAL 2 MINUTE),
  ('demo-llm-0003', 'log_diagnosis', 'es_expert_agent', 3, 'deepseek-chat', 'failed', 1420, 2, 'other', 'invalid tool response', 1700, 90, '{"system_id":"log01","alert_key":"L-009","alert_source":"elk"}', NOW() - INTERVAL 3 DAY + INTERVAL 4 MINUTE);
```

Expected: rows inserted and page has data.

- [ ] **Step 9: Verify remote APIs**

Run:

```bash
curl -fsS 'http://43.135.134.42/prod-api/agent-mgmt-api/llm-stats/summary?days=7'
curl -fsS 'http://43.135.134.42/prod-api/agent-mgmt-api/llm-stats/failures?days=7&page=1&page_size=5'
curl -fsS 'http://43.135.134.42/prod-api/agent-mgmt-api/llm-stats/by-run/demo-llm-0002'
curl -fsS 'http://43.135.134.42/prod-api/agent-mgmt-api/llm-stats/by-scenario?days=7'
curl -I -sS 'http://43.135.134.42/prod-api/agent-mgmt-api/logs/by-run/demo-llm-0001/html'
```

Expected: stats JSON includes demo rows and log HTML returns `200`.

- [ ] **Step 10: Verify frontend route and menu registration**

Run:

```bash
curl -I -sS http://43.135.134.42/agent-mgmt/llm-stats
ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'grep -R -l "LLM 调用统计\\|模型资源使用与故障分析" /opt/middleware-stack/data/nginx-html/static/js 2>/dev/null | head -20'
ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@43.135.134.42 'cd /opt/middleware-stack && source .env && docker exec -i mysql57 mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -NBe "SELECT menu_name,path,component,visible,status FROM \`ry-cloud\`.sys_menu WHERE path='\''llm-stats'\''"'
```

Expected: route returns `200`, built JS contains the new page text, and the menu query returns `LLM 统计`.
