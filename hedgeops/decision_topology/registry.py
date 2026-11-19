"""Explicit research taxonomy: three bounded capabilities, seven unimplemented."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DecisionFamily(str, Enum):
    AXIOMATIC = "axiomatic"
    PROBABILISTIC = "probabilistic"
    GAME_THEORETIC = "game_theoretic"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    COUNTERFACTUAL = "counterfactual"
    REGIME_SWITCHING = "regime_switching"
    BEHAVIORAL = "behavioral"
    INFORMATION_THEORETIC = "information_theoretic"
    TOPOLOGICAL = "topological"
    META = "meta"


@dataclass(frozen=True)
class FamilyCapability:
    family: DecisionFamily
    maturity: str
    scope: str


FAMILY_CAPABILITIES = (
    FamilyCapability(DecisionFamily.AXIOMATIC, "bounded", "Existing review-only rules and blocking invariants"),
    FamilyCapability(DecisionFamily.PROBABILISTIC, "research_only", "Requires data and calibration"),
    FamilyCapability(DecisionFamily.GAME_THEORETIC, "research_only", "Requires players, payoffs and solution concept"),
    FamilyCapability(DecisionFamily.REINFORCEMENT_LEARNING, "research_only", "Requires offline policy evaluation"),
    FamilyCapability(DecisionFamily.COUNTERFACTUAL, "bounded", "Temporal what-if sensitivity, not causal identification"),
    FamilyCapability(DecisionFamily.REGIME_SWITCHING, "research_only", "Requires validated latent-state model"),
    FamilyCapability(DecisionFamily.BEHAVIORAL, "research_only", "Existing role is a rule-based placeholder"),
    FamilyCapability(DecisionFamily.INFORMATION_THEORETIC, "research_only", "Requires defined observations and acquisition costs"),
    FamilyCapability(DecisionFamily.TOPOLOGICAL, "bounded", "Typed assessment/dependency DAG, not systemic-risk inference"),
    FamilyCapability(DecisionFamily.META, "research_only", "Policy self-modification is not enabled"),
)
