# Request parsing limits

The review API limits POST bodies to 65,536 bytes and request targets to 2,048 characters. It rejects ambiguous or oversized Content-Length representations, duplicate JSON object keys, and malformed JSON/UTF-8. The limits reduce parser ambiguity and obvious resource exhaustion but are not a full denial-of-service defense. The standard-library HTTP server still requires an independently reviewed reverse proxy with connection limits, read timeouts, and rate limiting for any non-local deployment.
