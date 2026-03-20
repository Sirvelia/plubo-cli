#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/build-appimage.sh \
  --binary <path> \
  --version <version> \
  [--arch <x86_64|aarch64>] \
  [--output-dir <dir>]
USAGE
}

BINARY_PATH=""
VERSION=""
ARCH="x86_64"
OUTPUT_DIR="dist"
APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --binary)
      BINARY_PATH="$2"
      shift 2
      ;;
    --version)
      VERSION="$2"
      shift 2
      ;;
    --arch)
      ARCH="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [ -z "${BINARY_PATH}" ] || [ -z "${VERSION}" ]; then
  usage
  exit 1
fi

if [ ! -f "${BINARY_PATH}" ]; then
  echo "Binary not found: ${BINARY_PATH}"
  exit 1
fi

case "${ARCH}" in
  x86_64|aarch64)
    ;;
  *)
    echo "Unsupported AppImage architecture: ${ARCH}"
    exit 1
    ;;
esac

VERSION="${VERSION#v}"
mkdir -p "${OUTPUT_DIR}"

BUILD_ROOT="$(mktemp -d)"
trap 'rm -rf "${BUILD_ROOT}"' EXIT

APPDIR="${BUILD_ROOT}/AppDir"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/scalable/apps"

install -m 0755 "${BINARY_PATH}" "${APPDIR}/usr/bin/pb-cli"

cat > "${APPDIR}/AppRun" <<'APP_RUN'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${HERE}/usr/bin/pb-cli" "$@"
APP_RUN
chmod +x "${APPDIR}/AppRun"

cat > "${APPDIR}/pb-cli.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=pb-cli
Comment=pb-cli command-line tool
Exec=pb-cli
Icon=pb-cli
Terminal=true
Categories=Utility;Development;
DESKTOP

cat > "${APPDIR}/usr/share/icons/hicolor/scalable/apps/pb-cli.svg" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="16" fill="#1f2937"/>
  <text x="64" y="74" text-anchor="middle" font-size="44" fill="#f9fafb" font-family="monospace">&gt;_</text>
</svg>
SVG

ln -s "usr/share/icons/hicolor/scalable/apps/pb-cli.svg" "${APPDIR}/pb-cli.svg"

APPIMAGETOOL_BIN=""
if command -v appimagetool >/dev/null 2>&1; then
  APPIMAGETOOL_BIN="appimagetool"
else
  APPIMAGETOOL_BIN="${BUILD_ROOT}/appimagetool.AppImage"
  curl -fsSL "${APPIMAGETOOL_URL}" -o "${APPIMAGETOOL_BIN}"
  chmod +x "${APPIMAGETOOL_BIN}"
fi

OUT_APPIMAGE="${OUTPUT_DIR}/pb-cli-${VERSION}-${ARCH}.AppImage"
ARCH="${ARCH}" "${APPIMAGETOOL_BIN}" --appimage-extract-and-run "${APPDIR}" "${OUT_APPIMAGE}"

echo "Generated ${OUT_APPIMAGE}"
