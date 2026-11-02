# Production release gates

`docs/release-gates.json` is a machine-readable register of seven independent release requirements. All are **unapproved** and production status is **blocked**. Each approval requires a unique remote HTTPS evidence URL with a record path (no embedded credentials, explicit port, fragment, or loopback host). Unapproved gates must have null evidence. These checks validate reference shape only; they do not fetch or attest to external evidence. Changing the status to `ready_for_manual_review` is possible only when every gate is approved. Even then, this status does **not** deploy, merge, or authorize production release.

Run `python review_app/scripts/check_release_gates.py --expect-blocked` from the repository root to validate the current policy and confirm it remains blocked. The release-validation CI matrix runs the same check. If the gate file is modified to imply readiness, the current CI policy fails closed until maintainers explicitly revise the release process.

The register is a review workflow aid, not cryptographic evidence. Independent sign-off, ownership, operational evidence and explicit human authorization remain mandatory.

## Approval provenance

Every approved gate must also record a reviewer identifier (`reviewer`) and a UTC timestamp ending in `Z` (`reviewed_at`), alongside its unique HTTPS evidence URL. Unapproved gates must not carry these fields with non-null values. The validator checks structure only: it cannot authenticate the reviewer, prove that the timestamp is genuine, or establish separation of duties. Reviewers must verify the linked evidence and approval identity through an independently governed system.

## Separation of duties

The `independent_security_review` and `maintainer_release_approval` gates must have different reviewer identifiers (case-insensitive comparison) when both are approved. This is a basic static guard, not proof of organizational independence, verified identity, or absence of conflicts of interest. An external approval system must enforce identities, roles, separation of duties, and tamper-evident records.

## Approval chronology

Approved review timestamps must not be more than five minutes in the future relative to the validator clock. Final maintainer approval is not permitted until independent security review has been approved, and its timestamp must be strictly later than the security review timestamp. These are metadata checks, not a trusted time source or proof that an approval occurred. The independent approval system must preserve authenticated timestamps and a tamper-evident history.

## Final approval prerequisites

Final maintainer approval is invalid unless every other release requirement is approved with evidence and reviewer provenance. Its timestamp must be strictly later than **each** prerequisite approval, not only the security review. This prevents a release-approval record from being marked complete while other gates are still pending, but does not establish that external evidence or identities are authentic.
