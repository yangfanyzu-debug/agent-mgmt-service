#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${AGENT_MGMT_APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
ACTION="${1:-start}"

cd "$APP_DIR"

load_env() {
  if [ -f "$APP_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$APP_DIR/.env"
    set +a
  fi

  export AGENT_MGMT_DB_HOST="${AGENT_MGMT_DB_HOST:-43.135.134.42}"
  export AGENT_MGMT_DB_PORT="${AGENT_MGMT_DB_PORT:-3306}"
  export AGENT_MGMT_DB_NAME="${AGENT_MGMT_DB_NAME:-ry-cloud}"
  export AGENT_MGMT_DB_USER="${AGENT_MGMT_DB_USER:-root}"
  export AGENT_MGMT_DB_CHARSET="${AGENT_MGMT_DB_CHARSET:-utf8mb4}"

  PID_FILE="${AGENT_MGMT_PID_FILE:-$APP_DIR/agent-mgmt.pid}"
  LOG_FILE="${AGENT_MGMT_LOG_FILE:-$APP_DIR/agent-mgmt.log}"
  HOST="${AGENT_MGMT_HOST:-0.0.0.0}"
  PORT="${AGENT_MGMT_PORT:-8300}"
}

venv_python() {
  if [ -x "$APP_DIR/.venv/bin/python" ]; then
    echo "$APP_DIR/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    command -v python3
  else
    command -v python
  fi
}

is_running() {
  [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

start_service() {
  if is_running; then
    echo "agent-mgmt-service is already running, pid=$(cat "$PID_FILE")"
    return 0
  fi

  mkdir -p "$(dirname "$PID_FILE")" "$(dirname "$LOG_FILE")"

  local python_bin
  python_bin="$(venv_python)"
  nohup "$python_bin" -m uvicorn app.main:app --host "$HOST" --port "$PORT" >> "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  sleep 1

  if is_running; then
    echo "agent-mgmt-service started, pid=$(cat "$PID_FILE"), port=$PORT"
  else
    echo "agent-mgmt-service failed to start; see $LOG_FILE" >&2
    rm -f "$PID_FILE"
    return 1
  fi
}

stop_service() {
  if ! is_running; then
    echo "agent-mgmt-service is not running"
    rm -f "$PID_FILE"
    return 0
  fi

  local pid
  pid="$(cat "$PID_FILE")"
  kill "$pid"

  for _ in $(seq 1 20); do
    if ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$PID_FILE"
      echo "agent-mgmt-service stopped"
      return 0
    fi
    sleep 0.5
  done

  kill -9 "$pid" 2>/dev/null || true
  rm -f "$PID_FILE"
  echo "agent-mgmt-service force stopped"
}

status_service() {
  if is_running; then
    echo "agent-mgmt-service is running, pid=$(cat "$PID_FILE"), port=$PORT"
  else
    echo "agent-mgmt-service is not running"
    return 1
  fi
}

case "$ACTION" in
  start)
    load_env
    start_service
    ;;
  stop)
    load_env
    stop_service
    ;;
  restart)
    load_env
    stop_service
    start_service
    ;;
  status)
    load_env
    status_service
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}" >&2
    exit 2
    ;;
esac
