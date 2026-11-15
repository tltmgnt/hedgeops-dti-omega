# Release-candidate evidence register — Phase 29

**Status: review candidate only. No production authorization.**

| Area | Automated evidence | Remaining independent gate |
| --- | --- | --- |
| Review-only behavior | Contract tests, no-execution-route CI guard | Domain-model validation and human approval governance |
| HTTP boundary | Host/Origin, parser, auth and overload tests | Production session/roles/CSRF design and adversarial testing |
| Availability | Socket timeout, 32-worker cap, 503 response tests | Reverse-proxy deadlines, distributed rate limits and load tests |
| Configuration | Preflight tests and release-validation policy gates | Live deployment audit, TLS, secrets management |
| Audit and recovery | Keyed audit, manifest and offline restore tests | Immutable external anchoring, off-site recovery drills |
| Integration | Legacy compatibility and cross-system contracts | Package consolidation, ownership and licensing |

The evidence register records what CI currently checks. It is not an attestation, a deployment approval, or a substitute for the unchecked items in `docs/RELEASE_CANDIDATE_CHECKLIST.md`.
