"""Deterministic temporal sensitivity branches, not identified causal effects."""
from __future__ import annotations

import math
from itertools import islice
from dataclasses import dataclass
from typing import Iterable

from hedgeops.state import TemporalCapacityState

DEFAULT_FRAGMENTATION = (0.0, 0.25, 0.5, 0.75, 1.0)


@dataclass(frozen=True)
class TemporalBranch:
    fragmentation_index: float
    required_minutes: float
    effective_minutes: float
    baseline_effective_minutes: float
    feasible: bool

    def to_dict(self) -> dict[str, float | bool]:
        return {
            "fragmentation_index": self.fragmentation_index,
            "required_minutes": self.required_minutes,
            "effective_minutes": self.effective_minutes,
            "baseline_effective_minutes": self.baseline_effective_minutes,
            "feasible": self.feasible,
        }


def _finite_unit(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(name + " must be a finite number")
    if not 0.0 <= value <= 1.0:
        raise ValueError(name + " must be in [0, 1]")
    return float(value)


def effective_minutes(temporal: TemporalCapacityState, *, fragmentation: float | None = None) -> float:
    """Provisional proxy aligned with review_app's Capacity.effective_minutes."""
    if not isinstance(temporal, TemporalCapacityState):
        raise ValueError("temporal must be a TemporalCapacityState")
    f = temporal.fragmentation_index if fragmentation is None else _finite_unit(
        fragmentation, "fragmentation"
    )
    return (
        max(0.0, temporal.free_minutes - temporal.recovery_minutes)
        * (1.0 - f)
        * temporal.autonomy_fraction
    )


def simulate_temporal_branches(
    temporal: TemporalCapacityState,
    required_minutes: float,
    fragmentation_values: Iterable[float] = DEFAULT_FRAGMENTATION,
) -> tuple[TemporalBranch, ...]:
    """Compare bounded hypothetical fragmentation inputs without mutating state."""
    if not isinstance(temporal, TemporalCapacityState):
        raise ValueError("temporal must be a TemporalCapacityState")
    if (isinstance(required_minutes, bool) or not isinstance(required_minutes, (int, float))
            or not math.isfinite(required_minutes) or required_minutes < 0):
        raise ValueError("required_minutes must be a nonnegative finite number")
    try:
        values = tuple(islice(fragmentation_values, 101))
    except TypeError as exc:
        raise ValueError("fragmentation_values must be iterable") from exc
    if not values or len(values) > 100:
        raise ValueError("provide between 1 and 100 fragmentation values")
    baseline = effective_minutes(temporal)
    branches = []
    for value in values:
        fragmentation = _finite_unit(value, "fragmentation")
        capacity = effective_minutes(temporal, fragmentation=fragmentation)
        branches.append(TemporalBranch(
            fragmentation_index=fragmentation,
            required_minutes=float(required_minutes),
            effective_minutes=capacity,
            baseline_effective_minutes=baseline,
            feasible=float(required_minutes) <= capacity,
        ))
    return tuple(branches)
