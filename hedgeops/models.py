
"""Core data models for HedgeOps Omega and DTI Omega."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


class AgentRole(str, Enum):
    ECONOMIC = "economic"
    STATISTICAL = "statistical"
    MACHINE_LEARNING = "machine_learning"
    BEHAVIORAL = "behavioral"
    RISK = "risk"
    ARBITRATION = "arbitration"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionStatus(str, Enum):
    PROPOSED = "proposed"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"
    APPROVED_BY_HUMAN = "approved_by_human"
    REJECTED_BY_HUMAN = "rejected_by_human"


@dataclass
class RiskFlag:
    """A risk or constraint identified during decision review."""

    code: str
    message: str
    severity: Severity = Severity.MEDIUM
    blocks_execution: bool = False

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("RiskFlag code must not be empty.")
        if not self.message.strip():
            raise ValueError("RiskFlag message must not be empty.")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible risk flag."""
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "blocks_execution": self.blocks_execution,
        }


@dataclass
class AgentAssessment:
    """One agent's assessment of a proposed decision."""

    agent: AgentRole
    summary: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
    risk_flags: list[RiskFlag] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0.")
        if not self.summary.strip():
            raise ValueError("Assessment summary must not be empty.")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible assessment."""
        return {
            "agent": self.agent.value,
            "summary": self.summary,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
            "assumptions": list(self.assumptions),
            "uncertainties": list(self.uncertainties),
            "risk_flags": [
                flag.to_dict() for flag in self.risk_flags
            ],
            "created_at": self.created_at,
        }


@dataclass
class DecisionRequest:
    """A decision submitted for analysis, not an instruction to execute."""

    objective: str
    context: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    decision_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ValueError("Decision objective must not be empty.")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible request."""
        return {
            "objective": self.objective,
            "context": self.context,
            "constraints": list(self.constraints),
            "decision_id": self.decision_id,
            "created_at": self.created_at,
        }


@dataclass
class DecisionRecord:
    """Auditable analysis record with human approval kept separate."""

    request: DecisionRequest
    assessments: list[AgentAssessment] = field(default_factory=list)
    status: DecisionStatus = DecisionStatus.PROPOSED
    recommendation: str = ""
    unresolved_questions: list[str] = field(default_factory=list)
    human_approval_required: bool = True
    record_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)

    @property
    def has_blocking_risk(self) -> bool:
        """Check whether any assessment contains a blocking or critical risk."""
        return any(
            flag.blocks_execution or flag.severity == Severity.CRITICAL
            for assessment in self.assessments
            for flag in assessment.risk_flags
        )

    def add_assessment(self, assessment: AgentAssessment) -> None:
        """Add an assessment and update the preliminary status."""
        self.assessments.append(assessment)

        if self.has_blocking_risk:
            self.status = DecisionStatus.BLOCKED
        elif self.status == DecisionStatus.PROPOSED:
            self.status = DecisionStatus.NEEDS_REVIEW

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible decision record."""
        return {
            "request": self.request.to_dict(),
            "assessments": [
                assessment.to_dict()
                for assessment in self.assessments
            ],
            "status": self.status.value,
            "recommendation": self.recommendation,
            "unresolved_questions": list(self.unresolved_questions),
            "human_approval_required": self.human_approval_required,
            "record_id": self.record_id,
            "created_at": self.created_at,
            "has_blocking_risk": self.has_blocking_risk,
        }

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize the decision record as JSON."""
        return json.dumps(
            self.to_dict(),
            indent=indent,
            allow_nan=False,
        )
