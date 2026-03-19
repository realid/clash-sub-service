#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

PYTHONPATH=src "$PYTHON_BIN" -m unittest \
  tests.test_fetcher \
  tests.test_parser \
  tests.test_builder \
  tests.test_service \
  tests.test_server \
  tests.test_cli

PYTHON_BIN="$PYTHON_BIN" ./tests/test_smoke.sh
