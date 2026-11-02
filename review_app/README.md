# HedgeOps Ω — local-review integration candidate

This directory contains a **standalone, standard-library-only Python 3.11+ reference implementation**. It is deliberately isolated from the repository's deeply nested legacy `src/` modules. The legacy source remains unchanged.

The six assessments are rule-based placeholders, **not trained ML or statistically calibrated forecasts**. TOC and effective-minutes calculations are provisional research proxies, not validated measures. Evaluations are never executable or automatically approved.

## Run

```bash
cd review_app
python -m unittest discover -s tests -v
python -m hedgeops
```

Open http://127.0.0.1:8080/ and submit illustrative scenarios. The HTTP API supports `POST /decisions`, `POST /simulate`, `GET /decisions?limit=20`, `GET /decisions/{id}`, `GET /audit/verify`, and `GET /health`.

```bash
curl http://127.0.0.1:8080/health
```

Set `HEDGEOPS_API_TOKEN` to require a bearer token for API requests. The dashboard also requires bearer authentication when a token is configured. Only bind to loopback for local review; **do not expose directly to the internet**. An HTTPS proxy, robust authentication, rate limiting, external audit anchoring and deployment security review are needed for production.

Run `python -m hedgeops.preflight` for an offline security configuration check before deployment; passing it is not a production approval.\n\n## Integration status

This is a non-destructive review branch. It does **not** unify the existing nested code, validate the original test suite, or claim production readiness. The existing legacy six-agent engine remains review-only; no financial transaction or brokerage endpoint is added.
