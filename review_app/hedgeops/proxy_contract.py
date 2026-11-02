"""Offline production proxy contract checks; configuration assertions are not attestations."""
from urllib.parse import urlparse

def inspect_proxy_contract(env):
    findings = []
    def require(name, expected, code):
        if env.get(name) != expected:
            findings.append(code)

    require("HEDGEOPS_REQUIRE_IDENTITY", "1", "identity_must_fail_closed")
    require("HEDGEOPS_PROXY_TLS_VERIFIED", "1", "tls_proxy_not_verified")
    require("HEDGEOPS_PROXY_RATE_LIMIT_VERIFIED", "1", "rate_limit_not_verified")
    require("HEDGEOPS_PROXY_DEADLINE_VERIFIED", "1", "request_deadline_not_verified")
    require("HEDGEOPS_PROXY_LOGGING_VERIFIED", "1", "request_logging_not_verified")
    origin = env.get("HEDGEOPS_PUBLIC_ORIGIN", "")
    try:
        parsed = urlparse(origin)
        valid = (parsed.scheme == "https" and bool(parsed.hostname)
                 and parsed.port is None and not parsed.username and not parsed.password
                 and parsed.path in ("", "/") and not parsed.query and not parsed.fragment)
    except ValueError:
        valid = False
    if not valid:
        findings.append("production_https_origin_required")
    if env.get("HEDGEOPS_HOST", "127.0.0.1") not in ("127.0.0.1", "::1", "localhost"):
        findings.append("backend_must_bind_loopback")
    return {"ok": not findings, "findings": findings}
