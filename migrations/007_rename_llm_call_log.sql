SET NAMES utf8mb4;

SET @old_llm_table_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.TABLES
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'llm_call_log'
);
SET @new_llm_table_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.TABLES
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_llm_call_log'
);
SET @rename_llm_table_sql := IF(
  @old_llm_table_exists = 1 AND @new_llm_table_exists = 0,
  'RENAME TABLE `llm_call_log` TO `agent_mgmt_llm_call_log`',
  'SELECT 1'
);
PREPARE stmt FROM @rename_llm_table_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @old_run_id_index_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_llm_call_log'
     AND INDEX_NAME = 'ix_llm_call_log_run_id'
);
SET @new_run_id_index_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_llm_call_log'
     AND INDEX_NAME = 'ix_agent_mgmt_llm_call_log_run_id'
);
SET @rename_run_id_index_sql := IF(
  @old_run_id_index_exists = 1 AND @new_run_id_index_exists = 0,
  'ALTER TABLE `agent_mgmt_llm_call_log` RENAME INDEX ix_llm_call_log_run_id TO ix_agent_mgmt_llm_call_log_run_id',
  'SELECT 1'
);
PREPARE stmt FROM @rename_run_id_index_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @old_scenario_index_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_llm_call_log'
     AND INDEX_NAME = 'ix_llm_call_log_scenario'
);
SET @new_scenario_index_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_llm_call_log'
     AND INDEX_NAME = 'ix_agent_mgmt_llm_call_log_scenario'
);
SET @rename_scenario_index_sql := IF(
  @old_scenario_index_exists = 1 AND @new_scenario_index_exists = 0,
  'ALTER TABLE `agent_mgmt_llm_call_log` RENAME INDEX ix_llm_call_log_scenario TO ix_agent_mgmt_llm_call_log_scenario',
  'SELECT 1'
);
PREPARE stmt FROM @rename_scenario_index_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @old_model_index_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_llm_call_log'
     AND INDEX_NAME = 'ix_llm_call_log_model'
);
SET @new_model_index_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_llm_call_log'
     AND INDEX_NAME = 'ix_agent_mgmt_llm_call_log_model'
);
SET @rename_model_index_sql := IF(
  @old_model_index_exists = 1 AND @new_model_index_exists = 0,
  'ALTER TABLE `agent_mgmt_llm_call_log` RENAME INDEX ix_llm_call_log_model TO ix_agent_mgmt_llm_call_log_model',
  'SELECT 1'
);
PREPARE stmt FROM @rename_model_index_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @old_status_index_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_llm_call_log'
     AND INDEX_NAME = 'ix_llm_call_log_status'
);
SET @new_status_index_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_llm_call_log'
     AND INDEX_NAME = 'ix_agent_mgmt_llm_call_log_status'
);
SET @rename_status_index_sql := IF(
  @old_status_index_exists = 1 AND @new_status_index_exists = 0,
  'ALTER TABLE `agent_mgmt_llm_call_log` RENAME INDEX ix_llm_call_log_status TO ix_agent_mgmt_llm_call_log_status',
  'SELECT 1'
);
PREPARE stmt FROM @rename_status_index_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @old_created_at_index_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_llm_call_log'
     AND INDEX_NAME = 'ix_llm_call_log_created_at'
);
SET @new_created_at_index_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_llm_call_log'
     AND INDEX_NAME = 'ix_agent_mgmt_llm_call_log_created_at'
);
SET @rename_created_at_index_sql := IF(
  @old_created_at_index_exists = 1 AND @new_created_at_index_exists = 0,
  'ALTER TABLE `agent_mgmt_llm_call_log` RENAME INDEX ix_llm_call_log_created_at TO ix_agent_mgmt_llm_call_log_created_at',
  'SELECT 1'
);
PREPARE stmt FROM @rename_created_at_index_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

ALTER TABLE `agent_mgmt_llm_call_log`
  COMMENT = 'LLM 调用明细表',
  MODIFY COLUMN `id` INT NOT NULL AUTO_INCREMENT,
  MODIFY COLUMN `run_id` VARCHAR(36) NOT NULL COMMENT '请求唯一标识，关联同一次处理的所有调用',
  MODIFY COLUMN `scenario_name` VARCHAR(200) NOT NULL DEFAULT 'unknown' COMMENT '场景名称',
  MODIFY COLUMN `agent_role` VARCHAR(200) NOT NULL COMMENT '调用角色：意图识别/规划Agent/专家名/轮询预编译/轮询评估',
  MODIFY COLUMN `call_index` INT NOT NULL COMMENT '本次请求内的LLM调用序号',
  MODIFY COLUMN `model` VARCHAR(100) NOT NULL DEFAULT 'unknown' COMMENT '模型名称',
  MODIFY COLUMN `status` ENUM('success','failed') NOT NULL COMMENT '最终状态（重试耗尽仍失败=failed）',
  MODIFY COLUMN `latency_ms` INT DEFAULT NULL COMMENT '耗时毫秒（从首次发起到最终响应），失败时可能为NULL',
  MODIFY COLUMN `retry_count` INT NOT NULL DEFAULT 0 COMMENT '重试次数（0=一次成功）',
  MODIFY COLUMN `error_type` VARCHAR(50) DEFAULT NULL COMMENT '失败时的错误分类：rate_limit/network/other',
  MODIFY COLUMN `error_msg` VARCHAR(500) DEFAULT NULL COMMENT '失败时的错误信息',
  MODIFY COLUMN `input_tokens` INT DEFAULT NULL COMMENT '输入token数（模型返回时记录）',
  MODIFY COLUMN `output_tokens` INT DEFAULT NULL COMMENT '输出token数（模型返回时记录）',
  MODIFY COLUMN `extra_data` TEXT DEFAULT NULL COMMENT '附加数据文本，如 {"system_id":"app01","alert_key":"A-001"}',
  MODIFY COLUMN `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '调用时间';

ALTER TABLE `agent_mgmt_execution_log`
  MODIFY COLUMN `run_id` VARCHAR(36) DEFAULT NULL COMMENT '请求唯一标识，关联 agent_mgmt_llm_call_log';
