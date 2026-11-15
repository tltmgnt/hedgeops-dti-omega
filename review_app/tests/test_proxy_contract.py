import unittest
from hedgeops.preflight import inspect_configuration
from hedgeops.proxy_contract import inspect_proxy_contract


class ProxyContractTests(unittest.TestCase):
    def test_empty_production_contract_fails_closed(self):
        result = inspect_configuration({"HEDGEOPS_PRODUCTION_PREFLIGHT": "1"})
        self.assertFalse(result["ok"])
        codes = {f["code"] for f in result["findings"]}
        self.assertIn("tls_proxy_not_verified", codes)
        self.assertIn("identity_must_fail_closed", codes)

    def test_each_assertion_required(self):
        env = {
            "HEDGEOPS_HOST": "127.0.0.1",
            "HEDGEOPS_PUBLIC_ORIGIN": "https://review.example.org",
            "HEDGEOPS_REQUIRE_IDENTITY": "1",
            "HEDGEOPS_PROXY_TLS_VERIFIED": "1",
            "HEDGEOPS_PROXY_RATE_LIMIT_VERIFIED": "1",
            "HEDGEOPS_PROXY_DEADLINE_VERIFIED": "1",
            "HEDGEOPS_PROXY_LOGGING_VERIFIED": "1",
        }
        self.assertTrue(inspect_proxy_contract(env)["ok"])
        for key in list(env):
            with self.subTest(key=key):
                mutated = dict(env)
                mutated.pop(key)
                if key == "HEDGEOPS_HOST":
                    mutated[key] = "0.0.0.0"
                self.assertFalse(inspect_proxy_contract(mutated)["ok"])

    def test_untrusted_proxy_header_is_not_evidence(self):
        result = inspect_proxy_contract({"X-Forwarded-Proto": "https",
                                         "X-Forwarded-For": "127.0.0.1"})
        self.assertFalse(result["ok"])

    def test_local_preflight_is_unchanged(self):
        self.assertTrue(inspect_configuration({})["ok"])

    def test_https_origin_rejects_credentials_and_port(self):
        for origin in ("https://user@review.example.org",
                       "https://review.example.org:443",
                       "http://review.example.org"):
            with self.subTest(origin=origin):
                self.assertFalse(inspect_proxy_contract(
                    {"HEDGEOPS_PUBLIC_ORIGIN": origin})["ok"])


if __name__ == "__main__":
    unittest.main()
