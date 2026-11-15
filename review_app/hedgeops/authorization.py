"""Conservative role policy for future authenticated review sessions.

No HTTP header or caller-supplied role is trusted as an identity assertion.
"""
ROLES = frozenset({"viewer", "analyst", "auditor", "administrator"})
READ_ROUTES = frozenset({"/", "/dashboard", "/health", "/decisions"})
AUDIT_ROUTES = frozenset({"/audit/verify"})
WRITE_ROUTES = frozenset({"/decisions", "/simulate"})


def permitted(role, method, path):
    if role not in ROLES or method not in ("GET", "POST"):
        return False
    if method == "GET":
        if path in READ_ROUTES or path.startswith("/decisions/"):
            return True
        if path in AUDIT_ROUTES:
            return role in ("auditor", "administrator")
        return False
    return path in WRITE_ROUTES and role in ("analyst", "administrator")


def identity_enforced():
    """Strict mode cannot run without a reviewed identity integration."""
    import os
    return os.getenv("HEDGEOPS_REQUIRE_IDENTITY", "") == "1"
