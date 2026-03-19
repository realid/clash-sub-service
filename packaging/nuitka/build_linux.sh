#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

prepare_build_env
ensure_python
install_build_deps
cleanup_previous_build

NUITKA_ARGS=()
while IFS= read -r line; do
  NUITKA_ARGS+=("$line")
done < <(build_nuitka_args)

"$PYTHON_BIN" -m nuitka \
  --linux-icon="" \
  "${NUITKA_ARGS[@]}"

echo "build complete: $OUTPUT_DIR"
