"""Validate release-gate evidence; never grant approval automatically."""
import argparse
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlsplit

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
    seen_evidence = set()
    for item in items:
        if type(item.get("approved")) is not bool:
            raise ValueError("approval must be a boolean")
        evidence = item.get("evidence")
        reviewer = item.get("reviewer")
        reviewed_at = item.get("reviewed_at")
        if item["approved"]:
            if (not isinstance(reviewer, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.@-]{2,127}", reviewer)):
                raise ValueError("approved gate requires an accountable reviewer identifier")
            if not isinstance(reviewed_at, str) or not reviewed_at.endswith("Z"):
                raise ValueError("approved gate requires a UTC review timestamp")
            try:
                parsed_time = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("invalid review timestamp") from exc
            if parsed_time.tzinfo != timezone.utc or parsed_time.year < 2020:
                raise ValueError("review timestamp must be UTC and plausible")
            if parsed_time > datetime.now(timezone.utc) + timedelta(minutes=5):
                raise ValueError("review timestamp cannot be in the future")
            if not isinstance(evidence, str) or evidence != evidence.strip():
                raise ValueError("approved gate requires a canonical HTTPS evidence URL")
            try:
                parsed = urlsplit(evidence)
                host = parsed.hostname
                port = parsed.port
            except ValueError as exc:
                raise ValueError("invalid evidence URL") from exc
            if (parsed.scheme != "https" or not host or
                    host in ("localhost", "127.0.0.1", "::1") or
                    parsed.username is not None or parsed.password is not None or
                    port is not None or parsed.fragment or
                    not parsed.path.strip("/")):
                raise ValueError("approved gate requires a remote HTTPS evidence URL with a record path")
            if evidence in seen_evidence:
                raise ValueError("evidence URLs must be distinct per gate")
            seen_evidence.add(evidence)
        elif evidence is not None or reviewer is not None or reviewed_at is not None:
            raise ValueError("unapproved gates must not carry approval provenance")
    by_id = {item["id"]: item for item in items}
    security = by_id["independent_security_review"]
    maintainer = by_id["maintainer_release_approval"]
    if maintainer["approved"] and not security["approved"]:
        raise ValueError("final release approval requires prior independent security review")
    if security["approved"] and maintainer["approved"]:
        security_time = datetime.fromisoformat(security["reviewed_at"].replace("Z", "+00:00"))
        maintainer_time = datetime.fromisoformat(maintainer["reviewed_at"].replace("Z", "+00:00"))
        if maintainer_time <= security_time:
            raise ValueError("final release approval must follow independent security review")
        if security["reviewer"].casefold() == maintainer["reviewer"].casefold():
            raise ValueError("independent security reviewer must differ from release approver")
    if maintainer["approved"]:
        pending = sorted(item["id"] for item in items if not item["approved"])
        if pending:
            raise ValueError("final release approval requires every other gate approved: " + ", ".join(pending))
        maintainer_time = datetime.fromisoformat(maintainer["reviewed_at"].replace("Z", "+00:00"))
        for item in items:
            if item["id"] == "maintainer_release_approval":
                continue
            gate_time = datetime.fromisoformat(item["reviewed_at"].replace("Z", "+00:00"))
            if gate_time >= maintainer_time:
                raise ValueError("final release approval must follow all prerequisite reviews")
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
