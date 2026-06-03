# Agent 管理生产部署文档

适用发布包：`agent-mgmt-production-20260603145008.tar.gz`

## 发布内容

- Agent 管理后端服务代码。
- 数据库迁移：`001`、`004`、`005`、`006`、`007`。
- RuoYi 前端生产构建产物：`ruoyi-ui/dist`。
- RuoYi 前端 Agent 管理相关源码备份：`ruoyi-ui/source`。
- 菜单初始化 SQL：`deploy/sql/010_agent_mgmt_llm_stats_menu.sql`。
- 接口文档：`docs/api/public-scenario-runtime-apis.md`。

## 生产前提

- MySQL 5.7，数据库名通常为 `ry-cloud`。
- Agent-Mgmt-Service 监听端口 `8300`。
- RuoYi 网关已将 `/agent-mgmt-api/**` 转发到 Agent-Mgmt-Service，并 StripPrefix。
- Nginx/RuoYi 前端静态目录可被替换。
- 执行用户具备以下权限：
  - 修改 Agent-Mgmt-Service 部署目录。
  - 执行 MySQL DDL。
  - 替换 RuoYi 前端静态资源。
  - 重启 Agent-Mgmt-Service。

## 包结构

```text
agent-mgmt-production-20260603145008/
  backend/
    app/
    migrations/
    tests/
    docs/
    requirements.txt
    start.sh
  ruoyi-ui/
    dist/
    source/
  deploy/sql/
    010_agent_mgmt_llm_stats_menu.sql
  docs/deployment/
    production-deployment-20260603.md
  manifest.sha256
```

## 部署变量

按生产实际路径替换：

```bash
export PKG=/tmp/agent-mgmt-production-20260603145008.tar.gz
export WORK=/tmp/agent-mgmt-production-20260603145008
export AGENT_DIR=/opt/agent-mgmt-service
export RY_UI_STATIC_DIR=/opt/middleware-stack/data/nginx-html
export MYSQL_CONTAINER=mysql57
export MYSQL_DB='ry-cloud'
export MYSQL_USER='root'
export MYSQL_PASSWORD='生产环境MySQL密码'
```

## 1. 解包

```bash
mkdir -p "$WORK"
tar -xzf "$PKG" -C /tmp
cd "$WORK"
sha256sum -c manifest.sha256
```

## 2. 备份

```bash
ts=$(date +%Y%m%d%H%M%S)
mkdir -p "$AGENT_DIR/backups/release-$ts" /opt/ruoyi-ui-backups

cp -a "$AGENT_DIR/app" "$AGENT_DIR/migrations" "$AGENT_DIR/requirements.txt" "$AGENT_DIR/backups/release-$ts/"
cp -a "$RY_UI_STATIC_DIR" "/opt/ruoyi-ui-backups/nginx-html-$ts"

docker exec "$MYSQL_CONTAINER" sh -c \
  "mysqldump -u$MYSQL_USER -p'$MYSQL_PASSWORD' --default-character-set=utf8mb4 '$MYSQL_DB' \
   agent_mgmt_agent agent_mgmt_agent_category agent_mgmt_agent_version \
   agent_mgmt_execution_log agent_mgmt_llm_call_log \
   agent_mgmt_scenario agent_mgmt_scenario_version sys_menu" \
  > "/opt/ruoyi-ui-backups/agent-mgmt-db-$ts.sql"
```

如果生产环境还没有 `agent_mgmt_llm_call_log`，上面的 `mysqldump` 可能提示该表不存在；这是正常的，先备份已有 Agent 管理表即可。

## 3. 部署后端代码

```bash
rsync -av --delete backend/app/ "$AGENT_DIR/app/"
rsync -av backend/migrations/ "$AGENT_DIR/migrations/"
rsync -av backend/docs/ "$AGENT_DIR/docs/"
cp backend/requirements.txt "$AGENT_DIR/requirements.txt"
cp backend/start.sh "$AGENT_DIR/start.sh"
chmod +x "$AGENT_DIR/start.sh"
```

如生产虚拟环境尚未安装依赖：

```bash
cd "$AGENT_DIR"
.venv/bin/pip install -r requirements.txt
```

## 4. 执行数据库迁移

迁移均为 MySQL 5.7 兼容，并包含 `SET NAMES utf8mb4`。

```bash
for f in \
  migrations/001_create_agent_mgmt_tables.sql \
  migrations/004_agent_categories.sql \
  migrations/005_llm_call_logs.sql \
  migrations/006_fix_llm_call_log_comments.sql \
  migrations/007_rename_llm_call_log.sql \
  deploy/sql/010_agent_mgmt_llm_stats_menu.sql
do
  docker cp "$f" "$MYSQL_CONTAINER:/tmp/$(basename "$f")"
  docker exec "$MYSQL_CONTAINER" sh -c \
    "mysql -u$MYSQL_USER -p'$MYSQL_PASSWORD' --default-character-set=utf8mb4 '$MYSQL_DB' < /tmp/$(basename "$f")"
done
```

说明：

- 新环境会创建 `agent_mgmt_llm_call_log`。
- 已存在旧表 `llm_call_log` 的环境会通过 `007` 重命名为 `agent_mgmt_llm_call_log`，保留原有数据。
- `010_agent_mgmt_llm_stats_menu.sql` 会确保 Agent 管理下存在 `LLM 统计` 菜单。

## 5. 重启后端

如果生产使用 systemd：

```bash
systemctl restart agent-mgmt-service.service
systemctl is-active agent-mgmt-service.service
```

如果生产使用项目脚本：

```bash
cd "$AGENT_DIR"
./start.sh restart
./start.sh status
```

## 6. 部署前端静态资源

```bash
cd "$RY_UI_STATIC_DIR"
rm -rf index.html index.html.gz favicon.ico robots.txt html static styles
tar -C "$WORK/ruoyi-ui/dist" -czf - . | tar -xzf -
```

如果前端源码也需要同步到生产 RuoYi 源码目录，可执行：

```bash
export RY_UI_SOURCE_DIR=/opt/ruoyi-cloud-ops/source/ruoyi-ui
rsync -av ruoyi-ui/source/src/api/agentMgmt/ "$RY_UI_SOURCE_DIR/src/api/agentMgmt/"
rsync -av ruoyi-ui/source/src/views/agentMgmt/ "$RY_UI_SOURCE_DIR/src/views/agentMgmt/"
```

## 7. 验证

后端健康检查：

```bash
curl -fsS http://127.0.0.1:8300/health
```

LLM 统计接口：

```bash
curl -fsS 'http://127.0.0.1:8300/llm-stats/summary?days=7'
curl -fsS 'http://127.0.0.1:8300/llm-stats/by-scenario?days=7'
```

数据库结构：

```bash
docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" --default-character-set=utf8mb4 "$MYSQL_DB" -e "
SHOW TABLES LIKE 'agent_mgmt_llm_call_log';
SHOW TABLES LIKE 'llm_call_log';
SHOW INDEX FROM agent_mgmt_llm_call_log;
SELECT menu_name,path,component,visible,status FROM sys_menu WHERE path='llm-stats';
"
```

期望：

- `agent_mgmt_llm_call_log` 存在。
- `llm_call_log` 不存在。
- 索引名为 `ix_agent_mgmt_llm_call_log_*`。
- `LLM 统计` 菜单存在且组件为 `agentMgmt/llmStats/index`。

前端页面：

```bash
curl -I http://生产域名或IP/agent-mgmt/agents
curl -I http://生产域名或IP/agent-mgmt/scenarios
curl -I http://生产域名或IP/agent-mgmt/logs
curl -I http://生产域名或IP/agent-mgmt/llm-stats
```

登录 RuoYi 后手工确认：

- Agent 管理页分类标签正常。
- Agent 新建/复制/版本激活逻辑正常。
- 场景新建/复制、Planner/执行 Agent 抽屉分类标签可选。
- 执行日志为表格展示，详情可打开。
- LLM 统计页整体统计、场景维度、run_id 详情可用。

## 回滚

前端回滚：

```bash
rm -rf "$RY_UI_STATIC_DIR"
cp -a "/opt/ruoyi-ui-backups/nginx-html-$ts" "$RY_UI_STATIC_DIR"
```

后端回滚：

```bash
rsync -av --delete "$AGENT_DIR/backups/release-$ts/app/" "$AGENT_DIR/app/"
rsync -av "$AGENT_DIR/backups/release-$ts/migrations/" "$AGENT_DIR/migrations/"
cp "$AGENT_DIR/backups/release-$ts/requirements.txt" "$AGENT_DIR/requirements.txt"
systemctl restart agent-mgmt-service.service
```

数据库回滚需谨慎。若只需要兼容旧后端，可临时执行：

```sql
RENAME TABLE agent_mgmt_llm_call_log TO llm_call_log;
```

更彻底的数据库回滚应使用第 2 步生成的 `agent-mgmt-db-$ts.sql`，并在业务低峰期执行。

## 本次打包验证

- 后端测试：`python3 -m unittest discover -s tests`，36 个测试通过。
- 前端构建：`npm run build:prod` 通过。
- 前端构建存在 RuoYi 原有包体积 warning，不影响部署。
