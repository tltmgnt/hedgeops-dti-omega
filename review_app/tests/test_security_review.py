import json
import tempfile
import unittest
from pathlib import Path

from hedgeops.security_review import REQUIRED, inspect_security_review


class SecurityReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "review.json"
        self.data = {"schema_version": 1, "status": "blocked",
                     "controls": [{"id": name, "description": "External review pending",
                                   "approved": False, "evidence": None}
                                  for name in sorted(REQUIRED)]}
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.data))

    def test_all_unapproved_is_blocked(self):
        self.assertTrue(inspect_security_review(self.path)["blocked"])

    def test_missing_control_rejected(self):
        self.data["controls"].pop()
        self.save()
        with self.assertRaises(ValueError):
            inspect_security_review(self.path)

    def test_approval_without_independent_review_rejected(self):
        self.data["controls"][0]["approved"] = True
        self.save()
        with self.assertRaises(ValueError):
            inspect_security_review(self.path)

    def test_evidence_cannot_be_self_attested(self):
        self.data["controls"][0]["evidence"] = "https://example.org/report"
        self.save()
        with self.assertRaises(ValueError):
            inspect_security_review(self.path)

    def test_duplicate_control_rejected(self):
        self.data["controls"][1]["id"] = self.data["controls"][0]["id"]
        self.save()
        with self.assertRaises(ValueError):
            inspect_security_review(self.path)

    def test_oversized_register_rejected(self):
        self.path.write_bytes(b" " * 16385)
        with self.assertRaisesRegex(ValueError, "size limit"):
            inspect_security_review(self.path)

    def test_invalid_utf8_rejected(self):
        self.path.write_bytes(b"\\xff")
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            inspect_security_review(self.path)

    def test_nonfinite_json_rejected(self):
        raw = json.dumps(self.data).replace('"schema_version": 1', '"schema_version": NaN')
        self.path.write_text(raw)
        with self.assertRaisesRegex(ValueError, "non-finite"):
            inspect_security_review(self.path)

    def test_duplicate_json_key_rejected(self):
        self.path.write_text(self.path.read_text().replace(
            '"status": "blocked"', '"status": "blocked", "status": "blocked"'))
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            inspect_security_review(self.path)

    def test_ready_status_rejected(self):
        self.data["status"] = "ready"
        self.save()
        with self.assertRaises(ValueError):
            inspect_security_review(self.path)


if __name__ == "__main__":
    unittest.main()
