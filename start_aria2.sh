#!/data/data/com.termux/files/usr/bin/env bash
# Start aria2c with RPC enabled. Adjust RPC port, dir, and concurrency as needed.
DEFAULT_DIR="${HOME}/storage/shared/Download"
mkdir -p "$DEFAULT_DIR"
ARIA2_PORT=6800
ARIA2_LOG="${HOME}/termux-video-tools/aria2.log"

echo "Starting aria2c RPC on port $ARIA2_PORT, downloads dir: $DEFAULT_DIR"
nohup aria2c --enable-rpc --rpc-listen-all=false --rpc-allow-origin-all \
  --dir="$DEFAULT_DIR" --max-concurrent-downloads=5 --max-connection-per-server=4 \
  --split=4 --min-split-size=1M --rpc-listen-port=${ARIA2_PORT} \
  --log="$ARIA2_LOG" --log-level=warn 2>/dev/null &
sleep 0.5
echo "aria2c started (check $ARIA2_LOG)."
