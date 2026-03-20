# Standalone `pb-cli` Binary

`pb-cli` can be distributed as a single executable file so target machines do not need Python installed.

## Build

Run on the OS you want to target:

```bash
./scripts/build-standalone.sh
```

Output binary:

```text
dist/pb-cli
```

## Install System-Wide

```bash
./scripts/install-standalone.sh
```

This installs the binary at:

```text
/usr/local/bin/pb-cli
```

## Verify

```bash
pb-cli --help
```

## Important

- Build per platform: Linux/macOS/Windows binaries are not interchangeable.
- Build on the same CPU architecture as the target (for example `amd64` vs `arm64`).

## Distribution Strategy

Channels for `pb-cli`:

- GitHub Releases: standalone binaries for Linux/macOS/Windows.
- AUR (`pb-cli-bin`): generated `PKGBUILD` + `.SRCINFO`.
- Custom apt repo: generated from `.deb` packages (`amd64` and `arm64`).
- AppImage (`x86_64`) for portable Linux usage.

## GitHub Actions Release Artifacts

The release workflow at `.github/workflows/release-binaries.yml` now generates:

- `pb-cli-linux-amd64`, `pb-cli-linux-arm64`
- `pb-cli-macos-amd64`, `pb-cli-macos-arm64`
- `pb-cli-windows-amd64.exe`
- `.deb` packages for Linux (`amd64`, `arm64`)
- AppImage (`x86_64`)
- AUR metadata (`PKGBUILD`, `.SRCINFO`)
- apt repository bundle (`pb-cli-apt-repo-<version>.tar.gz`)

## apt Repo via GitHub Pages

The same release workflow also deploys a live apt repository to GitHub Pages:

- Base URL: `https://<owner>.github.io/<repo>/apt`
- Distribution: `stable`
- Component: `main`

### One-Time Setup (User Machine)

```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://<owner>.github.io/<repo>/apt/pb-cli-archive-keyring.gpg \
  | sudo tee /etc/apt/keyrings/pb-cli-archive-keyring.gpg >/dev/null

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/pb-cli-archive-keyring.gpg] https://<owner>.github.io/<repo>/apt stable main" \
  | sudo tee /etc/apt/sources.list.d/pb-cli.list >/dev/null

sudo apt update
sudo apt install pb-cli
```

### Updates

After new releases are published, users get updates with:

```bash
sudo apt update
sudo apt upgrade
```

To ensure signed repository metadata is published, configure these GitHub secrets:

- `APT_GPG_PRIVATE_KEY`
- `APT_GPG_KEY_ID`
- `APT_GPG_PASSPHRASE` (if needed)

## Docker (No Python in Final Image)

Use a multi-stage build so Python is only in the builder stage:

```dockerfile
FROM python:3.12-slim AS pbcli-builder
WORKDIR /src
COPY . .
RUN ./scripts/build-standalone.sh

FROM wordpress:php8.2-apache
COPY --from=pbcli-builder /src/dist/pb-cli /usr/local/bin/pb-cli
RUN chmod +x /usr/local/bin/pb-cli
```
