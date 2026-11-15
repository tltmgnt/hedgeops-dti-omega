"""Shared read-only contract for both engines.

No imports of either engine, no execution authorization, no mutation.
"""
from dataclasses import dataclass
from typing import Mapping, Any

ROLES = frozenset({"economic", "statistical", "machine_learning", "behavioral", "risk", "arbitration"})
STATUSES = frozenset({"blocked", "needs_review"})

@dataclass(frozen=True)
class DecisionSummary:
    record_id: str
    status: str
    agent_roles: frozenset[str]
    blocking_codes: tuple[str, ...]
    human_approval_required: bool
    execution_authorized: bool

def normalize(record: Mapping[str, Any]) -> DecisionSummary:
    """Fail closed if a record cannot be represented as a safe review result."""
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    status = record.get("status")
    if status not in STATUSES:
        raise ValueError("unsupported or executable decision status")
    if record.get("human_approval_required") is not True:
        raise ValueError("human review must be required")
    if record.get("execution_authorized", False) is not False:
        raise ValueError("execution authorization is forbidden")
    assessments = record.get("assessments")
    if not isinstance(assessments, list):
        raise ValueError("assessments must be an array")
    roles = []
    flags = []
    for item in assessments:
        if not isinstance(item, dict) or not isinstance(item.get("agent"), str):
            raise ValueError("invalid assessment")
        if not isinstance(item.get("summary"), str) or not item["summary"].strip():
            raise ValueError("missing assessment explanation")
        roles.append(item["agent"])
        if not isinstance(item.get("risk_flags", []), list):
            raise ValueError("invalid risk flags")
        flags.extend(item.get("risk_flags", []))
    if len(roles) != len(ROLES) or frozenset(roles) != ROLES:
        raise ValueError("all six unique agent roles are required")
    if not isinstance(record.get("risk_flags", []), list):
        raise ValueError("invalid record risk flags")
    flags.extend(record.get("risk_flags", []))
    codes = []
    for flag in flags:
        if not isinstance(flag, dict) or not isinstance(flag.get("code"), str):
            raise ValueError("invalid risk flag")
        if flag.get("blocks_execution") is True or flag.get("severity") == "critical":
            codes.append(flag["code"])
    if codes and status != "blocked":
        raise ValueError("blocking risk cannot have reviewable status")
    rid = record.get("record_id")
    if not isinstance(rid, str) or not rid.strip():
        raise ValueError("record id required")
    return DecisionSummary(
        record_id=rid, status=status, agent_roles=frozenset(roles),
        blocking_codes=tuple(sorted(set(codes))), human_approval_required=True,
        execution_authorized=False,
    )
