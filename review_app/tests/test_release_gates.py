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

    def test_approval_requires_consistent_status(self):
        data = self.baseline()
        for item in data["requirements"]:
            item["approved"] = True
            item["evidence"] = "external-change-record"
        with self.assertRaises(ValueError):
            self.check(data)
        data["status"] = "ready_for_manual_review"
        self.assertTrue(self.check(data)["ready_for_manual_review"])


if __name__ == "__main__":
    unittest.main()
