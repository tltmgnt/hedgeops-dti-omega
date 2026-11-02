import copy
import unittest
from integration_contracts.normalized import ROLES, normalize
from integration_contracts.test_contracts import LEGACY, REVIEW, run_engine

class NormalizedContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.legacy = run_engine("legacy_compat", LEGACY)
        cls.review = run_engine("review_app", REVIEW)

    def test_both_engines_normalize(self):
        for record in (self.legacy, self.review):
            with self.subTest(engine=record.get("record_id")):
                normalized = normalize(record)
                self.assertEqual(normalized.agent_roles, ROLES)
                self.assertEqual(normalized.status, "blocked")
                self.assertFalse(normalized.execution_authorized)
                self.assertTrue(normalized.human_approval_required)

    def test_executable_status_rejected(self):
        for status in ("approved_by_human", "proposed", "executed"):
            with self.subTest(status=status):
                record = copy.deepcopy(self.review)
                record["status"] = status
                with self.assertRaises(ValueError):
                    normalize(record)

    def test_authorization_rejected(self):
        record = copy.deepcopy(self.review)
        record["execution_authorized"] = True
        with self.assertRaises(ValueError):
            normalize(record)

    def test_missing_role_rejected(self):
        record = copy.deepcopy(self.review)
        record["assessments"].pop()
        with self.assertRaises(ValueError):
            normalize(record)

    def test_blocking_risk_cannot_be_reviewable(self):
        record = copy.deepcopy(self.review)
        record["status"] = "needs_review"
        with self.assertRaises(ValueError):
            normalize(record)
