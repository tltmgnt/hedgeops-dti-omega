# Audit key operations

Set `HEDGEOPS_AUDIT_KEY` to a high-entropy secret provided by a secret manager before starting the review service. Do not commit or store the key alongside the SQLite database. New records use `hmac-sha256:` digests. Unkeyed records remain readable but are flagged as unverified in keyed mode; do not silently treat them as keyed. Backups require the same audit key and reject records failing verification. Keep the key available for backup verification and recovery, with a controlled rotation plan.

**Limitations:** This is record-level tamper evidence, not an append-only ledger. It cannot detect row deletion, database rollback, or a writer who also possesses the key. External audit anchoring and off-site retention are still required before production.
