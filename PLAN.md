# RuoYi 集成 Agent 管理：允许按功能重构表结构

## Summary
RuoYi 前端仍在 `E:\RuoYi-Cloud-master` 改造；Agent 管理后端迁移到 `E:\agent-mgmt-service`。Agent 管理相关表统一放入 RuoYi 的 `ry-cloud` 库，不再使用独立 `agent_mgmt` 库。表结构可按权限、审计、只读查看等功能需要调整，但必须兼容 MySQL 5.7 且不使用外键。

## Key Changes
- 后端服务：
  - 新建规范 FastAPI 项目 `E:\agent-mgmt-service`，目录按 `app/api`、`app/core`、`app/models`、`app/schemas`、`app/services`、`scripts`、`docs` 组织。
  - 重新设计 Agent 管理表结构，保留业务能力但去掉 SQLAlchemy 外键和数据库外键约束。
  - 表结构允许新增或调整字段，至少包含资源归属、审计、状态、版本、软删除或业务删除所需字段。
  - 建表/升级脚本必须兼容 MySQL 5.7，使用普通索引维护查询性能，由业务代码处理级联清理和一致性。
  - 创建、修改、状态变更、回滚等写操作从 Gateway 转发的 `user_id`、`username` 请求头识别当前用户。
  - `scope=mine` 返回本人创建资源；`scope=all` 返回全部资源。
  - 只有本人创建的 Agent/场景可编辑、删除、激活、停用、回滚；非本人创建只允许查看详情、列表和版本。
- RuoYi 前端：
  - 新增 4 个子菜单：Agent、场景、运营首页、执行日志。
  - Agent 和场景页面顶部增加“我的 / 所有”筛选，默认“我的”。
  - 非本人创建资源在“所有”视图中只读，操作按钮隐藏或禁用。
  - 前端 API 统一走 `/prod-api/agent-mgmt-api`。
  - 本次隐藏 Skill 重载功能，不接入 8200/8202。
- 数据库：
  - 新表创建在 `ry-cloud` 库。
  - 不迁移旧 `agent_mgmt` 库历史数据。
  - Agent 名称、场景名称继续全局唯一。
  - 表结构改动通过独立 SQL 脚本管理，例如 `sql/agent_mgmt_tables.sql` 或后端项目 `migrations/` 下的版本脚本。
- Gateway：
  - 新增 `/agent-mgmt-api/**` 路由，`StripPrefix=1`，转发到 `http://127.0.0.1:8300`。
  - 继续使用 RuoYi Gateway 鉴权过滤器转发 `user_id`、`username`。

## Public Interfaces
- 前端页面：
  - `/agent-mgmt/agents`
  - `/agent-mgmt/scenarios`
  - `/agent-mgmt/overview`
  - `/agent-mgmt/logs`
- 列表查询参数：
  - `scope=mine`
  - `scope=all`
- Agent/场景响应新增权限与归属信息：
  - `created_by_user_id`
  - `created_by_username`
  - `updated_by_user_id`
  - `updated_by_username`
  - `can_edit`
- Gateway 对外接口：
  - `/prod-api/agent-mgmt-api/health`
  - `/prod-api/agent-mgmt-api/agents/**`
  - `/prod-api/agent-mgmt-api/scenarios/**`
  - `/prod-api/agent-mgmt-api/logs/**`

## Test Plan
- SQL 验证：
  - 在 MySQL 5.7 执行建表脚本，确认无外键、无 MySQL 8 专属语法。
  - 检查唯一索引、普通索引、默认值和字符集。
- 后端权限验证：
  - 用户 A 创建资源后，在“我的”可完整操作。
  - 用户 B 在“所有”能查看用户 A 的资源，但写操作返回 403。
  - 缺失 `user_id` 请求头的写操作返回 401/403。
- 前端验证：
  - “我的 / 所有”筛选正常。
  - 非本人创建资源只读。
  - Agent、场景、运营首页、执行日志 4 个菜单可访问。
  - `npm run build:prod` 通过。
- 远端验证：
  - `192.168.0.142:8300/health` 正常。
  - Gateway `/agent-mgmt-api/health` 正常。
  - RuoYi 登录后通过 `/prod-api/agent-mgmt-api/**` 完成核心读写。

## Assumptions
- 可以为实现权限、审计、只读查看等功能调整 Agent 管理表结构。
- “我的”定义为本人创建资源，不按部门。
- “所有”显示全部 Agent/场景，但非本人创建只能查看。
- 不迁移旧 `agent_mgmt` 库历史数据。
- 本次仍不新增全局查看菜单，不接入 Skill 重载。
