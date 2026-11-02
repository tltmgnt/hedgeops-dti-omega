# Production release gates

`docs/release-gates.json` is a machine-readable register of seven independent release requirements. All are **unapproved** and production status is **blocked**. Each approval requires a unique remote HTTPS evidence URL with a record path (no embedded credentials, explicit port, fragment, or loopback host). Unapproved gates must have null evidence. These checks validate reference shape only; they do not fetch or attest to external evidence.  changing the status to `ready_for_manual_review` is possible only when every gate is approved. Even then, this status does **not** deploy, merge, or authorize production release.

Run `python review_app/scripts/check_release_gates.py --expect-blocked` from the repository root to validate the current policy and confirm it remains blocked. The release-validation CI matrix runs the same check. If the gate file is modified to imply readiness, the current CI policy fails closed until maintainers explicitly revise the release process.

The register is a review workflow aid, not cryptographic evidence. Independent sign-off, ownership, operational evidence and explicit human authorization remain mandatory.
