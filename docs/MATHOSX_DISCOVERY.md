# MathOS × research adapter — hedgeops-dti-omega

This optional, offline, research-only adapter mirrors the bounded [MathOS × discovery engine](https://github.com/tltmgnt/MathOS/pull/39) (source commit 98b9f39). It is **not** connected to application runtime, patient care, financial trading, physical control, or defense operations. It generates 56 **generic mathematical** research questions across 7 frontiers × 4 directions × 2 depths, evaluates finite causal-abstraction and parity examples, and produces NOT_CERTIFIED reports. It does not establish mathematical novelty or proof.

Run: `python -m unittest discover -s tests -p 'test_mathosx_discovery.py' -v` and `python -m mathosx.discovery --limit 16`.

To update rankings, researchers can run `python -m mathosx.discovery --rate-question causal-abstraction:invent:research --outcome useful --evidence-ref review/example-1 --reviewer reviewer-id` and submit a normal reviewed Git change to `mathosx/feedback.v1.json`. The heuristic learns which questions were rated useful, **not** which theorems are true; evidence reviews and domain validation remain manual. CI is read-only and opt-in; no scheduled, paid-model, or autonomous writes are enabled.
