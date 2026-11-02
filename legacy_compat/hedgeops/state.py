
"""Validated dual-state models for DTI Omega and HedgeOps Omega.

The temporal metrics in this module are provisional operational measures.
They require empirical validation before being treated as established metrics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from .models import utc_now


def _validate_timestamp(value: str) -> None:
    """Require a valid timezone-aware ISO-8601 timestamp."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Timestamp must be a non-empty string.")

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Timestamp must be valid ISO-8601.") from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timestamp must include a timezone.")


def _finite_number(name: str, value: float) -> None:
    """Reject booleans, non-numeric values, NaN, and infinity."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number.")

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")


def _unit_interval(name: str, value: float) -> None:
    """Require a finite number between zero and one."""
    _finite_number(name, value)

    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0.0 and 1.0.")


@dataclass(frozen=True)
class EnvironmentalState:
    """Measured representation of the external decision environment.

    Variables are named numeric observations. Uncertainty is a
    provisional normalized estimate between zero and one.
    """

    variables: Mapping[str, float]
    uncertainty: float
    observed_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not isinstance(self.variables, Mapping):
            raise ValueError("variables must be a mapping.")

        clean_variables = {}

        for name, value in self.variables.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Environmental variable names cannot be empty.")

            _finite_number(f"variables[{name}]", value)
            clean_variables[name] = float(value)

        _unit_interval("uncertainty", self.uncertainty)
        _validate_timestamp(self.observed_at)

        object.__setattr__(self, "variables", clean_variables)

    def to_dict(self) -> dict[str, Any]:
        return {
            "variables": dict(self.variables),
            "uncertainty": self.uncertainty,
            "observed_at": self.observed_at,
        }


@dataclass(frozen=True)
class TemporalCapacityState:
    """Operational representation of temporal resource capacity.

    The initial TOC proxy is the proportion of the planning horizon
    not already committed.

    TFI and autonomy are normalized inputs requiring domain-specific
    measurement protocols and empirical validation.
    """

    horizon_minutes: float
    committed_minutes: float
    fragmentation_index: float
    autonomy_fraction: float
    recovery_minutes: float = 0.0
    observed_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        _finite_number("horizon_minutes", self.horizon_minutes)
        _finite_number("committed_minutes", self.committed_minutes)
        _finite_number("recovery_minutes", self.recovery_minutes)

        if self.horizon_minutes <= 0:
            raise ValueError("horizon_minutes must be greater than zero.")

        if not 0 <= self.committed_minutes <= self.horizon_minutes:
            raise ValueError(
                "committed_minutes must be within the planning horizon."
            )

        if self.recovery_minutes < 0:
            raise ValueError("recovery_minutes cannot be negative.")

        _unit_interval(
            "fragmentation_index",
            self.fragmentation_index,
        )
        _unit_interval(
            "autonomy_fraction",
            self.autonomy_fraction,
        )
        _validate_timestamp(self.observed_at)

    @property
    def free_minutes(self) -> float:
        """Minutes not already committed."""
        return self.horizon_minutes - self.committed_minutes

    @property
    def toc_proxy(self) -> float:
        """Provisional temporal availability ratio, from zero to one."""
        return self.free_minutes / self.horizon_minutes

    def to_dict(self) -> dict[str, Any]:
        return {
            "horizon_minutes": self.horizon_minutes,
            "committed_minutes": self.committed_minutes,
            "free_minutes": self.free_minutes,
            "toc_proxy": self.toc_proxy,
            "fragmentation_index": self.fragmentation_index,
            "autonomy_fraction": self.autonomy_fraction,
            "recovery_minutes": self.recovery_minutes,
            "observed_at": self.observed_at,
        }


@dataclass(frozen=True)
class DualState:
    """Unified environmental and temporal state Z_t = (M_t, Theta_t)."""

    environment: EnvironmentalState
    temporal: TemporalCapacityState
    observed_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not isinstance(self.environment, EnvironmentalState):
            raise ValueError("environment must be an EnvironmentalState.")

        if not isinstance(self.temporal, TemporalCapacityState):
            raise ValueError("temporal must be a TemporalCapacityState.")

        _validate_timestamp(self.observed_at)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": "DTI_Omega_DualState",
            "notation": "Z_t = (M_t, Theta_t)",
            "environment": self.environment.to_dict(),
            "temporal": self.temporal.to_dict(),
            "observed_at": self.observed_at,
        }
