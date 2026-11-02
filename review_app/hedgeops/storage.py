"""Local SQLite persistence with unkeyed SHA-256 integrity checks.

Digests are not tamper-proof against anyone with database write access.
"""
import hashlib
import json
import sqlite3

def canonical(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False)

class Store:
    def __init__(self, path="hedgeops.sqlite3"):
        self.path = str(path)
        with self._db() as db:
            db.execute("CREATE TABLE IF NOT EXISTS decisions (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL, digest TEXT)")
            columns = {row[1] for row in db.execute("PRAGMA table_info(decisions)")}
            if "digest" not in columns:
                db.execute("ALTER TABLE decisions ADD COLUMN digest TEXT")

    def _db(self):
        return sqlite3.connect(self.path, timeout=10)

    def save(self, record):
        payload = canonical(record)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
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
            elif hashlib.sha256(payload.encode("utf-8")).hexdigest() != digest:
                invalid.append(rid)
        return {"total": len(rows), "valid": len(rows) - len(invalid) - len(legacy),
                "invalid_ids": invalid, "unverified_legacy_ids": legacy, "integrity_ok": not invalid and not legacy}
