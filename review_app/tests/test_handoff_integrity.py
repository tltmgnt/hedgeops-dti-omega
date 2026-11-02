import json
import tempfile
import unittest
from pathlib import Path

from hedgeops.handoff_integrity import check_handoff, REQUIRED_PHRASES
from hedgeops.security_review import REQUIRED as SECURITY
from scripts.check_release_gates import REQUIRED as GATES


class HandoffIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "release-gates.json").write_text(json.dumps({
            "schema_version": 1, "release_type": "production", "status": "blocked",
            "requirements": [{"id": name, "approved": False, "evidence": None}
                             for name in sorted(GATES)]}))
        (docs / "security-review-register.json").write_text(json.dumps({
            "schema_version": 1, "status": "blocked",
            "controls": [{"id": name, "description": "Pending external review",
                          "approved": False, "evidence": None}
                         for name in sorted(SECURITY)]}))
        self.handoff = docs / "FINAL_RELEASE_DECISION.md"
        self.handoff.write_text("\n".join(REQUIRED_PHRASES))

    def test_valid_no_go_handoff(self):
        self.assertTrue(check_handoff(self.root)["handoff_consistent"])

    def test_missing_draft_warning_rejected(self):
        self.handoff.write_text(self.handoff.read_text().replace("remain draft", ""))
        with self.assertRaisesRegex(ValueError, "remain draft"):
            check_handoff(self.root)

    def test_missing_independent_review_rejected(self):
        self.handoff.write_text(self.handoff.read_text().replace("independent security review", ""))
        with self.assertRaisesRegex(ValueError, "independent security review"):
            check_handoff(self.root)

    def test_symlink_handoff_rejected(self):
        target = self.root / "external-handoff.md"
        target.write_text(self.handoff.read_text())
        self.handoff.unlink()
        self.handoff.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "non-symlink"):
            check_handoff(self.root)

    def test_directory_in_place_of_handoff_rejected(self):
        self.handoff.unlink()
        self.handoff.mkdir()
        with self.assertRaisesRegex(ValueError, "regular non-symlink"):
            check_handoff(self.root)

    def test_missing_release_evidence_rejected(self):
        (self.root / "docs" / "release-gates.json").unlink()
        with self.assertRaisesRegex(ValueError, "release-gates.json"):
            check_handoff(self.root)

    def test_ready_register_rejected(self):
        path = self.root / "docs" / "release-gates.json"
        data = json.loads(path.read_text())
        data["status"] = "ready"
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            check_handoff(self.root)


if __name__ == "__main__":
    unittest.main()
