# HedgeOps Ω — Decision Topology v1

**Status: bounded research software.** This adds typed, non-executable review
graphs and deterministic temporal sensitivity branches. It does **not** add
trading execution, trained models, a live regime detector, a causal estimator,
a self-modifying agent, or decision authorization.

## Purpose and public API

The maintained installable package is the repository-root `hedgeops/`.
The existing `evaluate_decision()` behavior is unchanged. Its new additive
entrypoint produces the original `DecisionRecord` alongside an auditable
typed graph:

```python
from hedgeops.engine import evaluate_decision_with_topology
from hedgeops.models import DecisionRequest

record, topology = evaluate_decision_with_topology(
    DecisionRequest(objective="Synthetic review")
)
assert topology.to_dict()["execution_authorized"] is False
assert topology.to_dict()["human_approval_required"] is True
```

The graph holds request, six agent assessments, risk flags, unresolved questions
and the resulting review disposition. Edges carry typed roles:
`assesses`, `raises`, `identifies` and `informs`. Node identifiers are
deterministic within a decision record, using the existing record/decision IDs.
The graph does not copy or independently authenticate the evidence; it is a
read-only projection of the original record.

## Invariants

- Exactly six *unique* assessment roles, one request and one decision node.
- Only `blocked` and `needs_review` review states are allowed.
- A blocking/critical risk cannot produce `needs_review`.
- Human approval remains required; execution authorization is always false.
- No duplicate node IDs/edges, dangling links or directed cycles.
- Graph size capped at 5,000 nodes and 20,000 edges.
- Invalid projections raise `ValueError`; they do not fall back to an
  apparently safe decision.

The engine remains authoritative for risk assessment. A graph is neither
an independent risk engine nor a substitute for authenticated evidence.

## Temporal what-if analysis

```python
from hedgeops.state import TemporalCapacityState
from hedgeops.decision_topology import simulate_temporal_branches

state = TemporalCapacityState(
    horizon_minutes=120, committed_minutes=70,
    fragmentation_index=0.25, autonomy_fraction=0.8,
    recovery_minutes=10,
)
branches = simulate_temporal_branches(state, required_minutes=30)
for branch in branches:
    print(branch.to_dict())
```

Effective minutes follow the existing *provisional* review-app proxy:

```text
free_minutes = horizon_minutes - committed_minutes
effective_minutes = max(0, free_minutes - recovery_minutes)
                    * (1 - fragmentation_index) * autonomy_fraction
```

These are **hypothetical sensitivity branches**, not identified causal
effects. Changing fragmentation in the model does not assert that an
intervention can achieve the change. Feasibility refers only to the specified
time requirement; it does not lift any financial, legal, evidence or execution
block. Inputs are numeric and finite, and scenarios are bounded at 100.

## Ten-family research taxonomy

`FAMILY_CAPABILITIES` enumerates the ten requested concepts with honest
maturity labels:

| Family | v1 maturity |
| --- | --- |
| Axiomatic | Bounded: existing safety invariants |
| Probabilistic | Research only |
| Game-theoretic | Research only |
| Reinforcement learning | Research only |
| Counterfactual | Bounded: temporal what-if sensitivity only |
| Regime-switching | Research only |
| Behavioral | Research only; placeholder agent already exists |
| Information-theoretic | Research only |
| Topological | Bounded: typed assessment/dependency DAG |
| Meta/self-modifying | Research only |

These are overlapping methodological families, not a mathematically
exhaustive or disjoint classification of all possible decision trees.
There is no claim that the registry dynamically implements all ten.

## Validation and development boundaries

Run:

```sh
python -m pip install . pytest
python -m pytest tests -q
```

CI already checks Python 3.10 and 3.12 for the maintained package.
Follow the repository's [topology curriculum](portfolio/TOPOLOGY_CURRICULUM_V2.md)
and [integration contracts](../integration_contracts/README.md).
The `review_app/` implementation is kept isolated under its own namespace;
this extension does not add a dependency from the maintained package to it.

**Next research gate:** compare this projection with the simpler existing
record structure on a prespecified audit/review task. Validate time-proxy
units and held-out behavior before reporting incremental benefit. Later
probabilistic or causal engines require calibration, provenance and
independent tests; self-modifying policies must not change review controls.
