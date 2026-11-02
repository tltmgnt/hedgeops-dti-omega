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
- [ ] Authenticate all dashboard and API surfaces, use authorization roles, and review CSRF/XSS/CORS controls.
- [ ] Deploy behind TLS with secure reverse proxy, rate limiting, request logging and operational alerting.
- [ ] Replace bare SQLite digests with externally anchored or keyed append-only audit controls.
- [ ] Implement schema migration, backup/restore drills, and data retention/deletion policy.
- [ ] Conduct threat modeling, dependency scanning, penetration testing and secret management review.
- [ ] Add API integration tests against a running service, load tests and recovery exercises.
- [ ] Obtain independent domain validation of capacity and risk constructs and document failure modes.
- [ ] Establish human approval governance, audit evidence and deployment rollback procedures.
- [ ] Confirm license and project ownership before external distribution.

## Safety invariant
Every response is a non-executable review record. Even `needs_review` is not an authorization to trade or commit resources. There are no transaction integrations.

## Merge policy
Keep the PR in draft until release-validation passes and a maintainer reviews the security and compatibility limitations. Green CI alone does not establish production readiness.
