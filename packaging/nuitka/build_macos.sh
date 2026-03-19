#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

prepare_build_env
ensure_python
install_build_deps
cleanup_previous_build
export COPYFILE_DISABLE=1

PKG_IDENTIFIER="${PKG_IDENTIFIER:-com.lyratec.clash-sub-service}"
PKG_VERSION="${PKG_VERSION:-$(project_version)}"
PKG_NAME="${PKG_NAME:-${APP_NAME}-${PKG_VERSION}.pkg}"
PAYLOAD_ROOT="$OUTPUT_DIR/pkg-root"
LIB_DIR="$PAYLOAD_ROOT/usr/local/lib/$APP_NAME"
BIN_DIR="$PAYLOAD_ROOT/usr/local/bin"
ETC_DIR="$PAYLOAD_ROOT/usr/local/etc/$APP_NAME"
LOG_DIR="$PAYLOAD_ROOT/usr/local/var/log/$APP_NAME"
DAEMON_DIR="$PAYLOAD_ROOT/Library/LaunchDaemons"
PLIST_NAME="com.lyratec.clash-sub-service.plist"
SCRIPTS_DIR="$ROOT_DIR/packaging/macos_scripts"

NUITKA_ARGS=()
while IFS= read -r line; do
  NUITKA_ARGS+=("$line")
done < <(build_nuitka_args)

"$PYTHON_BIN" -m nuitka "${NUITKA_ARGS[@]}"

DIST_DIR=""
while IFS= read -r candidate; do
  if [[ -f "$candidate/$APP_NAME" ]]; then
    DIST_DIR="$candidate"
    break
  fi
done < <(find "$OUTPUT_DIR" -maxdepth 1 -type d -name '*.dist' | sort)

if [[ -z "$DIST_DIR" || ! -d "$DIST_DIR" ]]; then
  echo "nuitka dist directory containing $APP_NAME not found under: $OUTPUT_DIR" >&2
  exit 1
fi

rm -rf "$PAYLOAD_ROOT"
mkdir -p "$LIB_DIR" "$BIN_DIR" "$ETC_DIR" "$LOG_DIR" "$DAEMON_DIR"
/usr/bin/ditto --noextattr --noqtn "$DIST_DIR" "$LIB_DIR"
/usr/bin/ditto --noextattr --noqtn "$ROOT_DIR/config.example.yaml" "$ETC_DIR/config.example.yaml"
/usr/bin/ditto --noextattr --noqtn "$ROOT_DIR/packaging/launchd/$PLIST_NAME" "$DAEMON_DIR/$PLIST_NAME"
xattr -cr "$DIST_DIR" "$ROOT_DIR/config.example.yaml" "$ROOT_DIR/packaging/launchd/$PLIST_NAME" >/dev/null 2>&1 || true
xattr -cr "$PAYLOAD_ROOT" >/dev/null 2>&1 || true

cat >"$BIN_DIR/$APP_NAME" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec /usr/local/lib/$APP_NAME/$APP_NAME "\$@"
EOF
chmod +x "$BIN_DIR/$APP_NAME"

/usr/bin/pkgbuild \
  --root "$PAYLOAD_ROOT" \
  --scripts "$SCRIPTS_DIR" \
  --identifier "$PKG_IDENTIFIER" \
  --version "$PKG_VERSION" \
  --install-location / \
  "$OUTPUT_DIR/$PKG_NAME"

echo "build complete: $OUTPUT_DIR/$PKG_NAME"
