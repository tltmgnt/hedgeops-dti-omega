# Production release gates

`docs/release-gates.json` is a machine-readable register of seven independent release requirements. All are **unapproved** and production status is **blocked**. Each approval requires a unique remote HTTPS evidence URL with a record path (no embedded credentials, explicit port, fragment, or loopback host). Unapproved gates must have null evidence. These checks validate reference shape only; they do not fetch or attest to external evidence. Changing the status to `ready_for_manual_review` is possible only when every gate is approved. Even then, this status does **not** deploy, merge, or authorize production release.

Run `python review_app/scripts/check_release_gates.py --expect-blocked` from the repository root to validate the current policy and confirm it remains blocked. The release-validation CI matrix runs the same check. If the gate file is modified to imply readiness, the current CI policy fails closed until maintainers explicitly revise the release process.

The register is a review workflow aid, not cryptographic evidence. Independent sign-off, ownership, operational evidence and explicit human authorization remain mandatory.

## Authoritative gate inventory

Production release status: BLOCKED

The following seven IDs must match the machine-readable register exactly. These are tracked requirements, not completed approvals.

| Gate ID | Requirement |
| --- | --- |
| `identity_sessions_roles` | Production browser identity, sessions and roles |
| `tls_proxy_rate_limits` | Reviewed TLS proxy, rate limits and operations |
| `immutable_audit_retention` | Externally anchored immutable audit and retention |
| `backup_restore_drill` | Offsite backup and independently verified restore |
| `independent_security_review` | Independent threat and security assessment |
| `domain_model_validation` | Domain-model and behavioral validation |
| `maintainer_release_approval` | Explicit final maintainer authorization |

## Approval provenance

Every approved gate must also record a reviewer identifier (`reviewer`) and a UTC timestamp ending in `Z` (`reviewed_at`), alongside its unique HTTPS evidence URL. Unapproved gates must not carry these fields with non-null values. The validator checks structure only: it cannot authenticate the reviewer, prove that the timestamp is genuine, or establish separation of duties. Reviewers must verify the linked evidence and approval identity through an independently governed system.

## Separation of duties

The `independent_security_review` and `maintainer_release_approval` gates must have different reviewer identifiers (case-insensitive comparison) when both are approved. This is a basic static guard, not proof of organizational independence, verified identity, or absence of conflicts of interest. An external approval system must enforce identities, roles, separation of duties, and tamper-evident records.

## Approval chronology

Approved review timestamps must not be more than five minutes in the future relative to the validator clock. Final maintainer approval is not permitted until independent security review has been approved, and its timestamp must be strictly later than the security review timestamp. These are metadata checks, not a trusted time source or proof that an approval occurred. The independent approval system must preserve authenticated timestamps and a tamper-evident history.

## Final approval prerequisites

Final maintainer approval is invalid unless every other release requirement is approved with evidence and reviewer provenance. Its timestamp must be strictly later than **each** prerequisite approval, not only the security review. This prevents a release-approval record from being marked complete while other gates are still pending, but does not establish that external evidence or identities are authentic.

## Strict schema and ambiguity rejection

The validator rejects duplicate JSON object keys, unexpected top-level or gate fields, and missing required gate fields. Approved gate records may include `reviewer` and `reviewed_at`; the baseline blocked register keeps these optional fields absent. This prevents unrecognized metadata from silently changing the interpretation of release authorization. Any schema evolution requires an explicit validator and test update.

## Input limits

The release-gate JSON file is capped at 16 KiB before decoding. The validator requires UTF-8 JSON and rejects non-finite JSON constants such as `NaN` and `Infinity`, in addition to duplicate keys and unexpected fields. The size cap bounds input processing but is not a substitute for trusted repository permissions or signed release evidence.

## CI negative control

The release-validation matrix constructs a temporary copy of the blocked register, changes only its status to `ready_for_manual_review`, and invokes the real validator in a subprocess. CI requires the validator to exit unsuccessfully with the expected inconsistent-status error. This is a deliberately unauthorized release-ready fixture; it is never committed or treated as approval. The check detects a basic fail-open regression but does not prove comprehensive release-policy correctness.

## Exhaustive gate mutation tests

The unit suite builds a synthetic fully approved register (not the committed production register), then independently revokes each of the seven approvals and corrupts each gate's evidence, reviewer, or timestamp. Every mutation must be rejected. Additional tests reject duplicate gate IDs and a release-ready status with no approvals. These tests establish that the static validator fails closed for the enumerated mutations; they do not authenticate any real approval or remove the production release block.

## Inventory consistency policy

The documentation self-check requires each of the seven authoritative gate identifiers exactly once in the inventory section and rejects unexpected snake_case gate identifiers there. Mentions in later explanatory sections are allowed and do not count as duplicate inventory entries. The test suite exercises extra identifiers, duplicate headings and explanatory mentions to guard against false positives and omissions.
