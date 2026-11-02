"""Real HTTP boundary tests using a loopback ephemeral port."""
import http.client
import json
import os
import socket
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from hedgeops.api import Handler, ReviewHTTPServer
from hedgeops.storage import Store


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        class LocalHandler(Handler):
            store = Store(self.temp.name + "/http.sqlite3")
            def log_message(self, *args):
                pass
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), LocalHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.env = patch.dict(os.environ, {"HEDGEOPS_API_TOKEN": "test-secret"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp.cleanup()

    def request(self, method, path, payload=None, token="test-secret", content_type="application/json"):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        headers = {}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        if payload is not None:
            headers["Content-Type"] = content_type
            payload = payload if isinstance(payload, str) else json.dumps(payload)
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        status = response.status
        headers = dict(response.getheaders())
        body = response.read()
        connection.close()
        return status, headers, json.loads(body) if headers.get("Content-Type", "").startswith("application/json") else body

    @staticmethod
    def scenario():
        return {"objective": "HTTP review", "required_minutes": 10,
                "capacity": {"horizon_minutes": 100, "committed_minutes": 10,
                             "fragmentation_index": .1, "autonomy_fraction": 1},
                "evidence_verified": False, "constraints_verified": False}

    def test_dashboard_requires_authentication(self):
        for path in ("/", "/dashboard"):
            with self.subTest(path=path):
                status, _, _ = self.request("GET", path, token=None)
                self.assertEqual(status, 401)
                status, headers, html = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertIn(b"html", html.lower())
                self.assertEqual(headers["X-Frame-Options"], "DENY")

    def test_unauthorized_rejected(self):
        for token in (None, "incorrect"):
            with self.subTest(token=token):
                status, _, _ = self.request("GET", "/decisions", token=token)
                self.assertEqual(status, 401)

    def test_post_is_review_only_and_persisted(self):
        status, headers, record = self.request("POST", "/decisions", self.scenario())
        self.assertEqual(status, 201)
        self.assertEqual(record["status"], "blocked")
        self.assertTrue(record["human_approval_required"])
        self.assertFalse(record["execution_authorized"])
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        status, _, stored = self.request("GET", "/decisions/" + record["record_id"])
        self.assertEqual(status, 200)
        self.assertEqual(stored["record_id"], record["record_id"])

    def test_missing_fields_and_bad_json(self):
        for payload in ('{broken', '{"objective":"missing capacity"}'):
            with self.subTest(payload=payload):
                status, _, _ = self.request("POST", "/decisions", payload)
                self.assertEqual(status, 400)

    def test_empty_body_rejected(self):
        status, _, _ = self.request("POST", "/decisions", "")
        self.assertEqual(status, 413)

    def test_oversized_body_rejected(self):
        status, _, _ = self.request("POST", "/decisions", "x" * 65537)
        self.assertEqual(status, 413)

    def test_unsupported_method_rejected(self):
        status, _, _ = self.request("PUT", "/decisions", self.scenario())
        self.assertEqual(status, 405)

    def test_duplicate_content_length_rejected(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.putrequest("POST", "/decisions")
        connection.putheader("Authorization", "Bearer test-secret")
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", "2")
        connection.putheader("Content-Length", "2")
        connection.endheaders()
        connection.send(b"{}")
        response = connection.getresponse()
        self.assertEqual(response.status, 400)
        response.read()
        connection.close()

    def test_rejects_untrusted_host_even_with_token(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.request("GET", "/decisions", headers={
            "Authorization": "Bearer test-secret", "Host": "attacker.example"})
        response = connection.getresponse()
        self.assertEqual(response.status, 400)
        response.read()
        connection.close()

    def test_loopback_host_remains_valid(self):
        status, _, _ = self.request("GET", "/health")
        self.assertEqual(status, 200)

    def test_cross_origin_post_rejected(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.request("POST", "/decisions", body=json.dumps(self.scenario()),
                           headers={"Authorization": "Bearer test-secret",
                                    "Content-Type": "application/json",
                                    "Origin": "https://attacker.example"})
        response = connection.getresponse()
        self.assertEqual(response.status, 403)
        response.read()
        connection.close()

    def test_same_origin_post_allowed(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.request("POST", "/decisions", body=json.dumps(self.scenario()),
                           headers={"Authorization": "Bearer test-secret",
                                    "Content-Type": "application/json",
                                    "Origin": f"http://127.0.0.1:{self.server.server_port}"})
        response = connection.getresponse()
        self.assertEqual(response.status, 201)
        response.read()
        connection.close()

    def test_unsupported_methods_require_authentication(self):
        for method in ("PUT", "PATCH", "DELETE", "OPTIONS"):
            with self.subTest(method=method):
                status, headers, body = self.request(method, "/decisions", token=None)
                self.assertEqual(status, 401)
                self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
                self.assertEqual(body["error"], "unauthorized")
                status, _, body = self.request(method, "/decisions")
                self.assertEqual(status, 405)
                self.assertEqual(body["error"], "method not allowed")

    def test_duplicate_json_keys_rejected(self):
        status, _, body = self.request("POST", "/decisions", '{"objective":"one","objective":"two"}')
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "duplicate JSON key")

    def test_excessive_request_target_rejected(self):
        status, _, body = self.request("GET", "/decisions?" + "x" * 2100)
        self.assertEqual(status, 414)
        self.assertEqual(body["error"], "request target too long")

    def test_excessive_content_length_digits_rejected(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.putrequest("POST", "/decisions")
        connection.putheader("Authorization", "Bearer test-secret")
        connection.putheader("Content-Length", "9" * 100)
        connection.endheaders()
        response = connection.getresponse()
        self.assertEqual(response.status, 400)
        response.read()
        connection.close()

    def test_server_sets_connection_read_timeout(self):
        server = ReviewHTTPServer(("127.0.0.1", 0), Handler)
        try:
            client = socket.create_connection(server.server_address, timeout=2)
            try:
                accepted, _ = server.get_request()
                try:
                    self.assertEqual(accepted.gettimeout(), server.request_timeout_seconds)
                    self.assertGreater(server.request_timeout_seconds, 0)
                finally:
                    accepted.close()
            finally:
                client.close()
        finally:
            server.server_close()

    def test_content_type_required(self):
        status, _, _ = self.request("POST", "/decisions", self.scenario(), content_type="text/plain")
        self.assertEqual(status, 415)

    def test_no_execution_route(self):
        for route in ("/execute", "/trade", "/orders", "/approve"):
            with self.subTest(route=route):
                status, _, _ = self.request("POST", route, self.scenario())
                self.assertEqual(status, 404)

    def test_simulation_and_audit(self):
        status, _, result = self.request("POST", "/simulate", self.scenario())
        self.assertEqual(status, 200)
        self.assertEqual(len(result["scenarios"]), 5)
        status, _, result = self.request("GET", "/audit/verify")
        self.assertEqual(status, 200)
        self.assertTrue(result["integrity_ok"])


if __name__ == "__main__":
    unittest.main()
