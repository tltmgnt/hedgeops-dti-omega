"""Check that the release handoff explicitly preserves the NO_GO safety boundary."""
import argparse
import json
from pathlib import Path

from hedgeops.release_decision import decide_release

REQUIRED_PHRASES = (
    "NO_GO",
    "not authorized for merge or production deployment",
    "seven production release gates",
    "independent security review",
    "domain-model evidence",
    "explicit, separate maintainer authorization",
    "remain draft",
)


def check_handoff(root):
    root = Path(root)
    decision = decide_release(root)
    if decision["decision"] != "NO_GO" or decision["deploy_authorized"] or decision["merge_authorized"]:
        raise ValueError("release decision is not a safe NO_GO")
    document = (root / "docs" / "FINAL_RELEASE_DECISION.md").read_text(encoding="utf-8")
    missing = [phrase for phrase in REQUIRED_PHRASES if phrase not in document]
    if missing:
        raise ValueError("release handoff missing safety statements: " + ", ".join(missing))
    return {"handoff_consistent": True, "decision": "NO_GO", "production_ready": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify NO_GO release handoff consistency")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    print(json.dumps(check_handoff(args.root), sort_keys=True))


if __name__ == "__main__":
    main()
