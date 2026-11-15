"""Cross-system behavioral contracts; import each engine in an isolated process."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

def run_engine(directory, code):
    proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT / directory,
                          capture_output=True, text=True, timeout=20,
                          env={**os.environ, "PYTHONPATH": str(ROOT / directory)})
    if proc.returncode:
        raise AssertionError(f"{directory} failed: {proc.stderr}")
    return json.loads(proc.stdout)

LEGACY = """
import json
from hedgeops.engine import evaluate_decision
from hedgeops.models import DecisionRequest
r=evaluate_decision(DecisionRequest(objective='Cross-system review'))
print(json.dumps(r.to_dict()))
"""

REVIEW = """
import json
from hedgeops.core import Capacity, Scenario, evaluate
r=evaluate(Scenario(objective='Cross-system review', required_minutes=20,
    capacity=Capacity(100,20,.1,1), evidence_verified=False, constraints_verified=False))
print(json.dumps(r))
"""

class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.legacy = run_engine("legacy_compat", LEGACY)
        cls.review = run_engine("review_app", REVIEW)

    def test_six_roles_match(self):
        roles = lambda r: {a["agent"] for a in r["assessments"]}
        self.assertEqual(roles(self.legacy), roles(self.review))
        self.assertEqual(len(roles(self.review)), 6)

    def test_unverified_scenarios_blocked(self):
        self.assertEqual(self.legacy["status"], "blocked")
        self.assertEqual(self.review["status"], "blocked")

    def test_human_review_required(self):
        for result in (self.legacy, self.review):
            self.assertTrue(result["human_approval_required"])

    def test_no_execution_authority(self):
        self.assertFalse(self.review["execution_authorized"])
        self.assertTrue(self.legacy["has_blocking_risk"])

    def test_assessments_contain_explanations(self):
        for result in (self.legacy, self.review):
            self.assertTrue(all(a["summary"].strip() for a in result["assessments"]))

if __name__ == "__main__":
    unittest.main()
