"""Deterministic research decision evaluator. No execution or approval pathway.

The numerical quantities in this module are illustrative, unvalidated proxies.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import math
from uuid import uuid4

ROLES = ("economic", "statistical", "machine_learning", "behavioral", "risk", "arbitration")

def number(value, name, low=None, high=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite and numeric")
    if (low is not None and value < low) or (high is not None and value > high):
        raise ValueError(f"{name} out of bounds")
    return float(value)

@dataclass(frozen=True)
class Capacity:
    horizon_minutes: float
    committed_minutes: float
    fragmentation_index: float
    autonomy_fraction: float
    recovery_minutes: float = 0.0

    def __post_init__(self):
        horizon = number(self.horizon_minutes, "horizon_minutes", 0)
        if horizon <= 0:
            raise ValueError("horizon_minutes must be positive")
        number(self.committed_minutes, "committed_minutes", 0, horizon)
        number(self.fragmentation_index, "fragmentation_index", 0, 1)
        number(self.autonomy_fraction, "autonomy_fraction", 0, 1)
        number(self.recovery_minutes, "recovery_minutes", 0)

    @property
    def free_minutes(self):
        return self.horizon_minutes - self.committed_minutes

    @property
    def toc_proxy(self):
        return self.free_minutes / self.horizon_minutes

    @property
    def effective_minutes(self):
        return max(0, self.free_minutes - self.recovery_minutes) * (1 - self.fragmentation_index) * self.autonomy_fraction

@dataclass(frozen=True)
class Scenario:
    objective: str
    required_minutes: float
    capacity: Capacity
    uncertainty: float = 0.5
    expected_value: float = 0.0
    downside_exposure: float = 0.0
    max_downside: float = 0.0
    evidence_verified: bool = False
    constraints_verified: bool = False

    def __post_init__(self):
        if not isinstance(self.objective, str) or not self.objective.strip():
            raise ValueError("objective required")
        if not isinstance(self.capacity, Capacity):
            raise ValueError("capacity must be Capacity")
        number(self.required_minutes, "required_minutes", 0)
        number(self.uncertainty, "uncertainty", 0, 1)
        number(self.expected_value, "expected_value")
        number(self.downside_exposure, "downside_exposure", 0)
        number(self.max_downside, "max_downside", 0)
        if type(self.evidence_verified) is not bool or type(self.constraints_verified) is not bool:
            raise ValueError("verification flags must be booleans")

def from_dict(data):
    if not isinstance(data, dict):
        raise ValueError("scenario must be an object")
    if set(data) - set(Scenario.__dataclass_fields__):
        raise ValueError("unknown scenario fields")
    cap = data.get("capacity")
    if not isinstance(cap, dict) or set(cap) - set(Capacity.__dataclass_fields__):
        raise ValueError("invalid capacity object")
    required = {"objective", "required_minutes", "capacity"}
    if not required.issubset(data):
        raise ValueError("missing required scenario fields: " + ", ".join(sorted(required - set(data))))
    required_capacity = {"horizon_minutes", "committed_minutes", "fragmentation_index", "autonomy_fraction"}
    if not required_capacity.issubset(cap):
        raise ValueError("missing required capacity fields: " + ", ".join(sorted(required_capacity - set(cap))))
    return Scenario(**{**data, "capacity": Capacity(**cap)})

def evaluate(scenario):
    c = scenario.capacity
    flags = []
    def block(code, message):
        flags.append({"code": code, "severity": "high", "blocks_execution": True, "message": message})
    if scenario.required_minutes > c.effective_minutes:
        block("INSUFFICIENT_CAPACITY", "Required time exceeds effective temporal capacity")
    if scenario.downside_exposure > scenario.max_downside:
        block("DOWNSIDE_LIMIT", "Downside exposure exceeds stated limit")
    if not scenario.evidence_verified:
        block("UNVERIFIED_EVIDENCE", "Evidence has not been independently verified")
    if not scenario.constraints_verified:
        block("UNVERIFIED_CONSTRAINTS", "Constraints have not been independently verified")
    assessments = [
        {"agent": "economic", "summary": "Expected value is user supplied; no market data connected", "confidence": 0.2},
        {"agent": "statistical", "summary": "No calibrated statistical forecast available", "confidence": 0.1},
        {"agent": "machine_learning", "summary": "No trained predictive model configured", "confidence": 0.0},
        {"agent": "behavioral", "summary": "Autonomy and fragmentation need independent review", "confidence": 0.2},
        {"agent": "risk", "summary": "Hard limits evaluated deterministically", "confidence": 1.0, "risk_flags": flags},
        {"agent": "arbitration", "summary": "Six roles accounted for; no automatic authorization", "confidence": 0.5},
    ]
    return {
        "record_id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "request": asdict(scenario),
        "status": "blocked" if flags else "needs_review",
        "human_approval_required": True,
        "execution_authorized": False,
        "capacity": {"free_minutes": c.free_minutes, "toc_proxy": c.toc_proxy, "effective_minutes": c.effective_minutes},
        "heuristic_value_after_uncertainty": scenario.expected_value * (1 - scenario.uncertainty),
        "risk_flags": flags,
        "assessments": assessments,
        "recommendation": "Do not execute. Independent human review required.",
    }

def simulate(scenario, fragmentation_values=(0, 0.25, 0.5, 0.75, 1)):
    results = []
    for value in fragmentation_values:
        number(value, "fragmentation", 0, 1)
        cap = Capacity(**{**asdict(scenario.capacity), "fragmentation_index": value})
        results.append({"fragmentation_index": value, "effective_minutes": cap.effective_minutes,
                        "feasible": scenario.required_minutes <= cap.effective_minutes})
    return results
