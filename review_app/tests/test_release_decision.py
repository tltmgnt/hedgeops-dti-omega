import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hedgeops.release_decision import decide_release
from hedgeops.security_review import REQUIRED as SECURITY
from scripts.check_release_gates import REQUIRED as GATES


class ReleaseDecisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        docs = self.root / "docs"
        docs.mkdir()
        self.gates = docs / "release-gates.json"
        self.review = docs / "security-review-register.json"
        self.gates.write_text(json.dumps({
            "schema_version": 1, "release_type": "production", "status": "blocked",
            "requirements": [{"id": name, "approved": False, "evidence": None}
                             for name in sorted(GATES)]}))
        self.review.write_text(json.dumps({
            "schema_version": 1, "status": "blocked",
            "controls": [{"id": name, "description": "External review pending",
                          "approved": False, "evidence": None}
                         for name in sorted(SECURITY)]}))

    def test_no_go_on_committed_policy(self):
        result = decide_release(self.root)
        self.assertEqual(result["decision"], "NO_GO")
        self.assertFalse(result["deploy_authorized"])
        self.assertFalse(result["merge_authorized"])

    def test_unexpected_ready_result_rejected(self):
        with patch("hedgeops.release_decision.inspect_release_readiness",
                   return_value={"production_ready": True}):
            with self.assertRaisesRegex(ValueError, "cannot authorize"):
                decide_release(self.root)

    def test_invalid_release_register_fails(self):
        self.gates.write_text("{}")
        with self.assertRaises(ValueError):
            decide_release(self.root)

    def test_missing_security_register_fails(self):
        self.review.unlink()
        with self.assertRaises(FileNotFoundError):
            decide_release(self.root)


if __name__ == "__main__":
    unittest.main()
