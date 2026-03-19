#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
ENTRY_SCRIPT="${ENTRY_SCRIPT:-$ROOT_DIR/src/cli.py}"
ENTRY_NAME="$(basename "$ENTRY_SCRIPT" .py)"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT_DIR/dist/nuitka}"
APP_NAME="${APP_NAME:-clash-sub-service}"
SKIP_INSTALL="${SKIP_INSTALL:-auto}"

project_version() {
  "$PYTHON_BIN" - <<'PY'
from pathlib import Path
import re

text = Path("pyproject.toml").read_text(encoding="utf-8")
match = re.search(r'^version\s*=\s*"([^"]+)"\s*$', text, re.MULTILINE)
if not match:
    raise SystemExit("version not found in pyproject.toml")
print(match.group(1))
PY
}

has_python_module() {
  "$PYTHON_BIN" - <<PY >/dev/null 2>&1
import importlib.util
import sys
sys.exit(0 if importlib.util.find_spec("$1") else 1)
PY
}

prepare_build_env() {
  mkdir -p "$OUTPUT_DIR"
  mkdir -p "$ROOT_DIR/.nuitka-home/Library/Caches" "$ROOT_DIR/.cache"
  export HOME="$ROOT_DIR/.nuitka-home"
  export XDG_CACHE_HOME="$ROOT_DIR/.cache"
  export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
}

cleanup_previous_build() {
  rm -rf \
    "$OUTPUT_DIR/$ENTRY_NAME.build" \
    "$OUTPUT_DIR/$ENTRY_NAME.dist" \
    "$OUTPUT_DIR/$ENTRY_NAME.app" \
    "$OUTPUT_DIR/$APP_NAME.build" \
    "$OUTPUT_DIR/$APP_NAME.dist" \
    "$OUTPUT_DIR/$APP_NAME.app"
}

ensure_python() {
  if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "python not found: $PYTHON_BIN" >&2
    exit 1
  fi
}

install_build_deps() {
  if has_python_module nuitka && has_python_module yaml && has_python_module requests && has_python_module watchdog; then
    return 0
  fi

  if [[ "$SKIP_INSTALL" == "1" || "$SKIP_INSTALL" == "true" ]]; then
    echo "missing build dependencies and installation is disabled" >&2
    exit 1
  fi

  "$PYTHON_BIN" -m pip install --upgrade pip
  "$PYTHON_BIN" -m pip install -e .
  "$PYTHON_BIN" -m pip install nuitka
}

build_nuitka_args() {
  cat <<EOF
--assume-yes-for-downloads
--standalone
--disable-cache=all
--no-deployment-flag=self-execution
--output-dir=$OUTPUT_DIR
--output-filename=$APP_NAME
--include-module=app
--include-module=cli
--include-module=exit_codes
--include-package=config
--include-package=core
--include-package=models
--include-package=service
--include-package=local_http
--include-package=app_logging
--include-package=requests
--include-package=watchdog
--include-package=yaml
--python-flag=no_site
--module-parameter=tk-inter=no
EOF
  if has_python_module colorlog; then
    printf '%s\n' "--include-package=colorlog"
  fi
  printf '%s\n' "$ENTRY_SCRIPT"
}
