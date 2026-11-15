# Original HedgeOps engine compatibility snapshot

This directory copies the original repository's deeply nested `models.py`, `state.py`, `agents.py`, `engine.py`, and `test_engine.py` into an importable layout, preserving their content for independent testing.

The original files are not modified or deleted. This is a compatibility snapshot, **not** a unified domain model or a claim that the original nested package is repaired. Its existing safety behavior remains review-only.

Run independently from this directory:

```bash
cd legacy_compat
python -m unittest discover -s hedgeops/tests -v
```

Do not put both `review_app` and `legacy_compat` on the same PYTHONPATH: they deliberately have separate `hedgeops` package namespaces. The CI workflow executes them in separate processes and working directories.
