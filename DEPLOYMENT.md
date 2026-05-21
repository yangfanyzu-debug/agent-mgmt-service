# Agent Management Service Deployment

## Package Contents

- `app/`: FastAPI service source code.
- `migrations/`: MySQL schema and upgrade SQL.
- `sql/`: Same SQL files copied for deployment convenience.
- `requirements.txt`: Python dependencies.
- `.env.example`: Runtime environment template.
- `start.sh`: Service management script with `start`, `stop`, `restart`, and `status`.

## Database

For a new database, execute:

```sql
SOURCE sql/001_create_agent_mgmt_tables.sql;
```

For an existing database that was created before this version, execute upgrade scripts in order when the columns do not already exist:

```sql
SOURCE sql/002_expand_version_snapshots.sql;
SOURCE sql/003_agent_version_activation.sql;
SOURCE sql/004_agent_categories.sql;
```

The service startup also performs safe column checks for these schema additions.

## Environment

Copy `.env.example` to `.env` and adjust the database values:

```bash
cp .env.example .env
vi .env
```

Common variables:

```bash
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=agent_mgmt
HOST=0.0.0.0
PORT=8300
```

## Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

chmod +x start.sh
./start.sh start
./start.sh status
```

Other commands:

```bash
./start.sh stop
./start.sh restart
```

Health check:

```bash
curl http://127.0.0.1:8300/health
```
