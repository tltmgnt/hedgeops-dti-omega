# Topology compatibility and curriculum v2 — hedgeops-dti-omega

Version 2 adapts the explicit-molecular-graph teaching pattern to this repository's actual role. This is documentation and a learning/decision framework; it introduces no mathematical engine, runtime dependency or operational permission.

## Repository decision

| Question | Repository-specific answer |
| --- | --- |
| Architectural role | application |
| Minimum useful mathematics | Typed assessment/dependency graphs |
| Relationships to preserve | Six assessment roles, unresolved questions and blocking flags |
| Concrete operation / capstone | Remove one required role or introduce a critical risk and predict the resulting review status |
| Necessity and scope boundary | Graph structure describes the review workflow; it does not establish predictive or economic value |

The decision is a source-based recommendation, not measured proof that a new specialty improves this repository. Start with the existing implementation and compare any proposed abstraction against a simpler alternative.

## Six-criterion compatibility scorecard

Complete one scorecard per proposed candidate and per concrete operation. Leave unmeasured entries unknown. Scores are human judgments from 0 (no fit) to 5 (strong evidenced fit); unknown is not zero. Do not sum an incomplete card. A total out of 30 is a heuristic, not adoption approval, and feasibility or necessity can veto a high total.

| Criterion | Score | Required evidence |
| --- | --- | --- |
| Structural compatibility | Not yet scored | Map the repository objects and the relationships above without losing direction, labels, units or missingness. |
| Transformation support | Not yet scored | Demonstrate the capstone operation on accepted and rejected inputs. |
| Invariant preservation | Not yet scored | State the property preserved and supply a counterexample or perturbation. |
| Computational feasibility | Not yet scored | Measure size, time and memory on bounded fixtures; record limits. |
| Integration compatibility | Not yet scored | Verify existing schemas, APIs and neighboring contracts remain compatible. |
| Mathematical necessity | Not yet scored | Compare with typed assessment/dependency graphs and explain the additional capability, if any. |

## Curriculum

Prerequisites: basic programming, sets, functions and graph vocabulary. Work in six competency-gated sessions, approximately 60–90 minutes each; empirical evaluation is a separate research activity.

| Session | Learning objective | Exercise | Completion evidence |
| --- | --- | --- | --- |
| 1. Model | Identify six assessment roles, unresolved questions and blocking flags. | Draw a minimal valid example and one excluded relationship. | Annotated object/relation inventory with explicit assumptions. |
| 2. Contract | Distinguish schema validity from substantive correctness. | Trace validation and propose malformed, missing and boundary inputs. | Input-to-rejection table grounded in current source. |
| 3. Operation | Explain typed assessment/dependency graphs. | Remove one required role or introduce a critical risk and predict the resulting review status. | Hand trace compared with existing software, or a clearly labeled specification when no runtime exists. |
| 4. Preservation | State what a transformation must preserve. | Rename identifiers, reorder records, then alter one meaningful relation; predict each effect under the actual contract. | Separate invariant, expected change and unsupported transformation. |
| 5. Comparison | Justify mathematical necessity and cost. | Complete the six-criterion card for the existing approach and one proposed alternative; record unknowns honestly. | Evidence-backed recommendation with baseline and explicit veto conditions. |
| 6. Reproduction | Communicate the bounded result. | Reproduce the capstone using existing offline fixtures and record software version, inputs, outputs and limitations. | Reviewable notebook or report distinguishing computation, replay, independent evaluation and authorization. |

## Source-linked reading laboratory

The table is a guided selection of source lines, not an assertion that the whole repository is covered. Line numbers refer to the inspected source blob `575be175f0112151c8e60fa68ccbc6d72d1fb09f` in [hedgeops/engine.py](../../hedgeops/engine.py). Recheck anchors after source changes.

| Line | Statement | Learning check |
| --- | --- | --- |
| [1](../../hedgeops/engine.py#L1) | `"""Decision evaluation engine for HedgeOps Omega."""` | Explain the stated scope and identify a claim the implementation does not establish. |
| [3](../../hedgeops/engine.py#L3) | `from __future__ import annotations` | Identify the dependency and explain which operation needs it. |
| [5](../../hedgeops/engine.py#L5) | `from .agents import assess_all` | Identify the dependency and explain which operation needs it. |
| [6](../../hedgeops/engine.py#L6) | `from .models import (` | Identify the dependency and explain which operation needs it. |
| [7](../../hedgeops/engine.py#L7) | `AgentRole,` | Explain the statement, track its state change and predict its effect on the worked example. |
| [8](../../hedgeops/engine.py#L8) | `DecisionRecord,` | Explain the statement, track its state change and predict its effect on the worked example. |
| [9](../../hedgeops/engine.py#L9) | `DecisionRequest,` | Explain the statement, track its state change and predict its effect on the worked example. |
| [10](../../hedgeops/engine.py#L10) | `DecisionStatus,` | Explain the statement, track its state change and predict its effect on the worked example. |
| [11](../../hedgeops/engine.py#L11) | `Severity,` | Explain the statement, track its state change and predict its effect on the worked example. |
| [12](../../hedgeops/engine.py#L12) | `)` | Explain the statement, track its state change and predict its effect on the worked example. |
| [15](../../hedgeops/engine.py#L15) | `def evaluate_decision(request: DecisionRequest) -> DecisionRecord:` | State the input/output contract and trace one normal and one failing case. |
| [16](../../hedgeops/engine.py#L16) | `"""Evaluate a request and return a reviewable, non-executable record.` | Explain the stated scope and identify a claim the implementation does not establish. |
| [18](../../hedgeops/engine.py#L18) | `All six agents provide assessments. A blocking risk or critical flag` | Explain the statement, track its state change and predict its effect on the worked example. |
| [19](../../hedgeops/engine.py#L19) | `prevents the record from remaining in an ordinary review state.` | Explain the statement, track its state change and predict its effect on the worked example. |
| [20](../../hedgeops/engine.py#L20) | `This function never executes or authorizes a financial transaction.` | Explain the statement, track its state change and predict its effect on the worked example. |
| [21](../../hedgeops/engine.py#L21) | `"""` | Explain the stated scope and identify a claim the implementation does not establish. |
| [22](../../hedgeops/engine.py#L22) | `record = DecisionRecord(request=request)` | Explain the statement, track its state change and predict its effect on the worked example. |
| [23](../../hedgeops/engine.py#L23) | `assessments = assess_all(request)` | Explain the statement, track its state change and predict its effect on the worked example. |
| [25](../../hedgeops/engine.py#L25) | `for assessment in assessments:` | State the loop invariant, termination argument and one boundary case. |
| [26](../../hedgeops/engine.py#L26) | `record.add_assessment(assessment)` | Explain the statement, track its state change and predict its effect on the worked example. |
| [28](../../hedgeops/engine.py#L28) | `record.unresolved_questions = sorted(` | Explain the statement, track its state change and predict its effect on the worked example. |
| [29](../../hedgeops/engine.py#L29) | `{` | Explain the statement, track its state change and predict its effect on the worked example. |
| [30](../../hedgeops/engine.py#L30) | `question` | Explain the statement, track its state change and predict its effect on the worked example. |
| [31](../../hedgeops/engine.py#L31) | `for assessment in assessments` | State the loop invariant, termination argument and one boundary case. |
| [32](../../hedgeops/engine.py#L32) | `for question in assessment.uncertainties` | State the loop invariant, termination argument and one boundary case. |
| [33](../../hedgeops/engine.py#L33) | `}` | Explain the statement, track its state change and predict its effect on the worked example. |
| [34](../../hedgeops/engine.py#L34) | `)` | Explain the statement, track its state change and predict its effect on the worked example. |
| [36](../../hedgeops/engine.py#L36) | `roles_present = {assessment.agent for assessment in assessments}` | State the loop invariant, termination argument and one boundary case. |
| [37](../../hedgeops/engine.py#L37) | `expected_roles = set(AgentRole)` | Explain the statement, track its state change and predict its effect on the worked example. |
| [38](../../hedgeops/engine.py#L38) | `if roles_present != expected_roles:` | Trace both branches and identify the condition that changes the result. |
| [39](../../hedgeops/engine.py#L39) | `record.status = DecisionStatus.BLOCKED` | Explain the statement, track its state change and predict its effect on the worked example. |
| [40](../../hedgeops/engine.py#L40) | `record.unresolved_questions.append(` | Explain the statement, track its state change and predict its effect on the worked example. |
| [41](../../hedgeops/engine.py#L41) | `"Not all required agent roles returned an assessment."` | Explain the statement, track its state change and predict its effect on the worked example. |
| [42](../../hedgeops/engine.py#L42) | `)` | Explain the statement, track its state change and predict its effect on the worked example. |
| [44](../../hedgeops/engine.py#L44) | `blocking_flags = [` | Explain the statement, track its state change and predict its effect on the worked example. |
| [45](../../hedgeops/engine.py#L45) | `flag` | Explain the statement, track its state change and predict its effect on the worked example. |
| [46](../../hedgeops/engine.py#L46) | `for assessment in assessments` | State the loop invariant, termination argument and one boundary case. |
| [47](../../hedgeops/engine.py#L47) | `for flag in assessment.risk_flags` | State the loop invariant, termination argument and one boundary case. |
| [48](../../hedgeops/engine.py#L48) | `if flag.blocks_execution or flag.severity == Severity.CRITICAL` | Trace both branches and identify the condition that changes the result. |
| [49](../../hedgeops/engine.py#L49) | `]` | Explain the statement, track its state change and predict its effect on the worked example. |
| [51](../../hedgeops/engine.py#L51) | `if blocking_flags:` | Trace both branches and identify the condition that changes the result. |
| [52](../../hedgeops/engine.py#L52) | `record.status = DecisionStatus.BLOCKED` | Explain the statement, track its state change and predict its effect on the worked example. |
| [53](../../hedgeops/engine.py#L53) | `record.recommendation = (` | Explain the statement, track its state change and predict its effect on the worked example. |
| [54](../../hedgeops/engine.py#L54) | `"Do not execute. Resolve blocking risk flags and obtain the "` | Explain the statement, track its state change and predict its effect on the worked example. |
| [55](../../hedgeops/engine.py#L55) | `"required independent and human reviews."` | Explain the statement, track its state change and predict its effect on the worked example. |
| [56](../../hedgeops/engine.py#L56) | `)` | Explain the statement, track its state change and predict its effect on the worked example. |
| [57](../../hedgeops/engine.py#L57) | `else:` | Trace both branches and identify the condition that changes the result. |
| [58](../../hedgeops/engine.py#L58) | `record.status = DecisionStatus.NEEDS_REVIEW` | Explain the statement, track its state change and predict its effect on the worked example. |
| [59](../../hedgeops/engine.py#L59) | `record.recommendation = (` | Explain the statement, track its state change and predict its effect on the worked example. |
| [60](../../hedgeops/engine.py#L60) | `"For human review only. Validate the evidence, assumptions, "` | Explain the statement, track its state change and predict its effect on the worked example. |
| [61](../../hedgeops/engine.py#L61) | `"constraints, and uncertainties before making a decision."` | Explain the statement, track its state change and predict its effect on the worked example. |
| [62](../../hedgeops/engine.py#L62) | `)` | Explain the statement, track its state change and predict its effect on the worked example. |
| [64](../../hedgeops/engine.py#L64) | `record.human_approval_required = True` | Explain the statement, track its state change and predict its effect on the worked example. |
| [65](../../hedgeops/engine.py#L65) | `return record` | Predict the returned value and distinguish a computed result from authorization. |
## Assessment and verification

A learner must explain the model, trace the capstone, identify a counterexample and state the scope boundary. Assess these four competencies equally; a numerical score cannot compensate for an unsupported scientific or operational claim.

Relevant existing checks:

- [tests/test_engine.py](../../tests/test_engine.py)

Follow [README](../../README.md) for environment and installed-package instructions. Read scripts before execution; source-reading exercises do not authorize provider calls, model downloads, live orders, hardware actions or messages. Synthetic fixtures establish software behavior only. This documentation change does not report those exercises as already executed.

## Interoperability and adoption gate

Retain explicit domain contracts. Shared assurance records should refer to domain evidence and its assumptions rather than relabeling graph reachability, homology, statistical calibration and epistemic acceptance as interchangeable quantities. The canonical ResearchOs controller remains owned by ResearchOs; this curriculum does not create another controller fork.

Adopt additional mathematics only after a versioned experiment demonstrates a useful operation, the scorecard has evidence, the simpler baseline is inadequate and existing conformance checks remain satisfied. Graph structure describes the review workflow; it does not establish predictive or economic value.
