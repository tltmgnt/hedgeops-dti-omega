import json
import tempfile
import unittest
from pathlib import Path
from scripts.check_release_gates import inspect_gates, REQUIRED


class ReleaseGateTests(unittest.TestCase):
    def check(self, data):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "gates.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return inspect_gates(path)

    def baseline(self):
        return {"schema_version": 1, "release_type": "production",
                "status": "blocked",
                "requirements": [{"id": name, "approved": False, "evidence": None}
                                 for name in sorted(REQUIRED)]}

    def test_blocked_without_approvals(self):
        result = self.check(self.baseline())
        self.assertTrue(result["blocked"])
        self.assertEqual(len(result["outstanding"]), len(REQUIRED))

    def test_rejects_missing_requirement(self):
        data = self.baseline()
        data["requirements"].pop()
        with self.assertRaises(ValueError):
            self.check(data)

    def test_rejects_unsubstantiated_approval(self):
        data = self.baseline()
        data["requirements"][0]["approved"] = True
        with self.assertRaises(ValueError):
            self.check(data)

    def test_rejects_local_or_insecure_evidence(self):
        for value in ("http://evidence.example.org/record/1",
                      "https://localhost/record/1",
                      "https://user:pass@evidence.example.org/record/1",
                      "https://evidence.example.org/",
                      "https://evidence.example.org/record/1#fragment"):
            with self.subTest(value=value):
                data = self.baseline()
                data["requirements"][0]["approved"] = True
                data["requirements"][0]["evidence"] = value
                with self.assertRaises(ValueError):
                    self.check(data)

    def test_rejects_duplicate_evidence(self):
        data = self.baseline()
        for item in data["requirements"][:2]:
            item["approved"] = True
            item["evidence"] = "https://evidence.example.org/records/1"
        with self.assertRaises(ValueError):
            self.check(data)

    def test_rejects_evidence_on_unapproved_gate(self):
        data = self.baseline()
        data["requirements"][0]["evidence"] = "https://evidence.example.org/records/1"
        with self.assertRaises(ValueError):
            self.check(data)

    def test_rejects_missing_or_invalid_review_provenance(self):
        for reviewer, timestamp in ((None, None), ("a", "2026-10-31T12:00:00Z"),
                                    ("reviewer-1", "2026-10-31T12:00:00"),
                                    ("reviewer-1", "not-a-time")):
            with self.subTest(reviewer=reviewer, timestamp=timestamp):
                data = self.baseline()
                item = data["requirements"][0]
                item.update(approved=True, evidence="https://evidence.example.org/records/1",
                            reviewer=reviewer, reviewed_at=timestamp)
                with self.assertRaises(ValueError):
                    self.check(data)

    def test_rejects_provenance_on_unapproved_gate(self):
        data = self.baseline()
        data["requirements"][0]["reviewer"] = "reviewer-1"
        with self.assertRaises(ValueError):
            self.check(data)

    def test_approval_requires_consistent_status(self):
        data = self.baseline()
        for i, item in enumerate(data["requirements"]):
            item["approved"] = True
            item["evidence"] = f"https://evidence.example.org/records/{i}"
            item["reviewer"] = f"reviewer-{i}"
            item["reviewed_at"] = "2026-10-31T12:00:00Z"
        with self.assertRaises(ValueError):
            self.check(data)
        data["status"] = "ready_for_manual_review"
        self.assertTrue(self.check(data)["ready_for_manual_review"])


if __name__ == "__main__":
    unittest.main()
