#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/generate-aur-metadata.sh \
  --version <version> \
  --repo <owner/repo> \
  --x86_64-sha <sha256> \
  --aarch64-sha <sha256> \
  [--output-dir <dir>] \
  [--package-name <name>]
USAGE
}

VERSION=""
REPO_SLUG=""
SHA_X86_64=""
SHA_AARCH64=""
OUTPUT_DIR="dist/aur"
PACKAGE_NAME="pb-cli-bin"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --version)
      VERSION="$2"
      shift 2
      ;;
    --repo)
      REPO_SLUG="$2"
      shift 2
      ;;
    --x86_64-sha)
      SHA_X86_64="$2"
      shift 2
      ;;
    --aarch64-sha)
      SHA_AARCH64="$2"
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

if [ -z "${VERSION}" ] || [ -z "${REPO_SLUG}" ] || [ -z "${SHA_X86_64}" ] || [ -z "${SHA_AARCH64}" ]; then
  usage
  exit 1
fi

VERSION="${VERSION#v}"
mkdir -p "${OUTPUT_DIR}"

cat > "${OUTPUT_DIR}/PKGBUILD" <<PKGBUILD
pkgname=${PACKAGE_NAME}
pkgver=${VERSION}
pkgrel=1
pkgdesc='Standalone pb-cli binary'
arch=('x86_64' 'aarch64')
url='https://github.com/${REPO_SLUG}'
license=('GPL3')
depends=('glibc')
source_x86_64=("pb-cli::https://github.com/${REPO_SLUG}/releases/download/v\$pkgver/pb-cli-linux-amd64")
source_aarch64=("pb-cli::https://github.com/${REPO_SLUG}/releases/download/v\$pkgver/pb-cli-linux-arm64")
sha256sums_x86_64=('${SHA_X86_64}')
sha256sums_aarch64=('${SHA_AARCH64}')

package() {
  install -Dm755 "\$srcdir/pb-cli" "\$pkgdir/usr/bin/pb-cli"
}
PKGBUILD

cat > "${OUTPUT_DIR}/.SRCINFO" <<SRCINFO
pkgbase = ${PACKAGE_NAME}
	pkgdesc = Standalone pb-cli binary
	pkgver = ${VERSION}
	pkgrel = 1
	url = https://github.com/${REPO_SLUG}
	arch = x86_64
	arch = aarch64
	license = GPL3
	depends = glibc
	source_x86_64 = pb-cli::https://github.com/${REPO_SLUG}/releases/download/v${VERSION}/pb-cli-linux-amd64
	source_aarch64 = pb-cli::https://github.com/${REPO_SLUG}/releases/download/v${VERSION}/pb-cli-linux-arm64
	sha256sums_x86_64 = ${SHA_X86_64}
	sha256sums_aarch64 = ${SHA_AARCH64}

pkgname = ${PACKAGE_NAME}
SRCINFO

echo "Generated ${OUTPUT_DIR}/PKGBUILD"
echo "Generated ${OUTPUT_DIR}/.SRCINFO"
