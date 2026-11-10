"""Offline curriculum answer key. Synthetic checks, never operational approval."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
# The maintained package is at repository root; src/ contains legacy snapshots.
sys.path.insert(0, str(ROOT))
CASES = []

def check(name, actual, expected):
    passed = actual == expected
    CASES.append({"case": name, "actual": actual, "expected": expected, "passed": passed})
    if not passed:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")

def rejects(name, call, error=ValueError):
    try:
        call()
    except error:
        check(name, error.__name__, error.__name__)
    else:
        raise AssertionError(f"{name}: expected {error.__name__}")




def run():
    from unittest.mock import patch
    from hedgeops.engine import evaluate_decision
    from hedgeops.models import DecisionRequest, AgentAssessment, AgentRole, RiskFlag, Severity
    request = DecisionRequest("Synthetic review only")
    rows = [AgentAssessment(role,"Synthetic assessment",.5) for role in AgentRole]
    with patch("hedgeops.engine.assess_all",return_value=rows):
        r = evaluate_decision(request)
    check("all roles with no flags still require review", r.status.value, "needs_review")
    check("human approval stays required", r.human_approval_required, True)
    rows[0].risk_flags.append(RiskFlag("gap","Synthetic blocking gap",Severity.CRITICAL))
    with patch("hedgeops.engine.assess_all",return_value=rows):
        check("critical risk blocks", evaluate_decision(request).status.value, "blocked")
    with patch("hedgeops.engine.assess_all",return_value=rows[1:]):
        check("missing required role remains blocked", evaluate_decision(request).status.value, "blocked")
    rejects("empty objective rejected", lambda: DecisionRequest(""))

if __name__ == "__main__":
    if sys.argv[1:] not in ([], ["--verify"]):
        raise SystemExit("Usage: python curriculum/lab.py [--verify]")
    run()
    report = {"schema_version": 1, "status": "PASS", "case_count": len(CASES),
              "cases": CASES, "scope": "Synthetic curriculum checks only"}
    if sys.argv[1:] == ["--verify"]:
        expected = json.loads((Path(__file__).parent / "expected.json").read_text())
        if report != expected:
            raise AssertionError("Observed answers differ from curriculum/expected.json")
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
