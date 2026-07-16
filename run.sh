#!/data/data/com.termux/files/usr/bin/env bash
set -uo pipefail
TOOLS_DIR="${HOME}/termux-video-tools"
PIDFILE="${TOOLS_DIR}/.pids"
ARIA2_LOG="${TOOLS_DIR}/aria2.log"
DOWNLOAD_DIR="${HOME}/storage/shared/Download"
mkdir -p "${DOWNLOAD_DIR}" "${TOOLS_DIR}"

start_aria2() {
  if [ -f "${PIDFILE}" ] && pgrep -a aria2c >/dev/null 2>&1; then
    echo "[aria2c] already running"
    return 0
  fi
  echo "[aria2c] starting..."
  nohup aria2c \
    --enable-rpc \
    --rpc-listen-all=false \
    --rpc-allow-origin-all \
    --dir="${DOWNLOAD_DIR}" \
    --max-concurrent-downloads=5 \
    --max-connection-per-server=4 \
    --split=4 \
    --min-split-size=1M \
    --rpc-listen-port=6800 \
    --log="${ARIA2_LOG}" \
    --log-level=warn \
    >/dev/null 2>&1 &
  echo $! >> "${PIDFILE}"
  sleep 0.5
  if pgrep -x aria2c >/dev/null 2>&1; then
    echo "[aria2c] started (log: ${ARIA2_LOG})"
  else
    echo "[aria2c] failed to start" >&2
    return 1
  fi
}

start_server() {
  echo "[server] starting web UI..."
  nohup "${TOOLS_DIR}/vidget" serve --port 8080 \
    >> "${TOOLS_DIR}/server.log" 2>&1 &
  echo $! >> "${PIDFILE}"
  echo "[server] launched on http://0.0.0.0:8080 (log: ${TOOLS_DIR}/server.log)"
}

stop_all() {
  echo "Stopping tracked processes..."
  if [ -f "${PIDFILE}" ]; then
    while read -r pid; do
      [ -z "$pid" ] && continue
      kill "$pid" 2>/dev/null || true
    done < "${PIDFILE}"
    rm -f "${PIDFILE}"
  fi
  pkill -x aria2c 2>/dev/null || true
  pkill -f "video_server.py --serve" 2>/dev/null || true
  echo "Stopped."
}

status_all() {
  echo "aria2c: $(pgrep -x aria2c >/dev/null 2>&1 && echo running || echo stopped)"
  if pgrep -f "video_server.py --serve" >/dev/null 2>&1; then
    echo "server: running"
  else
    echo "server: stopped"
  fi
  if [ -f "${PIDFILE}" ]; then
    echo "pidfile: ${PIDFILE}"
    echo "pids: $(tr '\n' ' ' < "${PIDFILE}")"
  else
    echo "pidfile: missing"
  fi
}

case "${1:-start}" in
  start)
    : > "${PIDFILE}"
    start_aria2 || true
    start_server || true
    echo "PIDs stored in ${PIDFILE}"
    ;;
  stop)
    stop_all
    ;;
  restart)
    stop_all
    sleep 1
    "$0" start
    ;;
  status)
    status_all
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
