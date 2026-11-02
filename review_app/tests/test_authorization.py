import os
import unittest
from unittest.mock import patch
from hedgeops.authorization import ROLES, permitted, identity_enforced
from hedgeops.api import Handler


class AuthorizationPolicyTests(unittest.TestCase):
    def test_viewers_cannot_write_or_read_audit(self):
        for path in ("/decisions", "/simulate"):
            self.assertFalse(permitted("viewer", "POST", path))
        self.assertFalse(permitted("viewer", "GET", "/audit/verify"))
        self.assertTrue(permitted("viewer", "GET", "/decisions"))

    def test_analyst_can_review_but_not_audit(self):
        self.assertTrue(permitted("analyst", "POST", "/simulate"))
        self.assertTrue(permitted("analyst", "POST", "/decisions"))
        self.assertFalse(permitted("analyst", "GET", "/audit/verify"))

    def test_auditor_is_read_only(self):
        self.assertTrue(permitted("auditor", "GET", "/audit/verify"))
        self.assertFalse(permitted("auditor", "POST", "/decisions"))

    def test_administrator_scope(self):
        self.assertTrue(permitted("administrator", "GET", "/audit/verify"))
        self.assertTrue(permitted("administrator", "POST", "/decisions"))
        self.assertFalse(permitted("administrator", "POST", "/execute"))

    def test_unknown_roles_and_methods_fail_closed(self):
        for role in (None, "", "owner", "Viewer", "administrator "):
            self.assertFalse(permitted(role, "GET", "/decisions"))
        for role in ROLES:
            self.assertFalse(permitted(role, "DELETE", "/decisions"))
            self.assertFalse(permitted(role, "POST", "/approve"))

    def test_strict_identity_mode_rejects_even_legacy_token(self):
        handler = object.__new__(Handler)
        handler.headers = {"Authorization": "Bearer local-token",
                           "X-Role": "administrator"}
        with patch.dict(os.environ, {"HEDGEOPS_REQUIRE_IDENTITY": "1",
                                     "HEDGEOPS_API_TOKEN": "local-token"}):
            self.assertTrue(identity_enforced())
            self.assertFalse(handler.authorized())

    def test_local_mode_retains_existing_token_contract(self):
        handler = object.__new__(Handler)
        handler.headers = {"Authorization": "Bearer local-token"}
        with patch.dict(os.environ, {"HEDGEOPS_REQUIRE_IDENTITY": "0",
                                     "HEDGEOPS_API_TOKEN": "local-token"}):
            self.assertTrue(handler.authorized())


if __name__ == "__main__":
    unittest.main()
