#!/usr/bin/env bash
set -euo pipefail

LABEL="com.lyratec.clash-sub-service"
PKG_ID="com.lyratec.clash-sub-service"
PLIST_FILE="/Library/LaunchDaemons/$LABEL.plist"
BIN_FILE="/usr/local/bin/clash-sub-service"
LIB_DIR="/usr/local/lib/clash-sub-service"
ETC_DIR="/usr/local/etc/clash-sub-service"
LOG_DIR="/usr/local/var/log/clash-sub-service"

echo "stopping LaunchDaemon if loaded..."
launchctl bootout system "$PLIST_FILE" >/dev/null 2>&1 || true

echo "removing installed files..."
rm -f "$PLIST_FILE"
rm -f "$BIN_FILE"
rm -rf "$LIB_DIR"
rm -rf "$ETC_DIR"
rm -rf "$LOG_DIR"

if pkgutil --pkgs | grep -qx "$PKG_ID"; then
  echo "forgetting pkg receipt..."
  pkgutil --forget "$PKG_ID" >/dev/null
fi

echo "uninstall complete"
