"""Offline security preflight tests."""
import unittest
from hedgeops.preflight import inspect_configuration


class PreflightTests(unittest.TestCase):
    def test_local_defaults_are_warnings_not_errors(self):
        result = inspect_configuration({})
        self.assertTrue(result["ok"])
        self.assertEqual(result["binding"], "loopback")
        self.assertIn("missing_api_token", [f["code"] for f in result["findings"]])

    def test_non_loopback_requires_token_and_origin(self):
        result = inspect_configuration({"HEDGEOPS_HOST": "0.0.0.0"})
        self.assertFalse(result["ok"])
        self.assertIn("missing_public_origin", [f["code"] for f in result["findings"]])
        self.assertIn("missing_api_token", [f["code"] for f in result["findings"]])

    def test_non_loopback_http_origin_rejected(self):
        result = inspect_configuration({"HEDGEOPS_HOST": "0.0.0.0",
                                        "HEDGEOPS_API_TOKEN": "secret",
                                        "HEDGEOPS_PUBLIC_ORIGIN": "http://example.com"})
        self.assertFalse(result["ok"])
        self.assertIn("public_origin_must_use_https", [f["code"] for f in result["findings"]])

    def test_non_loopback_valid_config_still_warns_proxy(self):
        result = inspect_configuration({"HEDGEOPS_HOST": "0.0.0.0",
                                        "HEDGEOPS_API_TOKEN": "secret",
                                        "HEDGEOPS_AUDIT_KEY": "audit-secret",
                                        "HEDGEOPS_PUBLIC_ORIGIN": "https://review.example"})
        self.assertTrue(result["ok"])
        self.assertEqual([f["code"] for f in result["findings"]],
                         ["non_loopback_binding_requires_reviewed_proxy"])

    def test_invalid_origin_with_credentials_rejected(self):
        result = inspect_configuration({"HEDGEOPS_PUBLIC_ORIGIN": "https://user:pass@example.com"})
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
