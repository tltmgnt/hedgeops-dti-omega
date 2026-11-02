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

    def test_separation_of_duties_rejects_same_reviewer(self):
        data = self.baseline()
        by_id = {item["id"]: item for item in data["requirements"]}
        for index, gate in enumerate(("independent_security_review", "maintainer_release_approval")):
            by_id[gate].update(approved=True,
                               evidence=f"https://evidence.example.org/records/{index}",
                               reviewer="SecurityLead" if index == 0 else "securitylead",
                               reviewed_at="2026-10-31T12:00:00Z" if index == 0 else "2026-10-31T13:00:00Z")
        with self.assertRaisesRegex(ValueError, "reviewer must differ"):
            self.check(data)

    def test_separation_of_duties_accepts_distinct_reviewers(self):
        data = self.baseline()
        by_id = {item["id"]: item for item in data["requirements"]}
        for index, (gate, reviewer) in enumerate((
                ("independent_security_review", "security-reviewer"),
                ("maintainer_release_approval", "release-maintainer"))):
            by_id[gate].update(approved=True,
                               evidence=f"https://evidence.example.org/records/{index}",
                               reviewer=reviewer,
                               reviewed_at="2026-10-31T12:00:00Z" if index == 0 else "2026-10-31T13:00:00Z")
        with self.assertRaisesRegex(ValueError, "every other gate approved"):
            self.check(data)

    def test_rejects_future_review_timestamp(self):
        data = self.baseline()
        data["requirements"][0].update(
            approved=True, evidence="https://evidence.example.org/records/1",
            reviewer="reviewer-1", reviewed_at="2099-01-01T00:00:00Z")
        with self.assertRaisesRegex(ValueError, "future"):
            self.check(data)

    def test_release_approval_requires_prior_security_review(self):
        data = self.baseline()
        gate = next(item for item in data["requirements"]
                    if item["id"] == "maintainer_release_approval")
        gate.update(approved=True, evidence="https://evidence.example.org/records/release",
                    reviewer="release-maintainer", reviewed_at="2026-10-31T13:00:00Z")
        with self.assertRaisesRegex(ValueError, "prior independent security"):
            self.check(data)

    def test_release_approval_must_follow_security_review(self):
        data = self.baseline()
        by_id = {item["id"]: item for item in data["requirements"]}
        by_id["independent_security_review"].update(
            approved=True, evidence="https://evidence.example.org/records/security",
            reviewer="security-reviewer", reviewed_at="2026-10-31T13:00:00Z")
        by_id["maintainer_release_approval"].update(
            approved=True, evidence="https://evidence.example.org/records/release",
            reviewer="release-maintainer", reviewed_at="2026-10-31T12:00:00Z")
        with self.assertRaisesRegex(ValueError, "must follow"):
            self.check(data)
        by_id["maintainer_release_approval"]["reviewed_at"] = "2026-10-31T14:00:00Z"
        with self.assertRaisesRegex(ValueError, "every other gate approved"):
            self.check(data)

    def test_final_approval_requires_all_prerequisites(self):
        data = self.baseline()
        by_id = {item["id"]: item for item in data["requirements"]}
        for index, gate in enumerate(("independent_security_review", "maintainer_release_approval")):
            by_id[gate].update(approved=True,
                               evidence=f"https://evidence.example.org/records/{index}",
                               reviewer=f"reviewer-{index}",
                               reviewed_at="2026-10-31T12:00:00Z" if index == 0 else "2026-10-31T13:00:00Z")
        with self.assertRaisesRegex(ValueError, "every other gate approved"):
            self.check(data)

    def test_final_approval_must_follow_every_gate(self):
        data = self.baseline()
        for index, item in enumerate(data["requirements"]):
            item.update(approved=True,
                        evidence=f"https://evidence.example.org/records/{index}",
                        reviewer=f"reviewer-{index}",
                        reviewed_at="2026-10-31T14:00:00Z" if item["id"] == "domain_model_validation" else
                        ("2026-10-31T13:00:00Z" if item["id"] == "maintainer_release_approval" else "2026-10-31T12:00:00Z"))
        data["status"] = "ready_for_manual_review"
        with self.assertRaisesRegex(ValueError, "follow all prerequisite"):
            self.check(data)

    def test_approval_requires_consistent_status(self):
        data = self.baseline()
        for i, item in enumerate(data["requirements"]):
            item["approved"] = True
            item["evidence"] = f"https://evidence.example.org/records/{i}"
            item["reviewer"] = f"reviewer-{i}"
            item["reviewed_at"] = ("2026-10-31T13:00:00Z" if item["id"] == "maintainer_release_approval" else "2026-10-31T12:00:00Z")
        with self.assertRaises(ValueError):
            self.check(data)
        data["status"] = "ready_for_manual_review"
        self.assertTrue(self.check(data)["ready_for_manual_review"])


if __name__ == "__main__":
    unittest.main()
