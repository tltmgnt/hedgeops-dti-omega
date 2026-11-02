"""Review-only HTTP API. Never expose directly to the public internet."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import hmac
import json
import os
import threading
from .core import evaluate, from_dict, simulate
from .storage import Store
from .contract import normalize

def reject_duplicate_json_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


class Handler(BaseHTTPRequestHandler):
    store = None

    def valid_host(self):
        """Reject DNS-rebinding Host headers when listening on loopback."""
        bound = self.server.server_address[0]
        if bound not in ("127.0.0.1", "::1", "localhost"):
            return True  # Reverse proxy must validate public Host values.
        authority = self.headers.get("Host", "")
        allowed = {"localhost", "127.0.0.1", "[::1]"}
        host = authority.rsplit(":", 1)[0] if ":" in authority else authority
        if authority.startswith("[::1]"):
            host = "[::1]"
        return host.lower() in allowed

    def valid_origin(self):
        """Reject browser POSTs originating outside the configured origin."""
        origins = self.headers.get_all("Origin", [])
        if not origins:
            return True  # Non-browser clients use bearer authentication.
        if len(origins) != 1:
            return False
        origin = origins[0]
        parsed = urlparse(origin)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return False
        if parsed.username or parsed.password or parsed.path or parsed.params or parsed.query or parsed.fragment:
            return False
        expected = os.getenv("HEDGEOPS_PUBLIC_ORIGIN", "").rstrip("/")
        if not expected:
            expected = "http://" + self.headers.get("Host", "")
        return origin == expected

    def authorized(self):
        token = os.getenv("HEDGEOPS_API_TOKEN", "")
        return not token or hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + token)

    def security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")

    def reply(self, status, payload):
        data = json.dumps(payload, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.security_headers()
        self.end_headers()
        self.wfile.write(data)

    def valid_target(self):
        return len(self.path) <= 2048

    def reject_unsupported_method(self):
        if not self.valid_target():
            return self.reply(414, {"error": "request target too long"})
        if not self.valid_host():
            return self.reply(400, {"error": "invalid host"})
        if not self.authorized():
            return self.reply(401, {"error": "unauthorized"})
        return self.reply(405, {"error": "method not allowed"})

    def do_PUT(self):
        return self.reject_unsupported_method()

    def do_PATCH(self):
        return self.reject_unsupported_method()

    def do_DELETE(self):
        return self.reject_unsupported_method()

    def do_OPTIONS(self):
        return self.reject_unsupported_method()

    def do_GET(self):
        if not self.valid_target():
            return self.reply(414, {"error": "request target too long"})
        parsed = urlparse(self.path)
        if not self.valid_host():
            return self.reply(400, {"error": "invalid host"})
        if not self.authorized():
            return self.reply(401, {"error": "unauthorized"})
        if parsed.path in ("/", "/dashboard"):
            data = Path(__file__).with_name("dashboard.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.security_headers()
            self.end_headers()
            self.wfile.write(data)
            return
        if parsed.path == "/health":
            return self.reply(200, {"status": "ok", "execution_enabled": False})
        if parsed.path == "/audit/verify":
            return self.reply(200, self.store.verify())
        if parsed.path == "/decisions":
            try:
                args = parse_qs(parsed.query, keep_blank_values=True)
                if set(args) - {"limit"} or len(args.get("limit", [])) > 1:
                    raise ValueError("invalid query")
                limit = int(args.get("limit", ["50"])[0])
                return self.reply(200, {"decisions": self.store.list(limit)})
            except ValueError as err:
                return self.reply(400, {"error": str(err)})
        if parsed.path.startswith("/decisions/"):
            record = self.store.get(parsed.path.removeprefix("/decisions/"))
            return self.reply(200, record) if record else self.reply(404, {"error": "not found"})
        return self.reply(404, {"error": "not found"})

    def do_POST(self):
        if not self.valid_target():
            return self.reply(414, {"error": "request target too long"})
        if not self.valid_host():
            return self.reply(400, {"error": "invalid host"})
        if not self.valid_origin():
            return self.reply(403, {"error": "cross-origin POST forbidden"})
        if not self.authorized():
            return self.reply(401, {"error": "unauthorized"})
        path = urlparse(self.path).path
        if path not in ("/decisions", "/simulate"):
            return self.reply(404, {"error": "not found"})
        try:
            if self.headers.get("Transfer-Encoding"):
                return self.reply(400, {"error": "transfer encoding unsupported"})
            lengths = self.headers.get_all("Content-Length", [])
            if len(lengths) != 1 or len(lengths[0]) > 5 or not lengths[0].isascii() or not lengths[0].isdigit():
                return self.reply(400, {"error": "one valid Content-Length required"})
            size = int(lengths[0])
            if size < 1 or size > 65536:
                return self.reply(413, {"error": "body must be 1..65536 bytes"})
            if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
                return self.reply(415, {"error": "Content-Type must be application/json"})
            payload = json.loads(self.rfile.read(size), object_pairs_hook=reject_duplicate_json_keys)
            scenario = from_dict(payload)
            if path == "/simulate":
                return self.reply(200, {"scenarios": simulate(scenario)})
            record = evaluate(scenario)
            try:
                normalize(record)
            except ValueError:
                return self.reply(500, {"error": "decision failed safety contract validation"})
            self.store.save(record)
            return self.reply(201, record)
        except (ValueError, TypeError, KeyError, UnicodeDecodeError, json.JSONDecodeError) as err:
            return self.reply(400, {"error": str(err)})

class ReviewHTTPServer(ThreadingHTTPServer):
    """Bound idle/read time per accepted connection; proxy limits still required."""
    daemon_threads = True
    request_timeout_seconds = 10
    max_workers = 32

    def __init__(self, *args, **kwargs):
        self._worker_slots = threading.BoundedSemaphore(self.max_workers)
        super().__init__(*args, **kwargs)

    def process_request(self, request, client_address):
        if not self._worker_slots.acquire(blocking=False):
            try:
                request.sendall(
                    b"HTTP/1.1 503 Service Unavailable\r\n"
                    b"Content-Length: 0\r\n"
                    b"Connection: close\r\n"
                    b"Cache-Control: no-store\r\n"
                    b"X-Content-Type-Options: nosniff\r\n\r\n"
                )
            except OSError:
                pass
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._worker_slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._worker_slots.release()

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(self.request_timeout_seconds)
        return connection, address


def main():
    host = os.getenv("HEDGEOPS_HOST", "127.0.0.1")
    port = int(os.getenv("HEDGEOPS_PORT", "8080"))
    if host not in ("127.0.0.1", "::1", "localhost") and not os.getenv("HEDGEOPS_API_TOKEN"):
        raise RuntimeError("Non-loopback binding requires an API token and an HTTPS reverse proxy")
    Handler.store = Store(os.getenv("HEDGEOPS_DB", "hedgeops.sqlite3"))
    print(f"Review-only API: http://{host}:{port}", flush=True)
    ReviewHTTPServer((host, port), Handler).serve_forever()
