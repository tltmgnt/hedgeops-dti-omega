"""Operator-exported audit manifest. Keep manifest outside the database host.

This module never transmits or uploads data. A separately retained signed
manifest detects deletion and rollback relative to that manifest.
"""
import hashlib
import hmac
import json
from pathlib import Path

from .storage import canonical

def _rows(store):
    with store._db() as db:
        return db.execute("SELECT id, created_at, payload, digest FROM decisions ORDER BY id").fetchall()

def export_manifest(store, destination):
    if not store.audit_key:
        raise ValueError("HEDGEOPS_AUDIT_KEY required for signed manifest")
    if not store.verify()["integrity_ok"]:
        raise ValueError("source integrity verification failed")
    rows = _rows(store)
    entries = [{"id": rid, "created_at": created, "digest": digest}
               for rid, created, _, digest in rows]
    body = {"schema_version": 1, "count": len(entries), "entries": entries}
    signature = hmac.new(store.audit_key, canonical(body).encode(), hashlib.sha256).hexdigest()
    manifest = {**body, "signature": "hmac-sha256:" + signature}
    target = Path(destination)
    if target.resolve() == Path(store.path).resolve():
        raise ValueError("manifest must not overwrite database")
    with target.open("x", encoding="utf-8") as output:
        json.dump(manifest, output, sort_keys=True, indent=2)
    return str(target)

def verify_manifest(store, source):
    if not store.audit_key:
        raise ValueError("HEDGEOPS_AUDIT_KEY required for manifest verification")
    manifest = json.loads(Path(source).read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("invalid manifest")
    if set(manifest) != {"schema_version", "count", "entries", "signature"}:
        raise ValueError("invalid manifest fields")
    body = {k: manifest[k] for k in ("schema_version", "count", "entries")}
    expected = "hmac-sha256:" + hmac.new(
        store.audit_key, canonical(body).encode(), hashlib.sha256).hexdigest()
    if not isinstance(manifest["signature"], str) or not hmac.compare_digest(expected, manifest["signature"]):
        return {"integrity_ok": False, "reason": "invalid signature"}
    if manifest["schema_version"] != 1 or not isinstance(manifest["entries"], list):
        return {"integrity_ok": False, "reason": "invalid manifest structure"}
    if type(manifest["count"]) is not int or manifest["count"] != len(manifest["entries"]):
        return {"integrity_ok": False, "reason": "invalid manifest count"}
    if not store.verify()["integrity_ok"]:
        return {"integrity_ok": False, "reason": "database record integrity failed"}
    actual = [{"id": rid, "created_at": created, "digest": digest}
              for rid, created, _, digest in _rows(store)]
    return {"integrity_ok": actual == manifest["entries"],
            "reason": "match" if actual == manifest["entries"] else "database differs from signed manifest",
            "expected_count": manifest["count"], "actual_count": len(actual)}
