# Authentication and host-boundary policy

The review app defaults to loopback binding. With `HEDGEOPS_API_TOKEN` set, all GET and POST routes (including the dashboard) require a bearer token. A non-loopback bind without a token is rejected at startup. Loopback requests additionally reject untrusted HTTP Host headers to reduce DNS-rebinding exposure.

**Local development:** Without a token, loopback access remains available for convenience. Never expose that mode through a proxy or port-forward.

**Production blockers:** The built-in server is not a production identity provider. Deploy only behind reviewed TLS termination, authentication and role-based authorization, CSRF/origin protections, rate limiting, and strict proxy Host handling. The browser dashboard has no production session/login flow; adding a bearer token does not create one. Avoid putting tokens in URLs or client-side page source. A proper login/session design and security assessment are required before production.

HTTP Host checks are defense in depth, not a replacement for firewall rules or proxy configuration.
