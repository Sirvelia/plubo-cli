#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to build the standalone binary."
  exit 1
fi

if ! python3 -c "import PyInstaller, requests, packaging" >/dev/null 2>&1; then
  python3 -m pip install . pyinstaller
fi

python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name pb-cli \
  --runtime-hook scripts/pyinstaller_subprocess_env_hook.py \
  --add-data "plubo/templates:plubo/templates" \
  plubo/main.py

echo "Standalone binary generated at: ${ROOT_DIR}/dist/pb-cli"
