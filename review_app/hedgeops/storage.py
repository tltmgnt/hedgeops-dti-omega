"""Local SQLite persistence with optional keyed audit integrity.

HMAC protects individual records only when the key is kept outside the DB.
It does not detect deletion, rollback, or malicious rewriting by a key holder.
"""
import hashlib
import hmac
import os
import json
import sqlite3
from pathlib import Path

def canonical(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False)

class Store:
    def __init__(self, path="hedgeops.sqlite3"):
        self.path = str(path)
        self.audit_key = os.environ.get("HEDGEOPS_AUDIT_KEY", "").encode("utf-8")
        with self._db() as db:
            db.execute("CREATE TABLE IF NOT EXISTS decisions (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL, digest TEXT)")
            columns = {row[1] for row in db.execute("PRAGMA table_info(decisions)")}
            if "digest" not in columns:
                db.execute("ALTER TABLE decisions ADD COLUMN digest TEXT")

    def _db(self):
        return sqlite3.connect(self.path, timeout=10)

    def _digest(self, payload):
        data = payload.encode("utf-8")
        if self.audit_key:
            return "hmac-sha256:" + hmac.new(self.audit_key, data, hashlib.sha256).hexdigest()
        return "sha256:" + hashlib.sha256(data).hexdigest()

    def save(self, record):
        payload = canonical(record)
        digest = self._digest(payload)
        with self._db() as db:
            db.execute("INSERT INTO decisions(id, created_at, payload, digest) VALUES(?, ?, ?, ?)",
                       (record["record_id"], record["created_at"], payload, digest))

    def get(self, record_id):
        with self._db() as db:
            row = db.execute("SELECT payload FROM decisions WHERE id=?", (record_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def list(self, limit=50):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        with self._db() as db:
            rows = db.execute("SELECT payload FROM decisions ORDER BY created_at DESC, id DESC LIMIT ?", (limit,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def verify(self):
        with self._db() as db:
            rows = db.execute("SELECT id, payload, digest FROM decisions").fetchall()
        invalid, legacy = [], []
        for rid, payload, digest in rows:
            if digest is None:
                legacy.append(rid)
            elif digest.startswith("hmac-sha256:"):
                if not self.audit_key or not hmac.compare_digest(self._digest(payload), digest):
                    invalid.append(rid)
            elif digest.startswith("sha256:") or len(digest) == 64:
                expected = "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
                if self.audit_key:
                    legacy.append(rid)
                elif not hmac.compare_digest(expected, digest if digest.startswith("sha256:") else "sha256:" + digest):
                    invalid.append(rid)
            else:
                invalid.append(rid)
        return {"total": len(rows), "valid": len(rows) - len(invalid) - len(legacy),
                "invalid_ids": invalid, "unverified_legacy_ids": legacy, "integrity_ok": not invalid and not legacy}

    def backup_verified(self, destination):
        """Create a consistent SQLite snapshot; reject damaged source or existing targets.

        This is a local operator action, not an HTTP endpoint. External integrity
        anchoring and encrypted off-site retention remain deployment requirements.
        """
        target = Path(destination)
        if target.resolve() == Path(self.path).resolve():
            raise ValueError("backup destination must differ from source")
        if not self.verify()["integrity_ok"]:
            raise ValueError("source audit integrity failed; backup refused")
        # Exclusive creation prevents accidental overwriting of an existing backup.
        with target.open("xb") as created:
            pass
        try:
            with self._db() as source, sqlite3.connect(str(target)) as backup:
                source.backup(backup)
            if not Store(str(target)).verify()["integrity_ok"]:
                raise ValueError("backup audit integrity failed")
            with sqlite3.connect(str(target)) as check:
                if check.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("backup SQLite integrity failed")
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        return str(target)
