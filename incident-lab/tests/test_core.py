"""Tests for the causal graph used in incident root-cause analysis."""
import pytest

from analysis.causal_graph import (
    CausalEdge,
    CausalGraph,
    CausalNode,
    EdgeType,
    NodeType,
)


def test_causal_graph_build():
    g = CausalGraph(incident_id="inc-1")
    g.add_node(CausalNode(node_id="n1", label="prompt injection", node_type=NodeType.TRIGGER))
    g.add_node(CausalNode(node_id="n2", label="data exfiltration", node_type=NodeType.HARM))
    g.add_edge(CausalEdge(source_id="n1", target_id="n2", edge_type=EdgeType.CAUSES))
    assert len(g.nodes) == 2
    assert len(g.edges) == 1
    assert isinstance(g.get_causal_chain(), list)


def test_add_edge_rejects_unknown_node():
    g = CausalGraph(incident_id="inc-1")
    g.add_node(CausalNode(node_id="n1", label="x", node_type=NodeType.TRIGGER))
    with pytest.raises(ValueError):
        g.add_edge(CausalEdge(source_id="n1", target_id="missing", edge_type=EdgeType.CAUSES))
