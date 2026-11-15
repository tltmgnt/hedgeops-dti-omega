# Release-validation deployment gates

The `release-validation` GitHub Actions matrix (Python 3.11, 3.12, 3.13) now executes the offline deployment preflight policy gates after review-app unit tests.

The gates verify that local defaults are allowed with warnings, an unauthenticated non-loopback bind is rejected, an HTTP public origin is rejected for non-loopback use, and a fully specified HTTPS-origin configuration passes lint while retaining the reverse-proxy warning.

These are synthetic CI configurations with placeholder values, not deployment secrets. They do not prove that a reverse proxy, identity provider, TLS, network controls, or audit key is correctly deployed. Passing CI does not authorize production release.
