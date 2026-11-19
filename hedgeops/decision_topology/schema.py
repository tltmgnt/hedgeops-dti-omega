"""Typed, non-executable decision graph representation for HedgeOps Ω."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeKind(str, Enum):
    REQUEST = "request"
    ASSESSMENT = "assessment"
    RISK_FLAG = "risk_flag"
    UNCERTAINTY = "uncertainty"
    DECISION = "decision"


class EdgeKind(str, Enum):
    ASSESSES = "assesses"
    RAISES = "raises"
    IDENTIFIES = "identifies"
    INFORMS = "informs"


@dataclass(frozen=True)
class DecisionNode:
    node_id: str
    kind: NodeKind
    label: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.node_id, "kind": self.kind.value,
            "label": self.label, "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class DecisionEdge:
    source: str
    target: str
    kind: EdgeKind

    def to_dict(self) -> dict[str, str]:
        return {"source": self.source, "target": self.target, "kind": self.kind.value}


@dataclass(frozen=True)
class DecisionTopology:
    """A read-only projection of a review record; no execution/approval semantics."""
    record_id: str
    nodes: tuple[DecisionNode, ...]
    edges: tuple[DecisionEdge, ...]
    status: str
    human_approval_required: bool = True
    execution_authorized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "record_id": self.record_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "status": self.status,
            "human_approval_required": self.human_approval_required,
            "execution_authorized": self.execution_authorized,
        }
