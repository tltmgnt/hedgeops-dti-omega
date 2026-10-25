"""Decision evaluation engine for HedgeOps Omega."""

from __future__ import annotations

from .agents import assess_all
from .models import (
    AgentRole,
    DecisionRecord,
    DecisionRequest,
    DecisionStatus,
    Severity,
)


def evaluate_decision(request: DecisionRequest) -> DecisionRecord:
    """Evaluate a request and return a reviewable, non-executable record.

    All six agents provide assessments. A blocking risk or critical flag
    prevents the record from remaining in an ordinary review state.
    This function never executes or authorizes a financial transaction.
    """
    record = DecisionRecord(request=request)
    assessments = assess_all(request)

    for assessment in assessments:
        record.add_assessment(assessment)

    record.unresolved_questions = sorted(
        {
            question
            for assessment in assessments
            for question in assessment.uncertainties
        }
    )

    roles_present = {assessment.agent for assessment in assessments}
    expected_roles = set(AgentRole)
    if roles_present != expected_roles:
        record.status = DecisionStatus.BLOCKED
        record.unresolved_questions.append(
            "Not all required agent roles returned an assessment."
        )

    blocking_flags = [
        flag
        for assessment in assessments
        for flag in assessment.risk_flags
        if flag.blocks_execution or flag.severity == Severity.CRITICAL
    ]

    if blocking_flags:
        record.status = DecisionStatus.BLOCKED
        record.recommendation = (
            "Do not execute. Resolve blocking risk flags and obtain the "
            "required independent and human reviews."
        )
    else:
        record.status = DecisionStatus.NEEDS_REVIEW
        record.recommendation = (
            "For human review only. Validate the evidence, assumptions, "
            "constraints, and uncertainties before making a decision."
        )

    record.human_approval_required = True
    return record

