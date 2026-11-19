"""Build and validate bounded assessment/dependency DAGs from existing records.

This is a visualization/analysis projection, NOT a new decision authority.
"""
from __future__ import annotations

from collections import deque

from hedgeops.models import AgentRole, DecisionRecord, DecisionStatus, Severity

from .schema import DecisionEdge, DecisionNode, DecisionTopology, EdgeKind, NodeKind


def validate_topology(topology: DecisionTopology) -> None:
    """Reject malformed, cyclic, incomplete or executable decision graphs."""
    if not isinstance(topology, DecisionTopology):
        raise ValueError("topology must be a DecisionTopology")
    if not topology.record_id:
        raise ValueError("record_id required")
    if topology.human_approval_required is not True or topology.execution_authorized is not False:
        raise ValueError("topology cannot bypass human review or authorize execution")
    if topology.status not in {DecisionStatus.BLOCKED.value, DecisionStatus.NEEDS_REVIEW.value}:
        raise ValueError("only blocked and needs_review statuses are supported")
    if len(topology.nodes) > 5000 or len(topology.edges) > 20000:
        raise ValueError("topology exceeds bounded graph limits")

    nodes = {}
    for node in topology.nodes:
        if not isinstance(node, DecisionNode) or not isinstance(node.kind, NodeKind):
            raise ValueError("invalid node")
        if not isinstance(node.node_id, str) or not node.node_id or node.node_id in nodes:
            raise ValueError("duplicate or empty node ID")
        if not isinstance(node.label, str) or not node.label.strip():
            raise ValueError("node label required")
        if not isinstance(node.attributes, dict):
            raise ValueError("node attributes must be a dictionary")
        nodes[node.node_id] = node

    roles = [n.attributes.get("role") for n in nodes.values() if n.kind == NodeKind.ASSESSMENT]
    if len(roles) != len(AgentRole) or set(roles) != {role.value for role in AgentRole}:
        raise ValueError("all six unique assessment roles are required")
    if sum(n.kind == NodeKind.REQUEST for n in nodes.values()) != 1:
        raise ValueError("exactly one request node required")
    if sum(n.kind == NodeKind.DECISION for n in nodes.values()) != 1:
        raise ValueError("exactly one decision node required")
    decisions = [n for n in nodes.values() if n.kind == NodeKind.DECISION]
    if decisions[0].attributes.get("status") != topology.status:
        raise ValueError("decision node and topology statuses disagree")
    if topology.status == DecisionStatus.NEEDS_REVIEW.value:
        for n in nodes.values():
            if n.kind == NodeKind.RISK_FLAG and n.attributes.get("blocking") is True:
                raise ValueError("blocking flags require blocked status")

    indegree = {node_id: 0 for node_id in nodes}
    successors = {node_id: [] for node_id in nodes}
    seen = set()
    for edge in topology.edges:
        if not isinstance(edge, DecisionEdge) or not isinstance(edge.kind, EdgeKind):
            raise ValueError("invalid edge")
        if edge.source not in nodes or edge.target not in nodes:
            raise ValueError("dangling graph edge")
        signature = (nodes[edge.source].kind, nodes[edge.target].kind, edge.kind)
        permitted = {
            (NodeKind.REQUEST, NodeKind.ASSESSMENT, EdgeKind.ASSESSES),
            (NodeKind.ASSESSMENT, NodeKind.RISK_FLAG, EdgeKind.RAISES),
            (NodeKind.REQUEST, NodeKind.UNCERTAINTY, EdgeKind.IDENTIFIES),
            (NodeKind.ASSESSMENT, NodeKind.UNCERTAINTY, EdgeKind.IDENTIFIES),
            (NodeKind.ASSESSMENT, NodeKind.DECISION, EdgeKind.INFORMS),
            (NodeKind.RISK_FLAG, NodeKind.DECISION, EdgeKind.INFORMS),
            (NodeKind.UNCERTAINTY, NodeKind.DECISION, EdgeKind.INFORMS),
        }
        if signature not in permitted:
            raise ValueError("invalid typed dependency edge")
        key = (edge.source, edge.target, edge.kind)
        if key in seen:
            raise ValueError("duplicate graph edge")
        seen.add(key)
        successors[edge.source].append(edge.target)
        indegree[edge.target] += 1

    queue = deque(node_id for node_id, degree in indegree.items() if degree == 0)
    visited = 0
    while queue:
        node_id = queue.popleft()
        visited += 1
        for target in successors[node_id]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if visited != len(nodes):
        raise ValueError("decision topology contains a directed cycle")

    # Beyond acyclicity, require the review pathways to remain fully connected.
    request_id = next(n.node_id for n in nodes.values() if n.kind == NodeKind.REQUEST)
    decision_id = decisions[0].node_id
    edge_set = {(edge.source, edge.target, edge.kind) for edge in topology.edges}
    for node in nodes.values():
        if node.kind == NodeKind.ASSESSMENT:
            if ((request_id, node.node_id, EdgeKind.ASSESSES) not in edge_set
                    or (node.node_id, decision_id, EdgeKind.INFORMS) not in edge_set):
                raise ValueError("assessment pathway is incomplete")
        elif node.kind == NodeKind.RISK_FLAG:
            if (not isinstance(node.attributes.get("code"), str)
                    or not node.attributes["code"]
                    or node.attributes.get("severity") not in {s.value for s in Severity}
                    or type(node.attributes.get("blocking")) is not bool):
                raise ValueError("invalid risk flag attributes")
            if node.attributes["severity"] == Severity.CRITICAL.value and not node.attributes["blocking"]:
                raise ValueError("critical risk must remain blocking")
            producers = [e for e in topology.edges
                         if e.target == node.node_id and e.kind == EdgeKind.RAISES]
            if (len(producers) != 1
                    or (node.node_id, decision_id, EdgeKind.INFORMS) not in edge_set):
                raise ValueError("risk flag pathway is incomplete")
        elif node.kind == NodeKind.UNCERTAINTY:
            producers = [e for e in topology.edges
                         if e.target == node.node_id and e.kind == EdgeKind.IDENTIFIES]
            if (not producers
                    or (node.node_id, decision_id, EdgeKind.INFORMS) not in edge_set):
                raise ValueError("uncertainty pathway is incomplete")


def build_assessment_topology(record: DecisionRecord) -> DecisionTopology:
    """Project a six-role DecisionRecord into an auditable typed dependency graph.

    Missing or duplicate roles fail closed; the original engine remains authoritative
    for deciding BLOCKED vs NEEDS_REVIEW.
    """
    if not isinstance(record, DecisionRecord):
        raise ValueError("record must be a DecisionRecord")
    if record.human_approval_required is not True:
        raise ValueError("human approval is mandatory")
    if record.status not in (DecisionStatus.BLOCKED, DecisionStatus.NEEDS_REVIEW):
        raise ValueError("only review-only statuses can be projected")
    roles = [assessment.agent for assessment in record.assessments]
    if len(roles) != len(AgentRole) or set(roles) != set(AgentRole):
        raise ValueError("missing or duplicate assessment roles")
    if record.has_blocking_risk and record.status != DecisionStatus.BLOCKED:
        raise ValueError("blocking risk must have blocked status")

    nodes = []
    edges = []
    request_id = "request:" + record.request.decision_id
    decision_id = "decision:" + record.record_id
    nodes.append(DecisionNode(request_id, NodeKind.REQUEST, record.request.objective))
    nodes.append(DecisionNode(decision_id, NodeKind.DECISION, "Review disposition",
                              {"status": record.status.value}))

    for assessment in record.assessments:
        role = assessment.agent.value
        aid = "assessment:" + role
        nodes.append(DecisionNode(aid, NodeKind.ASSESSMENT, assessment.summary,
                                  {"role": role, "confidence": assessment.confidence}))
        edges.append(DecisionEdge(request_id, aid, EdgeKind.ASSESSES))
        edges.append(DecisionEdge(aid, decision_id, EdgeKind.INFORMS))
        for i, flag in enumerate(assessment.risk_flags):
            fid = "risk:" + role + ":" + str(i)
            blocking = flag.blocks_execution or flag.severity == Severity.CRITICAL
            nodes.append(DecisionNode(fid, NodeKind.RISK_FLAG, flag.message,
                                      {"code": flag.code, "severity": flag.severity.value,
                                       "blocking": blocking}))
            edges.append(DecisionEdge(aid, fid, EdgeKind.RAISES))
            edges.append(DecisionEdge(fid, decision_id, EdgeKind.INFORMS))

    for i, question in enumerate(sorted(set(record.unresolved_questions))):
        qid = "uncertainty:" + str(i)
        nodes.append(DecisionNode(qid, NodeKind.UNCERTAINTY, question))
        producers = [a.agent.value for a in record.assessments if question in a.uncertainties]
        if not producers:
            edges.append(DecisionEdge(request_id, qid, EdgeKind.IDENTIFIES))
        for role in producers:
            edges.append(DecisionEdge("assessment:" + role, qid, EdgeKind.IDENTIFIES))
        edges.append(DecisionEdge(qid, decision_id, EdgeKind.INFORMS))

    topology = DecisionTopology(
        record_id=record.record_id,
        nodes=tuple(nodes),
        edges=tuple(edges),
        status=record.status.value,
    )
    validate_topology(topology)
    return topology
