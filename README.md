# HedgeOps / DTI research prototype

Installable, non-executable six-role decision-review framework. The existing nested source files are preserved as legacy snapshots; the maintained importable package is now `hedgeops/` at repository root.

```sh
python -m pip install .
python -c 'from hedgeops.engine import evaluate_decision; from hedgeops.models import DecisionRequest; print(evaluate_decision(DecisionRequest(objective="Synthetic review")).to_dict())'
```

Economic, statistical, machine-learning, behavioral, risk and arbitration roles return transparent rule-based assessments. No trained predictor or external data feed is connected. Records remain blocked or require human review; no financial transaction is executed or authorized. Temporal metrics are provisional operational measures requiring empirical validation.

The restored package preserves the existing model/agent/engine implementations, adds packaging and runs their six original tests in CI. [Portfolio integration](docs/portfolio/INTEGRATION.md) identifies the shared assurance contract and remaining research evidence.

**∞**
