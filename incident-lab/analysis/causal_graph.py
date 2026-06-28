"""
Causal Graph Analysis for Incident Root Cause

This module builds causal dependency graphs from incident trajectories
to support root cause analysis and postmortem documentation.

Key capabilities:
1. Extract causal chains from conversation trajectories
2. Identify trigger → propagation → harm sequences
3. Generate Mermaid diagrams for postmortem reports
4. Compute causal attribution scores for contributing factors
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import json


class NodeType(Enum):
    """Types of nodes in the causal graph."""

    TRIGGER = "trigger"         # Initial event that started the chain
    PROPAGATION = "propagation" # Intermediate event that spread the issue
    HARM = "harm"               # Terminal event where harm occurred
    SAFEGUARD = "safeguard"     # Safeguard that was bypassed or failed
    CONTEXT = "context"         # Contextual factor that enabled the chain


class EdgeType(Enum):
    """Types of edges in the causal graph."""

    CAUSES = "causes"           # Direct causal relationship
    ENABLES = "enables"         # Necessary but not sufficient condition
    AMPLIFIES = "amplifies"     # Makes effect stronger
    BYPASSES = "bypasses"       # Circumvents a safeguard


@dataclass
class CausalNode:
    """A node in the causal dependency graph."""

    node_id: str
    label: str
    node_type: NodeType
    turn: Optional[int] = None  # Which conversation turn, if applicable

    # Analysis metadata
    severity: str = "medium"    # low, medium, high, critical
    confidence: float = 0.8    # How confident we are in this attribution
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "node_type": self.node_type.value,
            "turn": self.turn,
            "severity": self.severity,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }


@dataclass
class CausalEdge:
    """An edge in the causal dependency graph."""

    source_id: str
    target_id: str
    edge_type: EdgeType

    # Edge metadata
    strength: float = 1.0       # How strong the causal relationship is
    counterfactual: str = ""    # "If X hadn't happened, Y wouldn't have"

    def to_dict(self) -> dict:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.edge_type.value,
            "strength": self.strength,
            "counterfactual": self.counterfactual,
        }


@dataclass
class CausalGraph:
    """
    A causal dependency graph for incident analysis.

    Represents the chain of events from trigger through propagation to harm,
    including safeguards that failed or were bypassed.
    """

    incident_id: str
    nodes: dict[str, CausalNode] = field(default_factory=dict)
    edges: list[CausalEdge] = field(default_factory=list)

    # Graph metadata
    primary_cause: Optional[str] = None
    contributing_factors: list[str] = field(default_factory=list)

    def add_node(self, node: CausalNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.node_id] = node

    def add_edge(self, edge: CausalEdge) -> None:
        """Add an edge to the graph."""
        if edge.source_id not in self.nodes:
            raise ValueError(f"Source node {edge.source_id} not found")
        if edge.target_id not in self.nodes:
            raise ValueError(f"Target node {edge.target_id} not found")
        self.edges.append(edge)

    def get_causal_chain(self) -> list[CausalNode]:
        """
        Extract the main causal chain from trigger to harm.

        Returns nodes in order: trigger → propagation* → harm
        """
        chain = []

        # Find trigger nodes
        triggers = [n for n in self.nodes.values() if n.node_type == NodeType.TRIGGER]
        if not triggers:
            return chain

        # BFS from trigger to harm
        visited = set()
        queue = [triggers[0]]

        while queue:
            node = queue.pop(0)
            if node.node_id in visited:
                continue
            visited.add(node.node_id)
            chain.append(node)

            # Find connected nodes
            for edge in self.edges:
                if edge.source_id == node.node_id:
                    if edge.target_id not in visited:
                        queue.append(self.nodes[edge.target_id])

        return chain

    def get_bypassed_safeguards(self) -> list[CausalNode]:
        """Get all safeguards that were bypassed in this incident."""
        bypassed = []
        for edge in self.edges:
            if edge.edge_type == EdgeType.BYPASSES:
                if edge.target_id in self.nodes:
                    bypassed.append(self.nodes[edge.target_id])
        return bypassed

    def compute_attribution_scores(self) -> dict[str, float]:
        """
        Compute causal attribution scores for each node.

        Higher scores indicate nodes that contributed more to the harm.
        """
        scores = {}

        # Base score from node type
        type_weights = {
            NodeType.TRIGGER: 1.0,
            NodeType.PROPAGATION: 0.7,
            NodeType.HARM: 0.0,  # Harm is outcome, not cause
            NodeType.SAFEGUARD: 0.8,  # Failed safeguards are major causes
            NodeType.CONTEXT: 0.3,
        }

        for node_id, node in self.nodes.items():
            base = type_weights.get(node.node_type, 0.5)

            # Adjust by confidence
            base *= node.confidence

            # Adjust by edge strength (how many things this node caused)
            outgoing = [e for e in self.edges if e.source_id == node_id]
            if outgoing:
                avg_strength = sum(e.strength for e in outgoing) / len(outgoing)
                base *= avg_strength

            scores[node_id] = round(base, 3)

        return scores

    def to_mermaid(self) -> str:
        """
        Generate a Mermaid diagram of the causal graph.

        Suitable for embedding in postmortem markdown files.
        """
        lines = ["flowchart TB"]

        # Node type styling
        type_styles = {
            NodeType.TRIGGER: ":::trigger",
            NodeType.PROPAGATION: ":::propagation",
            NodeType.HARM: ":::harm",
            NodeType.SAFEGUARD: ":::safeguard",
            NodeType.CONTEXT: ":::context",
        }

        # Add nodes
        for node_id, node in self.nodes.items():
            style = type_styles.get(node.node_type, "")
            turn_label = f" [T{node.turn}]" if node.turn else ""
            lines.append(f'    {node_id}["{node.label}{turn_label}"]{style}')

        # Add edges
        edge_arrows = {
            EdgeType.CAUSES: "-->",
            EdgeType.ENABLES: "-.->",
            EdgeType.AMPLIFIES: "==>",
            EdgeType.BYPASSES: "--x",
        }

        for edge in self.edges:
            arrow = edge_arrows.get(edge.edge_type, "-->")
            lines.append(f"    {edge.source_id} {arrow} {edge.target_id}")

        # Add style definitions
        lines.extend([
            "",
            "    classDef trigger fill:#ff6b6b,stroke:#c92a2a",
            "    classDef propagation fill:#ffd43b,stroke:#fab005",
            "    classDef harm fill:#e64980,stroke:#a61e4d",
            "    classDef safeguard fill:#69db7c,stroke:#2f9e44",
            "    classDef context fill:#74c0fc,stroke:#1971c2",
        ])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize graph to dictionary."""
        return {
            "incident_id": self.incident_id,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "primary_cause": self.primary_cause,
            "contributing_factors": self.contributing_factors,
        }


def build_causal_graph_from_incident(incident: dict) -> CausalGraph:
    """
    Build a causal graph from an incident JSON file.

    Analyzes the conversation trajectory to identify:
    - Trigger: First action that initiated the attack
    - Propagation: Intermediate steps that advanced the attack
    - Harm: Final point where harm occurred
    - Safeguards: Which safeguards failed or were bypassed
    """
    incident_id = incident.get("incident_id", "UNKNOWN")
    graph = CausalGraph(incident_id=incident_id)

    trajectory = incident.get("trajectory", [])
    root_cause = incident.get("root_cause", {})

    # Track which turns are part of the attack
    attack_turns = []
    for i, turn in enumerate(trajectory):
        if turn.get("status") == "UNSAFE" or turn.get("verdict") == "VIOLATION":
            attack_turns.append(i)

    if not attack_turns:
        # No unsafe turns found, create minimal graph
        graph.add_node(CausalNode(
            node_id="no_harm",
            label="No harm detected",
            node_type=NodeType.CONTEXT,
        ))
        return graph

    # Create trigger node (first unsafe turn or context that enabled it)
    first_attack = attack_turns[0]
    if first_attack > 0:
        # There was context building before the attack
        graph.add_node(CausalNode(
            node_id="context_building",
            label="Context building (benign pretext)",
            node_type=NodeType.CONTEXT,
            turn=0,
            evidence=[f"Turns 0-{first_attack-1} established trust"],
        ))

    graph.add_node(CausalNode(
        node_id="trigger",
        label=root_cause.get("primary", "Initial attack"),
        node_type=NodeType.TRIGGER,
        turn=first_attack,
        severity="high",
        evidence=[root_cause.get("primary", "")],
    ))

    # Create propagation nodes for intermediate attack turns
    for i, turn_idx in enumerate(attack_turns[1:-1], start=1):
        graph.add_node(CausalNode(
            node_id=f"prop_{i}",
            label=f"Attack progression (turn {turn_idx})",
            node_type=NodeType.PROPAGATION,
            turn=turn_idx,
            severity="medium",
        ))

    # Create harm node (last unsafe turn)
    last_attack = attack_turns[-1]
    graph.add_node(CausalNode(
        node_id="harm",
        label="Harm materialized",
        node_type=NodeType.HARM,
        turn=last_attack,
        severity="critical",
    ))

    # Create safeguard failure node
    safeguard_gap = root_cause.get("secondary", "Unknown safeguard gap")
    graph.add_node(CausalNode(
        node_id="safeguard_failure",
        label=f"Safeguard gap: {safeguard_gap[:50]}",
        node_type=NodeType.SAFEGUARD,
        severity="high",
        evidence=[safeguard_gap],
    ))

    # Connect nodes
    if "context_building" in graph.nodes:
        graph.add_edge(CausalEdge(
            source_id="context_building",
            target_id="trigger",
            edge_type=EdgeType.ENABLES,
            counterfactual="Without context building, trigger might have been detected",
        ))

    # Connect trigger to propagation to harm
    prev_id = "trigger"
    for i in range(1, len(attack_turns) - 1):
        curr_id = f"prop_{i}"
        graph.add_edge(CausalEdge(
            source_id=prev_id,
            target_id=curr_id,
            edge_type=EdgeType.CAUSES,
        ))
        prev_id = curr_id

    # Connect last propagation (or trigger) to harm
    graph.add_edge(CausalEdge(
        source_id=prev_id,
        target_id="harm",
        edge_type=EdgeType.CAUSES,
    ))

    # Connect trigger to safeguard bypass
    graph.add_edge(CausalEdge(
        source_id="trigger",
        target_id="safeguard_failure",
        edge_type=EdgeType.BYPASSES,
        counterfactual="If safeguard had detected, attack would have stopped",
    ))

    # Set primary cause
    graph.primary_cause = "trigger"
    graph.contributing_factors = ["safeguard_failure"]
    if "context_building" in graph.nodes:
        graph.contributing_factors.append("context_building")

    return graph


def generate_postmortem_graph(incident_path: str, output_path: str) -> None:
    """
    Generate a causal graph analysis for an incident.

    Writes:
    - JSON graph representation
    - Mermaid diagram for markdown embedding
    - Attribution scores
    """
    with open(incident_path, "r") as f:
        incident = json.load(f)

    graph = build_causal_graph_from_incident(incident)

    # Compute attribution
    scores = graph.compute_attribution_scores()

    # Generate Mermaid diagram
    mermaid = graph.to_mermaid()

    # Build output
    output = {
        "incident_id": graph.incident_id,
        "causal_graph": graph.to_dict(),
        "attribution_scores": scores,
        "primary_cause": graph.primary_cause,
        "contributing_factors": graph.contributing_factors,
        "mermaid_diagram": mermaid,
        "bypassed_safeguards": [
            n.to_dict() for n in graph.get_bypassed_safeguards()
        ],
        "causal_chain_length": len(graph.get_causal_chain()),
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Causal graph generated: {output_path}")
    print(f"Primary cause: {graph.primary_cause}")
    print(f"Contributing factors: {graph.contributing_factors}")
    print(f"\nMermaid diagram:\n{mermaid}")


# Example usage
if __name__ == "__main__":
    # Example incident for demonstration
    example_incident = {
        "incident_id": "INC_004",
        "trajectory": [
            {"turn": 0, "status": "SAFE", "action": "context"},
            {"turn": 1, "status": "SAFE", "action": "write_port_scanner"},
            {"turn": 2, "status": "SAFE", "action": "write_service_identifier"},
            {"turn": 3, "status": "UNSAFE", "action": "combine_tools"},
            {"turn": 4, "status": "UNSAFE", "action": "run_scanner"},
        ],
        "root_cause": {
            "primary": "Single-turn intent analysis",
            "secondary": "No trajectory-level aggregation",
            "contributing": "Each subtask individually benign",
        },
    }

    graph = build_causal_graph_from_incident(example_incident)

    print("=" * 60)
    print(f"CAUSAL GRAPH: {graph.incident_id}")
    print("=" * 60)

    print("\nNodes:")
    for node_id, node in graph.nodes.items():
        print(f"  [{node.node_type.value}] {node_id}: {node.label}")

    print("\nEdges:")
    for edge in graph.edges:
        print(f"  {edge.source_id} --{edge.edge_type.value}--> {edge.target_id}")

    print("\nAttribution Scores:")
    scores = graph.compute_attribution_scores()
    for node_id, score in sorted(scores.items(), key=lambda x: -x[1]):
        print(f"  {node_id}: {score}")

    print("\nMermaid Diagram:")
    print(graph.to_mermaid())
