# Signed audit manifests

With `HEDGEOPS_AUDIT_KEY` configured, operators can create a signed snapshot manifest of all currently stored records:

```python
from hedgeops.storage import Store
from hedgeops.audit_manifest import export_manifest, verify_manifest
store = Store("hedgeops.sqlite3")
export_manifest(store, "/separate/secure/location/audit-2026-11-01.json")
print(verify_manifest(store, "/separate/secure/location/audit-2026-11-01.json"))
```

Run from `review_app`. Save the manifest in independently controlled, immutable or append-only storage and preserve the signing key in a separate secret manager. Create manifests on a schedule and after recovery. Comparison is against one specific signed snapshot: changes after that snapshot require a new manifest. A missing manifest, compromised key, or attacker-controlled replacement manifest defeats this protection. No external upload, scheduled export, or remote anchoring is implemented.
