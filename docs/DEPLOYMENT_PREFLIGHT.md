# Deployment security preflight

From `review_app/`, run `python -m hedgeops.preflight` to inspect configuration without opening a network socket. The command prints JSON findings and exits nonzero for detected errors.

Checks cover missing bearer tokens, non-loopback binding, public origin syntax/HTTPS, and missing audit signing keys. Loopback development without credentials is permitted with warnings. A configured non-loopback origin and token can pass automated checks but **does not imply production readiness**: a reviewed TLS reverse proxy, authentication/session design, rate limits, monitoring, and independent security approval are still required.

This is a configuration lint, not a secret-strength audit or a network/deployment verification.
