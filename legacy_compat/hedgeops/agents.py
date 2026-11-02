"""Six-agent assessment framework for HedgeOps Omega."""

from __future__ import annotations

from dataclasses import dataclass

from .models import AgentAssessment, AgentRole, DecisionRequest, RiskFlag, Severity


@dataclass
class BaseAgent:
    """Base class for transparent, rule-based assessment agents."""

    role: AgentRole

    def assess(self, request: DecisionRequest) -> AgentAssessment:
        raise NotImplementedError("Each agent must implement assess().")


class EconomicAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(AgentRole.ECONOMIC)

    def assess(self, request: DecisionRequest) -> AgentAssessment:
        return AgentAssessment(
            agent=self.role,
            summary="Economic conditions require review using relevant, current evidence.",
            confidence=0.4,
            evidence=["No external economic data source is connected."],
            assumptions=["The decision context may depend on macroeconomic conditions."],
            uncertainties=["Economic regime and scenario impacts have not been verified."],
        )


class StatisticalAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(AgentRole.STATISTICAL)

    def assess(self, request: DecisionRequest) -> AgentAssessment:
        return AgentAssessment(
            agent=self.role,
            summary="Statistical support cannot be established without data and a defined baseline.",
            confidence=0.3,
            evidence=["No dataset or statistical model was supplied."],
            assumptions=["Quantitative evaluation may be relevant to this decision."],
            uncertainties=["Forecast error, calibration, and sample adequacy are unknown."],
        )


class MachineLearningAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(AgentRole.MACHINE_LEARNING)

    def assess(self, request: DecisionRequest) -> AgentAssessment:
        return AgentAssessment(
            agent=self.role,
            summary="No machine-learning prediction is available in this prototype.",
            confidence=0.2,
            evidence=["No trained model or feature dataset is configured."],
            assumptions=["Pattern detection may be useful after data validation."],
            uncertainties=["Generalization and distribution-shift risks are untested."],
        )


class BehavioralAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(AgentRole.BEHAVIORAL)

    def assess(self, request: DecisionRequest) -> AgentAssessment:
        return AgentAssessment(
            agent=self.role,
            summary="Human incentives and decision biases should be reviewed explicitly.",
            confidence=0.4,
            evidence=["No stakeholder interviews or behavioral data were supplied."],
            assumptions=["Human incentives may affect implementation."],
            uncertainties=["Stakeholder incentives and behavioral factors remain unverified."],
        )


class RiskAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(AgentRole.RISK)

    def assess(self, request: DecisionRequest) -> AgentAssessment:
        flags = [
            RiskFlag(
                code="UNVERIFIED_CONSTRAINTS",
                message="Risk limits, data permissions, and execution constraints have not been independently verified.",
                severity=Severity.HIGH,
                blocks_execution=True,
            )
        ]
        return AgentAssessment(
            agent=self.role,
            summary="Execution must remain blocked until applicable constraints are verified.",
            confidence=0.95,
            evidence=["This prototype has no authorized execution or risk-system connection."],
            assumptions=["Conservative controls apply until the decision context is validated."],
            uncertainties=["Actual exposure, liquidity, and operational constraints are unknown."],
            risk_flags=flags,
        )


class ArbitrationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(AgentRole.ARBITRATION)

    def assess(self, request: DecisionRequest) -> AgentAssessment:
        return AgentAssessment(
            agent=self.role,
            summary="Independent evidence and agent findings must be reconciled before a recommendation.",
            confidence=0.5,
            evidence=["This initial arbitration assessment does not yet aggregate other agents."],
            assumptions=["Agent disagreement and missing evidence must remain visible."],
            uncertainties=["A final synthesis requires the complete set of assessments."],
        )


def build_agents() -> list[BaseAgent]:
    """Return the six assessment agents in a predictable order."""
    return [
        EconomicAgent(),
        StatisticalAgent(),
        MachineLearningAgent(),
        BehavioralAgent(),
        RiskAgent(),
        ArbitrationAgent(),
    ]


def assess_all(request: DecisionRequest) -> list[AgentAssessment]:
    """Collect assessments without executing or approving the requested action."""
    return [agent.assess(request) for agent in build_agents()]

