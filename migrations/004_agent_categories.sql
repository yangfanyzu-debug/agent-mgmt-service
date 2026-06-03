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
