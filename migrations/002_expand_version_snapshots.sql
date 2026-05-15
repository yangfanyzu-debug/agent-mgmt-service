ALTER TABLE `agent_mgmt_agent_version`
  ADD COLUMN `tags` VARCHAR(500) DEFAULT NULL AFTER `content`;

ALTER TABLE `agent_mgmt_scenario_version`
  ADD COLUMN `description` TEXT DEFAULT NULL AFTER `content`,
  ADD COLUMN `sub_type_hint` VARCHAR(500) DEFAULT NULL AFTER `description`,
  ADD COLUMN `keyword_hint` VARCHAR(500) DEFAULT NULL AFTER `sub_type_hint`,
  ADD COLUMN `skill_selector_dims` VARCHAR(500) DEFAULT NULL AFTER `keyword_hint`,
  ADD COLUMN `related_agents` TEXT DEFAULT NULL AFTER `skill_selector_dims`;
