#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
SUB_PID=""
APP_PID=""
PYTHON_BIN="${PYTHON_BIN:-python3}"
CURL_BIN="${CURL_BIN:-curl}"

cleanup() {
  if [[ -n "$APP_PID" ]]; then
    kill "$APP_PID" >/dev/null 2>&1 || true
    wait "$APP_PID" 2>/dev/null || true
  fi
  if [[ -n "$SUB_PID" ]]; then
    kill "$SUB_PID" >/dev/null 2>&1 || true
    wait "$SUB_PID" 2>/dev/null || true
  fi
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

cp "$ROOT_DIR/tests/fixtures/subscription.txt" "$TMP_DIR/subscription.txt"

PORT_SUB="${PORT_SUB:-18081}"
PORT_APP="${PORT_APP:-19095}"
LOG_PATH="$TMP_DIR/app.log"
OUT_PATH="$TMP_DIR/out.yaml"
CFG_PATH="$TMP_DIR/config.yaml"

cat >"$CFG_PATH" <<EOF
subscription:
  url: "http://127.0.0.1:${PORT_SUB}/subscription.txt"
  timeout: 15
output:
  path: "${OUT_PATH}"
server:
  listen: "127.0.0.1"
  port: ${PORT_APP}
  refresh_interval: 1
clash:
  port: 1082
  allow_lan: true
logging:
  level: "INFO"
  format: "text"
  stdout: false
  color: false
  access_log: true
  file:
    enabled: true
    path: "${LOG_PATH}"
    rotate:
      type: "size"
      max_bytes: 1048576
      backup_count: 2
EOF

cd "$TMP_DIR"
"$PYTHON_BIN" -m http.server "$PORT_SUB" --bind 127.0.0.1 >/dev/null 2>&1 &
SUB_PID="$!"

cd "$ROOT_DIR"
PYTHONPATH=src "$PYTHON_BIN" -m cli serve -c "$CFG_PATH" >/dev/null 2>&1 &
APP_PID="$!"

for _ in $(seq 1 50); do
  if "$CURL_BIN" -fsS "http://127.0.0.1:${PORT_APP}/clash.yaml" -o "$TMP_DIR/served.yaml"; then
    break
  fi
  sleep 0.2
done

test -f "$TMP_DIR/served.yaml"
test -f "$LOG_PATH"
grep -q "后台刷新服务已启动\\|本地 HTTP 服务已启动\\|服务入口" "$LOG_PATH"
grep -q "订阅刷新成功" "$LOG_PATH"
grep -q "access path=/clash.yaml status=200" "$LOG_PATH"
diff -u "$ROOT_DIR/tests/fixtures/expected.yaml" "$TMP_DIR/served.yaml"
