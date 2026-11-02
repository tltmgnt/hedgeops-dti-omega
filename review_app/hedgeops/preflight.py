"""Offline deployment configuration preflight; does not start a server."""
import json
import os
from urllib.parse import urlparse
from .proxy_contract import inspect_proxy_contract


def inspect_configuration(env=None):
    env = os.environ if env is None else env
    host = env.get("HEDGEOPS_HOST", "127.0.0.1")
    loopback = host in ("127.0.0.1", "::1", "localhost")
    token = env.get("HEDGEOPS_API_TOKEN", "")
    origin = env.get("HEDGEOPS_PUBLIC_ORIGIN", "")
    findings = []
    if not token:
        findings.append({"severity": "warning" if loopback else "error",
                         "code": "missing_api_token"})
    if not loopback:
        findings.append({"severity": "warning", "code": "non_loopback_binding_requires_reviewed_proxy"})
        if not origin:
            findings.append({"severity": "error", "code": "missing_public_origin"})
    if origin:
        parsed = urlparse(origin)
        if (parsed.scheme not in ("http", "https") or not parsed.hostname
                or parsed.username or parsed.password or parsed.path not in ("", "/")
                or parsed.query or parsed.fragment or parsed.params):
            findings.append({"severity": "error", "code": "invalid_public_origin"})
        elif not loopback and parsed.scheme != "https":
            findings.append({"severity": "error", "code": "public_origin_must_use_https"})
    if not env.get("HEDGEOPS_AUDIT_KEY"):
        findings.append({"severity": "warning", "code": "unsigned_audit_chain"})
    if env.get("HEDGEOPS_PRODUCTION_PREFLIGHT") == "1":
        contract = inspect_proxy_contract(env)
        findings.extend({"severity": "error", "code": code}
                        for code in contract["findings"])
    return {"ok": not any(item["severity"] == "error" for item in findings),
            "binding": "loopback" if loopback else "non_loopback",
            "findings": findings}


def main():
    result = inspect_configuration()
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
