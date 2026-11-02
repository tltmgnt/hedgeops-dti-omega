"""Validate release-gate evidence; never grant approval automatically."""
import argparse
import json
from pathlib import Path

REQUIRED = {
    "identity_sessions_roles",
    "tls_proxy_rate_limits",
    "immutable_audit_retention",
    "backup_restore_drill",
    "independent_security_review",
    "domain_model_validation",
    "maintainer_release_approval",
}


def inspect_gates(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("release_type") != "production":
        raise ValueError("unsupported release-gate schema or release type")
    items = data.get("requirements")
    if not isinstance(items, list) or len(items) != len(REQUIRED):
        raise ValueError("missing or duplicate release requirements")
    ids = [item.get("id") for item in items if isinstance(item, dict)]
    if set(ids) != REQUIRED or len(ids) != len(REQUIRED):
        raise ValueError("release requirement IDs do not match policy")
    for item in items:
        if type(item.get("approved")) is not bool:
            raise ValueError("approval must be a boolean")
        evidence = item.get("evidence")
        if item["approved"] and (not isinstance(evidence, str) or not evidence.strip()):
            raise ValueError("approved gate requires an evidence reference")
    approved = all(item["approved"] for item in items)
    if data.get("status") != ("ready_for_manual_review" if approved else "blocked"):
        raise ValueError("release status inconsistent with requirements")
    return {"ready_for_manual_review": approved, "blocked": not approved,
            "outstanding": [item["id"] for item in items if not item["approved"]]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, default=Path(__file__).resolve().parents[2] / "docs/release-gates.json")
    parser.add_argument("--expect-blocked", action="store_true")
    args = parser.parse_args()
    result = inspect_gates(args.file)
    print(json.dumps(result, indent=2))
    return 0 if not args.expect_blocked or result["blocked"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
