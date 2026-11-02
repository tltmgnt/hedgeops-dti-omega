"""Check that the release handoff explicitly preserves the NO_GO safety boundary."""
import argparse
import json
import re
import stat
from pathlib import Path

from hedgeops.release_decision import decide_release

MAX_HANDOFF_BYTES = 65536

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
    if root.is_symlink() or not root.is_dir():
        raise ValueError("release evidence root must be a regular non-symlink directory")
    docs = root / "docs"
    if docs.is_symlink() or not docs.is_dir():
        raise ValueError("release evidence docs must be a regular non-symlink directory")
    for filename in ("release-gates.json", "security-review-register.json",
                     "FINAL_RELEASE_DECISION.md"):
        candidate = docs / filename
        try:
            mode = candidate.lstat().st_mode
        except OSError as exc:
            raise ValueError("release evidence missing or inaccessible: " + filename) from exc
        if not stat.S_ISREG(mode):
            raise ValueError("release evidence must be a regular non-symlink file: " + filename)
    decision = decide_release(root)
    if decision["decision"] != "NO_GO" or decision["deploy_authorized"] or decision["merge_authorized"]:
        raise ValueError("release decision is not a safe NO_GO")
    with (docs / "FINAL_RELEASE_DECISION.md").open("rb") as source:
        raw = source.read(MAX_HANDOFF_BYTES + 1)
    if len(raw) > MAX_HANDOFF_BYTES:
        raise ValueError("release handoff exceeds size limit")
    try:
        document = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("release handoff is not valid UTF-8") from exc
    if not document.startswith("# Phase 50 — Final release decision handoff\n"):
        raise ValueError("release handoff missing canonical heading")
    if "**Automated decision: NO_GO.** The review candidate is not authorized for merge or production deployment." not in document:
        raise ValueError("release handoff missing explicit NO_GO decision statement")
    forbidden = re.compile(
        r'(?im)^\s*["\x27]?(?:merge_authorized|deploy_authorized|production_ready)["\x27]?\s*[:=]\s*["\x27]?true\b'
        r'|^\s*["\x27]?decision["\x27]?\s*[:=]\s*["\x27]?GO\b'
    )
    if forbidden.search(document):
        raise ValueError("release handoff contains contradictory authorization")
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
