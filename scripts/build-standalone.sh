#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "python (or python3) is required to build the standalone binary."
  exit 1
fi

ADD_DATA_SEP=":"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    ADD_DATA_SEP=";"
    ;;
esac

if ! "${PYTHON_BIN}" -c "import PyInstaller, requests, packaging" >/dev/null 2>&1; then
  "${PYTHON_BIN}" -m pip install . pyinstaller
fi

"${PYTHON_BIN}" -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name pb-cli \
  --runtime-hook scripts/pyinstaller_subprocess_env_hook.py \
  --add-data "plubo/templates${ADD_DATA_SEP}plubo/templates" \
  plubo/main.py

if [ -f "${ROOT_DIR}/dist/pb-cli.exe" ]; then
  echo "Standalone binary generated at: ${ROOT_DIR}/dist/pb-cli.exe"
else
  echo "Standalone binary generated at: ${ROOT_DIR}/dist/pb-cli"
fi
