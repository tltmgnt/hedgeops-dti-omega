import json
import tempfile
import unittest
from pathlib import Path
from scripts.check_release_policy_docs import inspect_policy_docs
from scripts.check_release_gates import REQUIRED


class ReleasePolicyDocumentationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "docs").mkdir()
        self.register = {"schema_version": 1, "release_type": "production",
                         "status": "blocked",
                         "requirements": [{"id": key, "approved": False, "evidence": None}
                                          for key in sorted(REQUIRED)]}
        self.save()
        self.documentation = self.root / "docs" / "RELEASE_GATES.md"
        self.documentation.write_text(
            "Production release status: BLOCKED\n## Authoritative gate inventory\n" +
            "\n".join("`" + key + "`" for key in sorted(REQUIRED)),
            encoding="utf-8")

    def save(self):
        (self.root / "docs" / "release-gates.json").write_text(
            json.dumps(self.register), encoding="utf-8")

    def test_matching_inventory(self):
        self.assertEqual(inspect_policy_docs(self.root)["documented_gates"], len(REQUIRED))

    def test_missing_documented_gate(self):
        content = self.documentation.read_text()
        self.documentation.write_text(content.replace("`" + sorted(REQUIRED)[0] + "`", "omitted"))
        with self.assertRaisesRegex(ValueError, "missing or duplicated"):
            inspect_policy_docs(self.root)

    def test_duplicate_documented_gate(self):
        self.documentation.write_text(self.documentation.read_text() +
                                      "\n`" + sorted(REQUIRED)[0] + "`")
        with self.assertRaisesRegex(ValueError, "missing or duplicated"):
            inspect_policy_docs(self.root)

    def test_missing_blocked_declaration(self):
        self.documentation.write_text(self.documentation.read_text().replace(
            "Production release status: BLOCKED", "Production release status: UNKNOWN"))
        with self.assertRaisesRegex(ValueError, "blocked release status"):
            inspect_policy_docs(self.root)


if __name__ == "__main__":
    unittest.main()
