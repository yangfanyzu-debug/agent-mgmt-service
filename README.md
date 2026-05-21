# Agent Management Service

FastAPI service for Agent and Scenario management, designed to be exposed by RuoYi Gateway.

## Local Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set AGENT_MGMT_DB_HOST=43.135.134.42
set AGENT_MGMT_DB_NAME=ry-cloud
set AGENT_MGMT_DB_USER=root
set AGENT_MGMT_DB_PASSWORD=your-password
uvicorn app.main:app --host 0.0.0.0 --port 8300
```

Gateway should forward `/agent-mgmt-api/**` to `http://127.0.0.1:8300` with `StripPrefix=1`.
