#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_BIN="${ROOT_DIR}/dist/pb-cli"
DEST_BIN="/usr/local/bin/pb-cli"

if [ ! -f "${SRC_BIN}" ]; then
  echo "Binary not found at ${SRC_BIN}. Build it first with scripts/build-standalone.sh"
  exit 1
fi

install_cmd=(install -m 0755 "${SRC_BIN}" "${DEST_BIN}")

if [ "$(id -u)" -ne 0 ]; then
  sudo "${install_cmd[@]}"
else
  "${install_cmd[@]}"
fi

echo "Installed ${DEST_BIN}"
echo "Try: pb-cli --help"
