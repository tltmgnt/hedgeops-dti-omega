# HTTP method security policy

Only GET and POST are implemented. PUT, PATCH, DELETE, and OPTIONS receive JSON `405 Method Not Allowed` responses **after** host and authentication checks. Unauthorized requests receive JSON `401` responses and the same security headers as ordinary API responses. The application intentionally does not enable CORS preflight or cross-origin browser API access.

This is an incremental boundary hardening measure, not production-grade identity management. The built-in HTTP server must remain behind a reviewed TLS reverse proxy for any non-local use.
