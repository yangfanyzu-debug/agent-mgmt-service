CREATE TABLE IF NOT EXISTS `agent_mgmt_agent` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `agent_name` VARCHAR(100) NOT NULL,
  `type` VARCHAR(20) NOT NULL,
  `content` MEDIUMTEXT NOT NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'draft',
  `tags` VARCHAR(500) DEFAULT NULL,
  `version` VARCHAR(40) NOT NULL DEFAULT 'v1',
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
  `created_by_user_id` BIGINT(20) NOT NULL,
  `created_by_username` VARCHAR(100) NOT NULL,
  `created_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  KEY ix_agent_version_agent_id (`agent_id`),
  KEY ix_agent_version_created_at (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent management agent versions';

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
  `created_by_user_id` BIGINT(20) NOT NULL,
  `created_by_username` VARCHAR(100) NOT NULL,
  `created_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  KEY ix_scenario_version_scenario_id (`scenario_id`),
  KEY ix_scenario_version_created_at (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent management scenario versions';

CREATE TABLE IF NOT EXISTS `agent_mgmt_execution_log` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `scenario_id` INT DEFAULT NULL,
  `scenario_name` VARCHAR(200) NOT NULL DEFAULT 'unknown',
  `log_name` VARCHAR(500) NOT NULL DEFAULT '',
  `extra_data` TEXT DEFAULT NULL,
  `remark` VARCHAR(500) DEFAULT NULL,
  `html_content` LONGTEXT DEFAULT NULL,
  `created_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  KEY ix_execution_log_scenario_id (`scenario_id`),
  KEY ix_execution_log_scenario_name (`scenario_name`),
  KEY ix_execution_log_created_at (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent management execution logs';
