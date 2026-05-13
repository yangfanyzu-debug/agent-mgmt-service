#!/bin/bash
cd /opt/agent-mgmt-service
source .venv/bin/activate
export AGENT_MGMT_DB_HOST=192.168.0.140
export AGENT_MGMT_DB_NAME=ry-cloud
export AGENT_MGMT_DB_USER=root
export AGENT_MGMT_DB_PASSWORD='MySQL57_20260327Aa1!'
exec .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8300
