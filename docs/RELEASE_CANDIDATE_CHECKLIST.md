# HedgeOps Ω release-candidate readiness checklist

## Validated by CI
- [x] Standalone review application unit tests on Python 3.11–3.13.
- [x] Original-engine compatibility snapshot tests on Python 3.11–3.13.
- [x] Cross-system behavioral contract tests in separate Python processes.
- [x] No broker/trade/execute/approve routes in the review API (static guard).
- [x] Python bytecode compilation.

These checks demonstrate a **review candidate**, not production readiness. The temporal metrics are unvalidated proxies and agent summaries are not calibrated forecasts.

## Blocking before production
- [ ] Consolidate original nested package layout without retaining duplicate divergent domain models.
- [ ] Replace optional bearer-token protection with production-grade browser sessions, role-based authorization, and reviewed CSRF/XSS/CORS controls. Dashboard and API now enforce the configured bearer token; local tokenless mode remains possible.
- [ ] Deploy behind TLS with secure reverse proxy, rate limiting, request logging and operational alerting.
- [ ] Establish externally anchored, append-only audit controls. Optional keyed HMAC digests and signed operator-exported manifests now exist, but neither automatically anchors to immutable external storage.
- [ ] Implement managed schema migrations, automated off-site backup/restore drills, and a data retention/deletion policy. Local verified backup and offline manifest recovery verification now have automated tests.
- [ ] Conduct threat modeling, dependency scanning, penetration testing and secret management review.
- [ ] Add load and concurrency tests, full deployment recovery exercises, and adversarial HTTP testing. Ephemeral live-HTTP integration tests and offline restore verification tests now run in CI.
- [ ] Obtain independent domain validation of capacity and risk constructs and document failure modes.
- [ ] Establish human approval governance, audit evidence and deployment rollback procedures.
- [ ] Confirm license and project ownership before external distribution.

## Safety invariant
Every response is a non-executable review record. Even `needs_review` is not an authorization to trade or commit resources. There are no transaction integrations.

## Merge policy
Keep the PR in draft until release-validation passes and a maintainer reviews the security and compatibility limitations. Green CI alone does not establish production readiness.
