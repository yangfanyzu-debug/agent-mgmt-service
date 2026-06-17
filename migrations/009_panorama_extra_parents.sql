ALTER TABLE `agent_mgmt_panorama_node`
  ADD COLUMN `extra_parent_ids` TEXT DEFAULT NULL
  COMMENT 'JSON array of additional parent node IDs';
