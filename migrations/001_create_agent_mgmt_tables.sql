SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `agent_mgmt_agent` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `agent_name` VARCHAR(100) NOT NULL,
  `type` VARCHAR(20) NOT NULL,
  `content` MEDIUMTEXT NOT NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'draft',
  `tags` VARCHAR(500) DEFAULT NULL,
  `version` VARCHAR(40) NOT NULL DEFAULT 'v1',
  `active_version` VARCHAR(40) DEFAULT NULL,
  `active_content` MEDIUMTEXT DEFAULT NULL,
  `active_tags` VARCHAR(500) DEFAULT NULL,
  `created_by_user_id` BIGINT(20) NOT NULL,
  `created_by_username` VARCHAR(100) NOT NULL,
  `updated_by_user_id` BIGINT(20) NOT NULL,
  `updated_by_username` VARCHAR(100) NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY uq_agent_name (`agent_name`),
  KEY ix_agent_creator (`created_by_user_id`),
  KEY ix_agent_status (`status`),
  KEY ix_agent_type (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent management agents';

CREATE TABLE IF NOT EXISTS `agent_mgmt_agent_version` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `agent_id` INT NOT NULL,
  `version` VARCHAR(40) NOT NULL,
  `content` MEDIUMTEXT NOT NULL,
  `tags` VARCHAR(500) DEFAULT NULL,
  `created_by_user_id` BIGINT(20) NOT NULL,
  `created_by_username` VARCHAR(100) NOT NULL,
  `created_at` DATETIME NOT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT 0,
  `activated_by_user_id` BIGINT(20) DEFAULT NULL,
  `activated_by_username` VARCHAR(100) DEFAULT NULL,
  `activated_at` DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ix_agent_version_agent_id (`agent_id`),
  KEY ix_agent_version_active (`agent_id`, `is_active`),
  KEY ix_agent_version_created_at (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent management agent versions';

CREATE TABLE IF NOT EXISTS `agent_mgmt_agent_category` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `parent_id` INT DEFAULT NULL,
  `category_code` VARCHAR(100) NOT NULL,
  `category_name` VARCHAR(100) NOT NULL,
  `sort_order` INT NOT NULL DEFAULT 0,
  `status` VARCHAR(20) NOT NULL DEFAULT 'active',
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY uq_agent_category_code (`category_code`),
  KEY ix_agent_category_parent (`parent_id`),
  KEY ix_agent_category_status (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent management category tree';

INSERT INTO `agent_mgmt_agent_category`
  (`id`, `parent_id`, `category_code`, `category_name`, `sort_order`, `status`, `created_at`, `updated_at`)
VALUES
  (1, NULL, 'ops', '运维告警', 10, 'active', NOW(), NOW()),
  (2, NULL, 'data_processing', '数据处理', 20, 'active', NOW(), NOW()),
  (3, NULL, 'content_generation', '内容生成', 30, 'active', NOW(), NOW()),
  (4, NULL, 'workflow', '工作流', 40, 'active', NOW(), NOW()),
  (5, NULL, 'integration', '集成', 50, 'active', NOW(), NOW()),
  (6, NULL, 'custom', '自定义', 60, 'active', NOW(), NOW()),
  (101, 1, 'alert_analysis', '告警分析', 10, 'active', NOW(), NOW()),
  (102, 1, 'notification', '通知', 20, 'active', NOW(), NOW()),
  (201, 2, 'log_processing', '日志处理', 10, 'active', NOW(), NOW()),
  (202, 2, 'metric_analysis', '指标分析', 20, 'active', NOW(), NOW())
ON DUPLICATE KEY UPDATE
  `parent_id`=VALUES(`parent_id`),
  `category_name`=VALUES(`category_name`),
  `sort_order`=VALUES(`sort_order`),
  `status`=VALUES(`status`),
  `updated_at`=VALUES(`updated_at`);

CREATE TABLE IF NOT EXISTS `agent_mgmt_scenario` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `scenario_name` VARCHAR(100) NOT NULL,
  `description` TEXT DEFAULT NULL,
  `sub_type_hint` VARCHAR(500) DEFAULT NULL,
  `keyword_hint` VARCHAR(500) DEFAULT NULL,
  `skill_selector_dims` VARCHAR(500) DEFAULT NULL,
  `related_agents` TEXT NOT NULL,
  `content` MEDIUMTEXT DEFAULT NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'draft',
  `version` VARCHAR(40) NOT NULL DEFAULT 'v1',
  `created_by_user_id` BIGINT(20) NOT NULL,
  `created_by_username` VARCHAR(100) NOT NULL,
  `updated_by_user_id` BIGINT(20) NOT NULL,
  `updated_by_username` VARCHAR(100) NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY uq_scenario_name (`scenario_name`),
  KEY ix_scenario_creator (`created_by_user_id`),
  KEY ix_scenario_status (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent management scenarios';

CREATE TABLE IF NOT EXISTS `agent_mgmt_scenario_version` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `scenario_id` INT NOT NULL,
  `version` VARCHAR(40) NOT NULL,
  `content` MEDIUMTEXT NOT NULL,
  `description` TEXT DEFAULT NULL,
  `sub_type_hint` VARCHAR(500) DEFAULT NULL,
  `keyword_hint` VARCHAR(500) DEFAULT NULL,
  `skill_selector_dims` VARCHAR(500) DEFAULT NULL,
  `related_agents` TEXT DEFAULT NULL,
  `created_by_user_id` BIGINT(20) NOT NULL,
  `created_by_username` VARCHAR(100) NOT NULL,
  `created_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  KEY ix_scenario_version_scenario_id (`scenario_id`),
  KEY ix_scenario_version_created_at (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent management scenario versions';

CREATE TABLE IF NOT EXISTS `agent_mgmt_execution_log` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `run_id` VARCHAR(36) DEFAULT NULL COMMENT '请求唯一标识，关联 agent_mgmt_llm_call_log',
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
