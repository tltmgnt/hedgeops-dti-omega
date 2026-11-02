"""Offline verification of a separately retained audit manifest against a pinned digest.

The expected SHA-256 digest MUST come from an independent trusted channel.
A digest supplied by the same compromised host does not establish anchoring.
"""
import argparse
import hashlib
import json
from pathlib import Path

from .audit_manifest import verify_manifest
from .storage import Store


def check_anchor(database, manifest, expected_sha256):
    if (not isinstance(expected_sha256, str) or len(expected_sha256) != 64
            or any(char not in "0123456789abcdef" for char in expected_sha256)):
        raise ValueError("expected SHA-256 must be 64 lowercase hexadecimal characters")
    raw = Path(manifest).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        return {"integrity_ok": False, "reason": "manifest differs from independent anchor"}
    result = verify_manifest(Store(database), manifest)
    return {"integrity_ok": bool(result["integrity_ok"]),
            "reason": result.get("reason", "unknown"),
            "anchor_sha256": actual}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify offline audit manifest against independently retained digest")
    parser.add_argument("--database", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        result = check_anchor(args.database, args.manifest, args.expected_sha256)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        result = {"integrity_ok": False, "reason": str(exc)}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["integrity_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
