# Cross-system contracts

These tests launch each HedgeOps implementation in a separate Python process to avoid collisions between the two `hedgeops` namespaces.

Contracts verify:
- six role identifiers match;
- unverified scenarios remain blocked;
- human review is mandatory;
- no execution authority is granted;
- assessments include summaries.

They do **not** establish numerical equivalence, statistical calibration, empirical validity, or production readiness. The original nested files are still preserved unchanged; `legacy_compat` is a compatibility snapshot.
Run from the repository root: `python -m unittest discover -s integration_contracts -v`.
