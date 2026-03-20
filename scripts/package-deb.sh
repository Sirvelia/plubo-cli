#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/package-deb.sh \
  --binary <path> \
  --version <version> \
  --arch <amd64|arm64> \
  [--output-dir <dir>] \
  [--package-name <name>] \
  [--maintainer <name and email>] \
  [--description <text>]
USAGE
}

BINARY_PATH=""
VERSION=""
ARCH=""
OUTPUT_DIR="dist"
PACKAGE_NAME="pb-cli"
MAINTAINER="pb-cli maintainers <maintainers@example.com>"
DESCRIPTION="pb-cli standalone command-line tool"

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
    --package-name)
      PACKAGE_NAME="$2"
      shift 2
      ;;
    --maintainer)
      MAINTAINER="$2"
      shift 2
      ;;
    --description)
      DESCRIPTION="$2"
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

if [ -z "${BINARY_PATH}" ] || [ -z "${VERSION}" ] || [ -z "${ARCH}" ]; then
  usage
  exit 1
fi

if [ ! -f "${BINARY_PATH}" ]; then
  echo "Binary not found: ${BINARY_PATH}"
  exit 1
fi

if ! command -v dpkg-deb >/dev/null 2>&1; then
  echo "dpkg-deb is required to build .deb packages."
  exit 1
fi

case "${ARCH}" in
  amd64|arm64)
    ;;
  *)
    echo "Unsupported Debian architecture: ${ARCH}"
    exit 1
    ;;
esac

VERSION="${VERSION#v}"
mkdir -p "${OUTPUT_DIR}"

BUILD_ROOT="$(mktemp -d)"
trap 'rm -rf "${BUILD_ROOT}"' EXIT

PKG_ROOT="${BUILD_ROOT}/${PACKAGE_NAME}"
mkdir -p "${PKG_ROOT}/DEBIAN" "${PKG_ROOT}/usr/bin"

install -m 0755 "${BINARY_PATH}" "${PKG_ROOT}/usr/bin/pb-cli"

cat > "${PKG_ROOT}/DEBIAN/control" <<CONTROL
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: ${MAINTAINER}
Depends: libc6
Description: ${DESCRIPTION}
CONTROL

OUT_DEB="${OUTPUT_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "${PKG_ROOT}" "${OUT_DEB}" >/dev/null

echo "Generated ${OUT_DEB}"
