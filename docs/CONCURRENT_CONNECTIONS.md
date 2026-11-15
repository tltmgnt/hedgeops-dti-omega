# Concurrent connection limits

The review HTTP server caps active request worker threads at 32 using a non-blocking bounded semaphore. When all slots are occupied, new accepted connections receive `503 Service Unavailable` with `Connection: close` and are closed without creating a worker. Slots are released after worker termination, including on errors. Existing per-socket read timeouts remain in effect.

This limit is per process and does not bound kernel accept backlog, total bandwidth, CPU per accepted request, or distributed request rates. Use a reviewed reverse proxy with rate limits, overall deadlines, and observability for any non-local deployment.
