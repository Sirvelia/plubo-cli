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
