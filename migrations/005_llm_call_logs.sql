SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `agent_mgmt_llm_call_log` (
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
  `extra_data` TEXT DEFAULT NULL COMMENT '附加数据文本，如 {"system_id":"app01","alert_key":"A-001"}',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '调用时间',
  PRIMARY KEY (`id`),
  KEY ix_agent_mgmt_llm_call_log_run_id (`run_id`),
  KEY ix_agent_mgmt_llm_call_log_scenario (`scenario_name`),
  KEY ix_agent_mgmt_llm_call_log_model (`model`),
  KEY ix_agent_mgmt_llm_call_log_status (`status`),
  KEY ix_agent_mgmt_llm_call_log_created_at (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LLM 调用明细表';

SET @execution_run_id_column_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_execution_log'
     AND COLUMN_NAME = 'run_id'
);
SET @execution_run_id_column_sql := IF(
  @execution_run_id_column_exists = 0,
  'ALTER TABLE `agent_mgmt_execution_log` ADD COLUMN `run_id` VARCHAR(36) DEFAULT NULL COMMENT ''请求唯一标识，关联 agent_mgmt_llm_call_log'' AFTER `id`',
  'SELECT 1'
);
PREPARE stmt FROM @execution_run_id_column_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @execution_run_id_index_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_execution_log'
     AND INDEX_NAME = 'ix_agent_mgmt_execution_log_run_id'
);
SET @execution_run_id_index_sql := IF(
  @execution_run_id_index_exists = 0,
  'ALTER TABLE `agent_mgmt_execution_log` ADD INDEX ix_agent_mgmt_execution_log_run_id (`run_id`)',
  'SELECT 1'
);
PREPARE stmt FROM @execution_run_id_index_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @llm_extra_data_column_exists := (
  SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'agent_mgmt_llm_call_log'
     AND COLUMN_NAME = 'extra_data'
);
SET @llm_extra_data_column_sql := IF(
  @llm_extra_data_column_exists = 0,
  'ALTER TABLE `agent_mgmt_llm_call_log` ADD COLUMN `extra_data` TEXT DEFAULT NULL COMMENT ''附加数据文本，如 {"system_id":"app01","alert_key":"A-001"}'' AFTER `output_tokens`',
  'SELECT 1'
);
PREPARE stmt FROM @llm_extra_data_column_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
