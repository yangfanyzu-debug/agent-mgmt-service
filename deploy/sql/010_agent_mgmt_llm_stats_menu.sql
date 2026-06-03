SET NAMES utf8mb4;

SET @parent_id := (
  SELECT menu_id
    FROM sys_menu
   WHERE path = 'agent-mgmt'
      OR menu_name = 'Agent管理'
   ORDER BY parent_id ASC, order_num ASC
   LIMIT 1
);

SET @exists := (
  SELECT COUNT(*)
    FROM sys_menu
   WHERE parent_id = @parent_id
     AND path = 'llm-stats'
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
 WHERE parent_id = @parent_id
   AND path = 'llm-stats';
