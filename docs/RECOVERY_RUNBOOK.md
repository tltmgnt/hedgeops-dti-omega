# Recovery verification runbook

1. Retrieve the SQLite backup and the independently retained signed manifest from separately controlled storage.
2. Supply the original `HEDGEOPS_AUDIT_KEY` through your secret manager, not a committed file.
3. Run from `review_app`:

```sh
python -m hedgeops.recovery --database /restore/hedgeops.sqlite3 --manifest /secure/audit-manifest.json
```

The command returns JSON and exits **0** only if SQLite integrity and the signed record inventory match; otherwise it exits **1**. A missing database is not created. Do not resume service until verification passes and operational review is complete.

This is snapshot verification, not continuous ledger anchoring. Manifests must be preserved externally and protected against replacement. Verification may need read/write permission for schema inspection by the current `Store` implementation; run on an isolated copy. Test your organization-specific key rotation, retention, and restore procedures before production.
