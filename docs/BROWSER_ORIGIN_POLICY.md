# Browser origin policy

POST requests with an `Origin` header must match the expected public origin exactly. On local loopback this defaults to `http://<Host>`. Behind a TLS reverse proxy, configure `HEDGEOPS_PUBLIC_ORIGIN=https://your-reviewed-host.example` and ensure the proxy validates the public Host and TLS boundary. Requests with absent Origin remain supported for non-browser bearer-token API clients.

This check does **not** authenticate users, protect clients whose bearer tokens have leaked, or replace CSRF/session controls. The service still requires a production identity/session design and an independently reviewed reverse proxy. Avoid allowing untrusted callers to control `HEDGEOPS_PUBLIC_ORIGIN`.
