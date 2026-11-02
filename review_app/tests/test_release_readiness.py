import json
import tempfile
import unittest
from pathlib import Path

from hedgeops.release_readiness import inspect_release_readiness
from hedgeops.security_review import REQUIRED as SECURITY
from scripts.check_release_gates import REQUIRED as GATES


class ReleaseReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        docs = self.root / "docs"
        docs.mkdir()
        self.gates = docs / "release-gates.json"
        self.review = docs / "security-review-register.json"
        self.gate_data = {"schema_version": 1, "release_type": "production",
                          "status": "blocked", "requirements": [
                              {"id": name, "approved": False, "evidence": None}
                              for name in sorted(GATES)]}
        self.review_data = {"schema_version": 1, "status": "blocked",
                            "controls": [{"id": name, "description": "Pending external review",
                                          "approved": False, "evidence": None}
                                         for name in sorted(SECURITY)]}
        self.save()

    def save(self):
        self.gates.write_text(json.dumps(self.gate_data))
        self.review.write_text(json.dumps(self.review_data))

    def test_both_registers_block_production(self):
        result = inspect_release_readiness(self.root)
        self.assertFalse(result["production_ready"])
        self.assertTrue(result["release_gates_blocked"])
        self.assertTrue(result["independent_review_blocked"])

    def test_missing_security_control_fails(self):
        self.review_data["controls"].pop()
        self.save()
        with self.assertRaises(ValueError):
            inspect_release_readiness(self.root)

    def test_self_approved_security_control_fails(self):
        self.review_data["controls"][0]["approved"] = True
        self.save()
        with self.assertRaises(ValueError):
            inspect_release_readiness(self.root)

    def test_missing_release_gate_fails(self):
        self.gate_data["requirements"].pop()
        self.save()
        with self.assertRaises(ValueError):
            inspect_release_readiness(self.root)

    def test_unexpected_ready_status_fails(self):
        self.gate_data["status"] = "ready"
        self.save()
        with self.assertRaises(ValueError):
            inspect_release_readiness(self.root)


if __name__ == "__main__":
    unittest.main()
