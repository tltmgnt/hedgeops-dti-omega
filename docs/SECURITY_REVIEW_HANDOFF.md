# Phase 19 — security review handoff

**Scope:** review-only HedgeOps application on `integration/hedgeops-review-app-phase6`. This is not a trading or execution service. Keep PR #1 in draft until independent review and explicit maintainer approval.

## Existing controls and evidence

- Review-only decision contract: `review_app/hedgeops/contract.py`, `integration_contracts/`.
- HTTP authentication and request framing: `review_app/hedgeops/api.py`, `review_app/tests/test_http.py`.
- Record-level SHA-256 / optional HMAC audit: `review_app/hedgeops/storage.py`.
- Signed snapshot manifests: `review_app/hedgeops/audit_manifest.py`.
- Offline recovery verification: `review_app/hedgeops/recovery.py`, `review_app/tests/test_recovery.py`.
- Matrix validation: `.github/workflows/release-validation.yml`, plus independent review-app, legacy-compat, and integration-contracts workflows.

## Independent security review checklist

- [ ] Threat-model service exposure, database compromise, manifest replacement, key theft, and operator misuse.
- [ ] Verify production identity, sessions, roles, CSRF defenses, TLS termination, and proxy trust boundaries.
- [ ] Assess request smuggling, header parsing, rate limiting, denial-of-service, and concurrent writes.
- [ ] Validate secrets management, rotation, recovery and incident response for `HEDGEOPS_API_TOKEN` and `HEDGEOPS_AUDIT_KEY`.
- [ ] Verify off-host immutable retention of manifests and backups; simulate deletion, rollback, stale manifests, and lost keys.
- [ ] Review schema migrations, retention/deletion obligations, and restoration with live workloads.
- [ ] Run static analysis, dependency review, penetration tests, and independent domain-model validation.
- [ ] Confirm licensing, maintainership, code ownership, and change approval.

## Recovery drill (isolated environment)

1. Configure a secret-manager-supplied `HEDGEOPS_AUDIT_KEY` and generate review records.
2. Export a signed manifest to an independently controlled location using `export_manifest`.
3. Create a verified SQLite backup using `Store.backup_verified`.
4. Restore the backup in an isolated directory.
5. Run `python -m hedgeops.recovery --database <restored.db> --manifest <retained.json>` from `review_app`; require exit 0.
6. Delete a record from a *disposable copy* and repeat verification; require exit 1.
7. Record evidence, operators, timestamps, backup age, key version, and remediation outcome in the external change-management system.

**Limitations:** HMAC and signed manifests provide point-in-time evidence only when secrets and manifest copies remain independent. They cannot establish a continuous tamper-proof ledger. No production deployment, external anchoring, managed secret rotation, or scheduled export has been configured.

## Merge gate

Require green CI on the proposed merge SHA, completed independent security review, domain-owner acceptance, documented rollback, and explicit maintainer approval. Green tests alone are insufficient.
