# Security policy

This repository is a deliberately small demo target. Never commit credentials or production data.

Report vulnerabilities through GitHub private vulnerability reporting when available. Do not include secrets in Issues, pull requests, logs or evidence bundles.

The demo deployment binds to `127.0.0.1` by default. The container runs as a non-root numeric user. Production use requires a hardened server, TLS, signed images, SBOM, network policy and durable secret management.
