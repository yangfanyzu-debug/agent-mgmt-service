SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `agent_mgmt_panorama_layer` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `description` VARCHAR(500) DEFAULT NULL,
  `display_order` INT NOT NULL DEFAULT 0,
  `color` VARCHAR(32) NOT NULL DEFAULT '#7F77DD',
  `show_label` TINYINT(1) NOT NULL DEFAULT 1,
  `style_config` TEXT DEFAULT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_agent_mgmt_panorama_layer_name` (`name`),
  KEY `ix_agent_mgmt_panorama_layer_order` (`display_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI SRE panorama layers';

CREATE TABLE IF NOT EXISTS `agent_mgmt_panorama_node` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `parent_id` INT DEFAULT NULL,
  `layer_id` INT DEFAULT NULL,
  `name` VARCHAR(160) NOT NULL,
  `description` VARCHAR(1000) DEFAULT NULL,
  `sort_order` INT NOT NULL DEFAULT 0,
  `data_binding_type` VARCHAR(20) NOT NULL DEFAULT 'none',
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_agent_mgmt_panorama_node_name` (`name`),
  KEY `ix_agent_mgmt_panorama_node_parent` (`parent_id`),
  KEY `ix_agent_mgmt_panorama_node_layer` (`layer_id`),
  KEY `ix_agent_mgmt_panorama_node_sort` (`parent_id`, `sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI SRE panorama nodes';

CREATE TABLE IF NOT EXISTS `agent_mgmt_panorama_tag` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `description` VARCHAR(500) DEFAULT NULL,
  `border_color` VARCHAR(32) NOT NULL DEFAULT '#F59E0B',
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_agent_mgmt_panorama_tag_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI SRE panorama tags';

CREATE TABLE IF NOT EXISTS `agent_mgmt_panorama_node_tag` (
  `node_id` INT NOT NULL,
  `tag_id` INT NOT NULL,
  `created_at` DATETIME NOT NULL,
  PRIMARY KEY (`node_id`, `tag_id`),
  KEY `ix_agent_mgmt_panorama_node_tag_tag` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI SRE panorama node tag relation';

CREATE TABLE IF NOT EXISTS `agent_mgmt_panorama_agent_slot` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `node_id` INT NOT NULL,
  `display_name` VARCHAR(160) NOT NULL,
  `match_name` VARCHAR(160) NOT NULL,
  `description` VARCHAR(1000) DEFAULT NULL,
  `sort_order` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_agent_mgmt_panorama_agent_slot_node` (`node_id`),
  KEY `ix_agent_mgmt_panorama_agent_slot_match` (`match_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI SRE panorama Agent slots';

CREATE TABLE IF NOT EXISTS `agent_mgmt_panorama_scenario_slot` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `node_id` INT NOT NULL,
  `display_name` VARCHAR(160) NOT NULL,
  `match_name` VARCHAR(160) NOT NULL,
  `description` VARCHAR(1000) DEFAULT NULL,
  `sort_order` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_agent_mgmt_panorama_scenario_slot_node` (`node_id`),
  KEY `ix_agent_mgmt_panorama_scenario_slot_match` (`match_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI SRE panorama scenario slots';

INSERT INTO `agent_mgmt_panorama_layer`
  (`id`, `name`, `description`, `display_order`, `color`, `show_label`, `style_config`, `created_at`, `updated_at`)
VALUES
  (1, 'AI SRE', '根节点所在层', 0, '#7F77DD', 0, NULL, NOW(), NOW()),
  (2, '运维场景', '一级场景节点层', 1, '#7F77DD', 1, NULL, NOW(), NOW()),
  (3, '多agent协同场景', '多Agent协同执行入口', 2, '#7F77DD', 1, NULL, NOW(), NOW()),
  (4, '规划/意图识别', '规划 Agent 所在层', 3, '#7F77DD', 1, NULL, NOW(), NOW()),
  (5, '应用级Agent', '应用领域专家 Agent', 4, '#7F77DD', 1, NULL, NOW(), NOW()),
  (6, '中间件Agent', '中间件专家 Agent', 5, '#7F77DD', 1, NULL, NOW(), NOW()),
  (7, '数据库Agent', '数据库专家 Agent', 6, '#7F77DD', 1, NULL, NOW(), NOW()),
  (8, '基础层Agent', '基础设施 Agent', 7, '#7F77DD', 1, NULL, NOW(), NOW())
ON DUPLICATE KEY UPDATE
  `id`=`id`;

INSERT INTO `agent_mgmt_panorama_tag`
  (`id`, `name`, `description`, `border_color`, `created_at`, `updated_at`)
VALUES
  (1, '存量', '已有的存量运维场景', '#F59E0B', NOW(), NOW()),
  (2, '增量', '新增的增量运维场景', '#F59E0B', NOW(), NOW())
ON DUPLICATE KEY UPDATE
  `id`=`id`;

INSERT INTO `agent_mgmt_panorama_node`
  (`id`, `parent_id`, `layer_id`, `name`, `description`, `sort_order`, `data_binding_type`, `created_at`, `updated_at`)
VALUES
  (1, NULL, 1, 'AI SRE', 'AI SRE 能力全景根节点', 0, 'none', NOW(), NOW()),
  (2, 1, 2, '告警分析', '围绕告警识别、分析、处置的运维场景', 10, 'none', NOW(), NOW()),
  (3, 2, 3, '告警根因分析场景', '多 Agent 协同完成告警根因分析', 10, 'scenario', NOW(), NOW()),
  (4, 3, 4, '规划Agent', '负责意图识别与专家调度', 10, 'agent', NOW(), NOW()),
  (5, 4, 5, '应用Agent', '负责应用侧日志、链路和恢复验证', 10, 'agent', NOW(), NOW()),
  (6, 4, 6, '中间件Agent', '负责中间件集群健康分析', 20, 'agent', NOW(), NOW())
ON DUPLICATE KEY UPDATE
  `id`=`id`;

INSERT INTO `agent_mgmt_panorama_node_tag`
  (`node_id`, `tag_id`, `created_at`)
VALUES
  (2, 1, NOW()),
  (3, 1, NOW())
ON DUPLICATE KEY UPDATE
  `created_at`=`created_at`;

INSERT INTO `agent_mgmt_panorama_scenario_slot`
  (`id`, `node_id`, `display_name`, `match_name`, `description`, `sort_order`, `created_at`, `updated_at`)
VALUES
  (1, 3, '告警源_102', 'alert_analysis', '匹配场景 scenario_name=alert_analysis', 10, NOW(), NOW())
ON DUPLICATE KEY UPDATE
  `id`=`id`;

INSERT INTO `agent_mgmt_panorama_agent_slot`
  (`id`, `node_id`, `display_name`, `match_name`, `description`, `sort_order`, `created_at`, `updated_at`)
VALUES
  (1, 4, '规划Agent_102', 'planner_agent', '匹配 Agent.agent_name=planner_agent', 10, NOW(), NOW()),
  (2, 5, '应用Agent_102', 'es_expert_agent', '匹配 Agent.agent_name=es_expert_agent', 10, NOW(), NOW())
ON DUPLICATE KEY UPDATE
  `id`=`id`;
