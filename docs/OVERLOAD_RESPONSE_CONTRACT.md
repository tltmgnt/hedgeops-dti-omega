# Overload response contract

When all 32 request worker slots are occupied, the review HTTP server rejects newly accepted connections with HTTP `503 Service Unavailable`, `Content-Length: 0`, `Connection: close`, and `Retry-After: 1`. It includes no-store, no-sniff, anti-framing and no-referrer headers. The response is deliberately minimal and does not disclose audit data or application internals.

A successful or failed worker releases its semaphore slot. Regression tests cover saturation, recovery, and sequential reuse of a single worker slot. Clients should retry with backoff and jitter, not spin at one-second intervals.

This is a local overload contract, not a service-level guarantee. A reverse proxy must still enforce connection limits, rate limits, and request deadlines.
