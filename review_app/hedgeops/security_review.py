"""Static independent-security-review evidence readiness checker."""
import json
from pathlib import Path

MAX_DOCUMENT_BYTES = 16384

REQUIRED = frozenset(("identity_sessions", "network_boundary", "audit_immutability",
                      "backup_recovery", "secrets_management", "adversarial_testing",
                      "domain_review"))


def inspect_security_review(path):
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result

    with Path(path).open("rb") as source:
        raw = source.read(MAX_DOCUMENT_BYTES + 1)
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise ValueError("security review register exceeds size limit")
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=no_duplicates,
                          parse_constant=lambda value: (_ for _ in ()).throw(
                              ValueError("non-finite JSON value: " + value)))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid UTF-8 JSON security review register") from exc
    if not isinstance(data, dict) or set(data) != {"schema_version", "status", "controls"}:
        raise ValueError("invalid security review register")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("unsupported security review schema")
    if not isinstance(data["controls"], list) or len(data["controls"]) != len(REQUIRED):
        raise ValueError("security review control count mismatch")
    seen = set()
    for control in data["controls"]:
        if not isinstance(control, dict) or set(control) != {"id", "description", "approved", "evidence"}:
            raise ValueError("invalid security review control")
        identifier = control["id"]
        if not isinstance(identifier, str) or identifier not in REQUIRED or identifier in seen:
            raise ValueError("unknown or duplicate security review control")
        seen.add(identifier)
        if not isinstance(control["description"], str) or not control["description"].strip():
            raise ValueError("missing security review description")
        if type(control["approved"]) is not bool or control["approved"] or control["evidence"] is not None:
            raise ValueError("independent review cannot be self-approved by CI")
    if seen != REQUIRED or data["status"] != "blocked":
        raise ValueError("independent review must remain blocked")
    return {"blocked": True, "controls": len(seen)}


def main():
    root = Path(__file__).resolve().parents[2]
    print(json.dumps(inspect_security_review(root / "docs" / "security-review-register.json")))


if __name__ == "__main__":
    main()
