"""Conservative final release decision; automation cannot authorize deployment."""
import json
from pathlib import Path

from hedgeops.release_readiness import inspect_release_readiness


def decide_release(root):
    readiness = inspect_release_readiness(root)
    if readiness["production_ready"]:
        raise ValueError("automated release decision cannot authorize production")
    return {"decision": "NO_GO", "deploy_authorized": False,
            "merge_authorized": False,
            "reason": "independent security review and production approvals outstanding",
            "release_gates_blocked": readiness["release_gates_blocked"],
            "independent_review_blocked": readiness["independent_review_blocked"]}


def main():
    root = Path(__file__).resolve().parents[2]
    print(json.dumps(decide_release(root), sort_keys=True))


if __name__ == "__main__":
    main()
