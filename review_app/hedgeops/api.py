"""Review-only HTTP API. Never expose directly to the public internet."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import hmac
import json
import os
from .core import evaluate, from_dict, simulate
from .storage import Store

class Handler(BaseHTTPRequestHandler):
    store = None

    def authorized(self):
        token = os.getenv("HEDGEOPS_API_TOKEN", "")
        return not token or hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + token)

    def security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
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

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/dashboard"):
            data = Path(__file__).with_name("dashboard.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.security_headers()
            self.end_headers()
            self.wfile.write(data)
            return
        if not self.authorized():
            return self.reply(401, {"error": "unauthorized"})
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
        if not self.authorized():
            return self.reply(401, {"error": "unauthorized"})
        path = urlparse(self.path).path
        if path not in ("/decisions", "/simulate"):
            return self.reply(404, {"error": "not found"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 65536:
                return self.reply(413, {"error": "body must be 1..65536 bytes"})
            if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
                return self.reply(415, {"error": "Content-Type must be application/json"})
            payload = json.loads(self.rfile.read(size))
            scenario = from_dict(payload)
            if path == "/simulate":
                return self.reply(200, {"scenarios": simulate(scenario)})
            record = evaluate(scenario)
            self.store.save(record)
            return self.reply(201, record)
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as err:
            return self.reply(400, {"error": str(err)})

def main():
    host = os.getenv("HEDGEOPS_HOST", "127.0.0.1")
    port = int(os.getenv("HEDGEOPS_PORT", "8080"))
    if host not in ("127.0.0.1", "::1", "localhost") and not os.getenv("HEDGEOPS_API_TOKEN"):
        raise RuntimeError("Non-loopback binding requires an API token and an HTTPS reverse proxy")
    Handler.store = Store(os.getenv("HEDGEOPS_DB", "hedgeops.sqlite3"))
    print(f"Review-only API: http://{host}:{port}", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
