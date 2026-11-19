"""Bounded v1 decision topology invariants and temporal what-if tests."""
from dataclasses import replace
from unittest.mock import patch

import pytest

from hedgeops.decision_topology import (
    DecisionEdge, DecisionFamily, EdgeKind, FAMILY_CAPABILITIES,
    build_assessment_topology, effective_minutes, simulate_temporal_branches,
    validate_topology,
)
from hedgeops.engine import evaluate_decision, evaluate_decision_with_topology
from hedgeops.models import (
    AgentAssessment, AgentRole, DecisionRequest, DecisionStatus,
)
from hedgeops.state import TemporalCapacityState


def complete_no_risk_assessments():
    return [AgentAssessment(agent=role, summary="Synthetic no-risk assessment", confidence=0.5)
            for role in AgentRole]


def no_risk_record():
    with patch("hedgeops.engine.assess_all", return_value=complete_no_risk_assessments()):
        return evaluate_decision(DecisionRequest(objective="Synthetic safe review"))


def example_temporal():
    return TemporalCapacityState(
        horizon_minutes=120, committed_minutes=70,
        fragmentation_index=0.25, autonomy_fraction=0.8,
        recovery_minutes=10,
    )


def test_engine_exposes_additive_review_topology():
    record, graph = evaluate_decision_with_topology(DecisionRequest(objective="Review scenario"))
    assert record.status == DecisionStatus.BLOCKED
    assert graph.status == "blocked"
    assert graph.human_approval_required
    assert graph.execution_authorized is False
    assert graph.record_id == record.record_id
    assert {n.attributes["role"] for n in graph.nodes if n.kind.value == "assessment"} == {
        role.value for role in AgentRole
    }
    assert any(n.kind.value == "risk_flag" and n.attributes["blocking"] for n in graph.nodes)
    assert graph.to_dict()["schema_version"] == 1
    validate_topology(graph)


def test_no_risk_review_is_still_not_approved():
    graph = build_assessment_topology(no_risk_record())
    assert graph.status == "needs_review"
    assert graph.execution_authorized is False
    assert not any(n.kind.value == "risk_flag" for n in graph.nodes)


@pytest.mark.parametrize("omitted", list(AgentRole))
def test_missing_roles_fail_closed(omitted):
    rows = [a for a in complete_no_risk_assessments() if a.agent != omitted]
    with patch("hedgeops.engine.assess_all", return_value=rows):
        record = evaluate_decision(DecisionRequest(objective="Incomplete role check"))
    assert record.status == DecisionStatus.BLOCKED
    with pytest.raises(ValueError, match="roles"):
        build_assessment_topology(record)


def test_duplicate_roles_fail_closed():
    record = no_risk_record()
    record.assessments[-1] = record.assessments[0]
    with pytest.raises(ValueError, match="roles"):
        build_assessment_topology(record)


def test_cannot_project_blocking_risk_as_reviewable():
    record = evaluate_decision(DecisionRequest(objective="Tampered status"))
    record.status = DecisionStatus.NEEDS_REVIEW
    with pytest.raises(ValueError, match="blocking"):
        build_assessment_topology(record)


def test_graph_rejects_bypass_or_executable_state():
    graph = build_assessment_topology(no_risk_record())
    for altered in (
        replace(graph, human_approval_required=False),
        replace(graph, execution_authorized=True),
        replace(graph, status="approved_by_human"),
    ):
        with pytest.raises(ValueError):
            validate_topology(altered)


def test_graph_rejects_dangling_edges_duplicates_and_cycles():
    graph = build_assessment_topology(no_risk_record())
    with pytest.raises(ValueError, match="dangling"):
        validate_topology(replace(graph, edges=graph.edges + (
            DecisionEdge("missing", graph.nodes[0].node_id, EdgeKind.INFORMS),)))
    with pytest.raises(ValueError, match="duplicate"):
        validate_topology(replace(graph, edges=graph.edges + (graph.edges[0],)))
    decision_id = next(n.node_id for n in graph.nodes if n.kind.value == "decision")
    request_id = next(n.node_id for n in graph.nodes if n.kind.value == "request")
    with pytest.raises(ValueError, match="cycle"):
        validate_topology(replace(graph, edges=graph.edges + (
            DecisionEdge(decision_id, request_id, EdgeKind.INFORMS),)))


def test_graph_preserves_uncertainty_provenance():
    record = evaluate_decision(DecisionRequest(objective="Track uncertainty"))
    graph = build_assessment_topology(record)
    questions = {n.label for n in graph.nodes if n.kind.value == "uncertainty"}
    assert questions == set(record.unresolved_questions)
    for node in graph.nodes:
        if node.kind.value == "uncertainty":
            assert any(e.target == node.node_id and e.kind == EdgeKind.IDENTIFIES for e in graph.edges)


def test_temporal_sensitivity_matches_review_app_proxy_formula():
    state = example_temporal()
    assert effective_minutes(state) == pytest.approx(24.0)
    branches = simulate_temporal_branches(state, required_minutes=30, fragmentation_values=[0, 0.25, 1])
    assert [b.effective_minutes for b in branches] == pytest.approx([32, 24, 0])
    assert [b.feasible for b in branches] == [True, False, False]
    assert all(b.baseline_effective_minutes == pytest.approx(24) for b in branches)
    assert state.fragmentation_index == 0.25


def test_temporal_recovery_is_floored_at_zero():
    state = TemporalCapacityState(120, 115, 0, 1, recovery_minutes=20)
    assert effective_minutes(state) == 0.0


@pytest.mark.parametrize("required,values", [
    (float("nan"), [0]), (float("inf"), [0]), (True, [0]),
    (-1, [0]), (1, []), (1, [True]), (1, [float("nan")]),
    (1, [1.1]), (1, [0] * 101),
])
def test_temporal_validation_rejects_invalid_inputs(required, values):
    with pytest.raises(ValueError):
        simulate_temporal_branches(example_temporal(), required, values)


def test_no_trading_authority_and_no_automatic_causal_claim():
    branch = simulate_temporal_branches(example_temporal(), 30)[0].to_dict()
    assert set(branch) == {
        "fragmentation_index", "required_minutes", "effective_minutes",
        "baseline_effective_minutes", "feasible"
    }
    graph = build_assessment_topology(no_risk_record()).to_dict()
    assert graph["execution_authorized"] is False
    assert graph["human_approval_required"] is True


def test_family_registry_is_explicit_about_missing_implementations():
    assert len(DecisionFamily) == 10
    assert {entry.family for entry in FAMILY_CAPABILITIES} == set(DecisionFamily)
    assert {entry.family for entry in FAMILY_CAPABILITIES if entry.maturity == "bounded"} == {
        DecisionFamily.AXIOMATIC, DecisionFamily.COUNTERFACTUAL, DecisionFamily.TOPOLOGICAL
    }
