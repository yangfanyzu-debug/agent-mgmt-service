ALTER TABLE `agent_mgmt_agent`
  ADD COLUMN `active_version` VARCHAR(40) DEFAULT NULL AFTER `version`,
  ADD COLUMN `active_content` MEDIUMTEXT DEFAULT NULL AFTER `active_version`,
  ADD COLUMN `active_tags` VARCHAR(500) DEFAULT NULL AFTER `active_content`;

ALTER TABLE `agent_mgmt_agent_version`
  ADD COLUMN `is_active` TINYINT(1) NOT NULL DEFAULT 0 AFTER `created_at`,
  ADD COLUMN `activated_by_user_id` BIGINT(20) DEFAULT NULL AFTER `is_active`,
  ADD COLUMN `activated_by_username` VARCHAR(100) DEFAULT NULL AFTER `activated_by_user_id`,
  ADD COLUMN `activated_at` DATETIME DEFAULT NULL AFTER `activated_by_username`,
  ADD INDEX `ix_agent_version_active` (`agent_id`, `is_active`);

UPDATE `agent_mgmt_agent`
   SET active_version = version,
       active_content = content,
       active_tags = tags
 WHERE active_version IS NULL;

INSERT INTO `agent_mgmt_agent_version`
  (agent_id, version, content, tags, created_by_user_id, created_by_username,
   created_at, is_active, activated_by_user_id, activated_by_username, activated_at)
SELECT a.id, a.active_version, a.active_content, a.active_tags,
       a.updated_by_user_id, a.updated_by_username, a.updated_at,
       1, a.updated_by_user_id, a.updated_by_username, a.updated_at
  FROM `agent_mgmt_agent` a
 WHERE a.active_version IS NOT NULL
   AND NOT EXISTS (
     SELECT 1
       FROM `agent_mgmt_agent_version` v
      WHERE v.agent_id = a.id
        AND v.version = a.active_version
   );

UPDATE `agent_mgmt_agent_version` v
JOIN `agent_mgmt_agent` a
  ON a.id = v.agent_id
 AND a.active_version = v.version
   SET v.is_active = 1
 WHERE v.is_active = 0;
