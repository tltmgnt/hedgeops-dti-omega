# Phase 51 — Release handoff integrity

Run `python -m hedgeops.handoff_integrity` from `review_app/` to check the committed release decision, blocked evidence registers, and required NO_GO handoff statements together. The command does not grant approvals, perform deployment, or substitute for independent security review. The check is intentionally conservative and detects missing safety statements, not the truth of external infrastructure claims.

The draft PR must remain unmerged and all seven production release gates remain unapproved until independently verified evidence and explicit human authorization are available.
