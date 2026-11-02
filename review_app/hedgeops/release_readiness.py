"""Consolidated offline release evidence readiness: no approvals are granted."""
import json
from pathlib import Path

from hedgeops.security_review import inspect_security_review
from scripts.check_release_gates import inspect_gates


def inspect_release_readiness(root):
    root = Path(root)
    gates = inspect_gates(root / "docs" / "release-gates.json")
    security = inspect_security_review(root / "docs" / "security-review-register.json")
    if not gates["blocked"] or not security["blocked"]:
        raise ValueError("production evidence must remain blocked")
    return {"production_ready": False, "release_gates_blocked": True,
            "independent_review_blocked": True,
            "release_gate_count": 7, "security_control_count": security["controls"]}


def main():
    root = Path(__file__).resolve().parents[2]
    print(json.dumps(inspect_release_readiness(root), sort_keys=True))


if __name__ == "__main__":
    main()
