# HedgeOps Ω release-candidate readiness checklist

## Validated by CI
- [x] Standalone review application unit tests on Python 3.11–3.13.
- [x] Original-engine compatibility snapshot tests on Python 3.11–3.13.
- [x] Cross-system behavioral contract tests in separate Python processes.
- [x] No broker/trade/execute/approve routes in the review API (static guard).
- [x] Python bytecode compilation.
- [x] Offline deployment preflight unit tests and release-validation policy gates across Python 3.11–3.13.
- [x] Loopback Host validation, browser POST Origin checks, authenticated unsupported-method handling, and bounded request parsing tests.
- [x] Socket read timeout, 32-worker concurrency cap, overload 503 contract and recovery tests.

These checks demonstrate a **review candidate**, not production readiness. The temporal metrics are unvalidated proxies and agent summaries are not calibrated forecasts.

## Blocking before production
- [ ] Consolidate original nested package layout without retaining duplicate divergent domain models.
- [ ] Replace optional bearer-token protection with production-grade browser sessions, role-based authorization, and reviewed CSRF/XSS/CORS controls. Dashboard and API now enforce the configured bearer token; local tokenless mode remains possible.
- [ ] Deploy behind TLS with secure reverse proxy, total request deadlines, rate limiting, request logging and operational alerting. The app now has a 10-second socket read timeout and 32-worker cap, but no proxy-enforced total deadline or distributed rate limit.
- [ ] Establish externally anchored, append-only audit controls. Optional keyed HMAC digests and signed operator-exported manifests now exist, but neither automatically anchors to immutable external storage.
- [ ] Implement managed schema migrations, automated off-site backup/restore drills, and a data retention/deletion policy. Local verified backup and offline manifest recovery verification now have automated tests.
- [ ] Conduct threat modeling, dependency scanning, penetration testing and secret management review. CI preflight uses synthetic settings and does not validate a live deployment.
- [ ] Add load and concurrency tests, full deployment recovery exercises, and adversarial HTTP testing. Ephemeral live-HTTP integration tests and offline restore verification tests now run in CI.
- [ ] Obtain independent domain validation of capacity and risk constructs and document failure modes.
- [ ] Establish human approval governance, audit evidence and deployment rollback procedures.
- [ ] Confirm license and project ownership before external distribution.

## Safety invariant
Every response is a non-executable review record. Even `needs_review` is not an authorization to trade or commit resources. There are no transaction integrations.

## Current review gate evidence

- CI matrix: `.github/workflows/release-validation.yml` includes explicit deployment configuration policy checks.
- Local preflight: `python -m hedgeops.preflight` from `review_app/` (lint only; not production authorization).
- HTTP boundary tests: `review_app/tests/test_http.py` cover host, origin, request size, worker saturation and recovery.
- Operator handoff: `docs/SECURITY_REVIEW_HANDOFF.md`; independent sign-off remains outstanding.

## Merge policy
Keep the PR in draft until release-validation passes and a maintainer reviews the security and compatibility limitations. Green CI alone does not establish production readiness.

## Phase 43 identity groundwork (not production authorization)

The review app now defines an explicit deny-by-default role matrix in `hedgeops.authorization`: viewer (read), analyst (read and review-only writes), auditor (read and audit verification), administrator (all supported review-only operations). This matrix is a **policy specification only**, not yet enforced for ordinary API requests, because the application has no trusted browser-session identity provider. Client-supplied role headers must never be accepted as authentication. Setting `HEDGEOPS_REQUIRE_IDENTITY=1` intentionally rejects every request, including bearer-token requests, until a reviewed identity verifier is integrated. Local development behavior remains unchanged by default. The production identity release gate remains unapproved.

## Phase 44 deployment-security configuration contract

Set `HEDGEOPS_PRODUCTION_PREFLIGHT=1` to require a loopback backend, HTTPS public origin, strict identity mode, and explicit operator assertions for reviewed TLS proxy, rate limits, total request deadlines and request logging. Missing assertions fail the offline preflight. The `*_VERIFIED=1` environment flags are **untrusted operator claims**, not technical verification of a live proxy; the preflight does not inspect infrastructure or authenticate attestations. The existing local development preflight remains unchanged. The production deployment security gate remains blocked until independently verified external evidence exists.
