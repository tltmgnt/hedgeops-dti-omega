from hedgeops.agents import assess_all
from hedgeops.engine import evaluate_decision
from hedgeops.models import (
    AgentRole,
    AgentAssessment,
    DecisionRequest,
    DecisionStatus,
    RiskFlag,
    Severity,
)


def test_all_six_agents_return_assessments():
    request = DecisionRequest(objective="Evaluate a hypothetical investment scenario")

    assessments = assess_all(request)

    assert len(assessments) == 6
    assert {item.agent for item in assessments} == set(AgentRole)


def test_decision_requires_human_review():
    request = DecisionRequest(objective="Review a hypothetical decision")

    record = evaluate_decision(request)

    assert record.human_approval_required is True
    assert record.status == DecisionStatus.BLOCKED
    assert record.recommendation


def test_risk_agent_blocks_unverified_execution():
    request = DecisionRequest(objective="Test risk controls")

    record = evaluate_decision(request)

    assert record.has_blocking_risk is True
    assert record.status == DecisionStatus.BLOCKED
    assert any(
        flag.blocks_execution
        for assessment in record.assessments
        for flag in assessment.risk_flags
    )


def test_uncertainties_are_preserved():
    request = DecisionRequest(objective="Test uncertainty tracking")

    record = evaluate_decision(request)

    assert record.unresolved_questions
    assert all(isinstance(question, str) for question in record.unresolved_questions)


def test_critical_risk_flag_is_blocking():
    request = DecisionRequest(objective="Test critical risk")
    assessment = AgentAssessment(
        agent=AgentRole.RISK,
        summary="Critical risk identified",
        confidence=1.0,
        risk_flags=[
            RiskFlag(
                code="CRITICAL_TEST",
                message="A critical constraint has failed.",
                severity=Severity.CRITICAL,
            )
        ],
    )

    from hedgeops.models import DecisionRecord

    record = DecisionRecord(request=request)
    record.add_assessment(assessment)

    assert record.has_blocking_risk is True
    assert record.status == DecisionStatus.BLOCKED


def test_decision_record_can_be_converted_to_dict():
    request = DecisionRequest(objective="Test audit record")

    record = evaluate_decision(request)
    data = record.to_dict()

    assert data["request"]["objective"] == "Test audit record"
    assert data["human_approval_required"] is True
    assert "assessments" in data


def test_missing_role_stays_blocked_without_risk_flags():
    """Missing role coverage is independently sufficient to block review output."""
    from unittest.mock import patch

    request = DecisionRequest(objective="Synthetic incomplete-role regression")
    complete = [
        AgentAssessment(role, "Synthetic no-risk assessment", 0.5)
        for role in AgentRole
    ]
    with patch("hedgeops.engine.assess_all", return_value=complete):
        assert evaluate_decision(request).status == DecisionStatus.NEEDS_REVIEW
    for omitted in AgentRole:
        remaining = [row for row in complete if row.agent != omitted]
        with patch("hedgeops.engine.assess_all", return_value=remaining):
            record = evaluate_decision(request)
        assert record.status == DecisionStatus.BLOCKED
        assert record.human_approval_required is True
        assert "Not all required agent roles returned an assessment." in record.unresolved_questions
        assert "missing assessments" in record.recommendation
