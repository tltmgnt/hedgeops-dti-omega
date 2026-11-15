# Phase 49 — Consolidated release evidence readiness

Run `python -m hedgeops.release_readiness` from `review_app/` to check the committed production release-gate register and independent security-review register together. A successful command reports `production_ready: false`; it means the documented block is consistent, **not** that production is approved.

The checker rejects missing or malformed gate/control entries, unsupported approval assertions and a premature ready status. It does not authenticate reviewers, inspect live infrastructure, collect external evidence, or change either register. Human review, external security evidence, independent domain validation and final maintainer authorization remain required.
