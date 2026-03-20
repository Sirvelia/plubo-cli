#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/generate-apt-repo.sh \
  --deb <path> [--deb <path> ...] \
  [--repo-dir <dir>] \
  [--codename <name>] \
  [--component <name>] \
  [--origin <name>] \
  [--label <name>] \
  [--description <text>]

Optional signing env vars:
  APT_GPG_PRIVATE_KEY   ASCII-armored key or base64-encoded key
  APT_GPG_KEY_ID        gpg key id or fingerprint
  APT_GPG_PASSPHRASE    optional passphrase
USAGE
}

REPO_DIR="dist/apt-repo"
CODENAME="stable"
COMPONENT="main"
ORIGIN="pb-cli"
LABEL="pb-cli"
DESCRIPTION="pb-cli apt repository"
DEBS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --deb)
      DEBS+=("$2")
      shift 2
      ;;
    --repo-dir)
      REPO_DIR="$2"
      shift 2
      ;;
    --codename)
      CODENAME="$2"
      shift 2
      ;;
    --component)
      COMPONENT="$2"
      shift 2
      ;;
    --origin)
      ORIGIN="$2"
      shift 2
      ;;
    --label)
      LABEL="$2"
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

if [ "${#DEBS[@]}" -eq 0 ]; then
  usage
  exit 1
fi

if ! command -v dpkg-scanpackages >/dev/null 2>&1; then
  echo "dpkg-scanpackages is required. Install package: dpkg-dev"
  exit 1
fi

if ! command -v apt-ftparchive >/dev/null 2>&1; then
  echo "apt-ftparchive is required. Install package: apt-utils"
  exit 1
fi

mkdir -p "${REPO_DIR}"
rm -rf "${REPO_DIR}/pool" "${REPO_DIR}/dists"

ARCHES=()

for deb in "${DEBS[@]}"; do
  if [ ! -f "${deb}" ]; then
    echo "Deb package not found: ${deb}"
    exit 1
  fi

  pkg_name="$(dpkg-deb -f "${deb}" Package)"
  pkg_arch="$(dpkg-deb -f "${deb}" Architecture)"
  ARCHES+=("${pkg_arch}")

  target_dir="${REPO_DIR}/pool/${COMPONENT}/${pkg_name:0:1}/${pkg_name}"
  mkdir -p "${target_dir}"
  cp "${deb}" "${target_dir}/"
done

mapfile -t unique_arches < <(printf '%s\n' "${ARCHES[@]}" | sort -u)

for arch in "${unique_arches[@]}"; do
  bin_dir="${REPO_DIR}/dists/${CODENAME}/${COMPONENT}/binary-${arch}"
  mkdir -p "${bin_dir}"

  (
    cd "${REPO_DIR}"
    dpkg-scanpackages --arch "${arch}" "pool/${COMPONENT}" /dev/null > "dists/${CODENAME}/${COMPONENT}/binary-${arch}/Packages"
  )

  gzip -9c "${bin_dir}/Packages" > "${bin_dir}/Packages.gz"
done

release_file="${REPO_DIR}/dists/${CODENAME}/Release"
architectures_line="$(printf '%s ' "${unique_arches[@]}")"
architectures_line="${architectures_line%% }"

{
  echo "Origin: ${ORIGIN}"
  echo "Label: ${LABEL}"
  echo "Suite: ${CODENAME}"
  echo "Codename: ${CODENAME}"
  echo "Date: $(LC_ALL=C date -Ru)"
  echo "Architectures: ${architectures_line}"
  echo "Components: ${COMPONENT}"
  echo "Description: ${DESCRIPTION}"
  (
    cd "${REPO_DIR}"
    apt-ftparchive release "dists/${CODENAME}" | sed '1{/^Date:/d;}'
  )
} > "${release_file}"

if [ -n "${APT_GPG_PRIVATE_KEY:-}" ] && [ -n "${APT_GPG_KEY_ID:-}" ]; then
  GNUPGHOME_DIR="$(mktemp -d)"
  trap 'rm -rf "${GNUPGHOME_DIR}"' EXIT
  export GNUPGHOME="${GNUPGHOME_DIR}"
  chmod 700 "${GNUPGHOME}"

  if ! printf '%s' "${APT_GPG_PRIVATE_KEY}" | gpg --batch --import >/dev/null 2>&1; then
    printf '%s' "${APT_GPG_PRIVATE_KEY}" | base64 --decode | gpg --batch --import >/dev/null
  fi

  gpg_sign_args=(--batch --yes --pinentry-mode loopback --default-key "${APT_GPG_KEY_ID}")
  if [ -n "${APT_GPG_PASSPHRASE:-}" ]; then
    gpg_sign_args+=(--passphrase "${APT_GPG_PASSPHRASE}")
  fi

  gpg "${gpg_sign_args[@]}" --armor --detach-sign --output "${REPO_DIR}/dists/${CODENAME}/Release.gpg" "${release_file}"
  gpg "${gpg_sign_args[@]}" --clearsign --output "${REPO_DIR}/dists/${CODENAME}/InRelease" "${release_file}"

  echo "Generated signed apt repository in ${REPO_DIR}"
else
  echo "Generated unsigned apt repository in ${REPO_DIR}"
fi
