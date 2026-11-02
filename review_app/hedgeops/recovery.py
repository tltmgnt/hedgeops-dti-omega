"""Offline recovery verification. No server or trading endpoints."""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .audit_manifest import verify_manifest
from .storage import Store

def check_recovery(database, manifest):
    db_path = Path(database)
    manifest_path = Path(manifest)
    if not db_path.is_file():
        return {"integrity_ok": False, "reason": "database missing"}
    if not manifest_path.is_file():
        return {"integrity_ok": False, "reason": "manifest missing"}
    # Do not instantiate Store until the database has been confirmed to exist.
    with sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            return {"integrity_ok": False, "reason": "SQLite integrity check failed"}
    store = Store(str(db_path))
    return verify_manifest(store, str(manifest_path))

def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify recovered HedgeOps database against a signed manifest")
    parser.add_argument("--database", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args(argv)
    try:
        result = check_recovery(args.database, args.manifest)
    except (ValueError, OSError, sqlite3.DatabaseError, json.JSONDecodeError) as exc:
        result = {"integrity_ok": False, "reason": str(exc)}
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("integrity_ok") else 1

if __name__ == "__main__":
    sys.exit(main())
