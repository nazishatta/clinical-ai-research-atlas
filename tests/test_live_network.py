"""Checks for the accessible default state of the live network."""
import networkx as nx
import pytest
pytest.importorskip("pyvis")
from src.live_network import build_live_network_html


def sample_graph():
    graph=nx.Graph()
    graph.add_node('a', name='Alice Example', papers=2)
    graph.add_node('b', name='Bob Example', papers=3)
    graph.add_edge('a','b', shared=2, strength=1.0)
    return graph


def test_network_hides_labels_but_preserves_hover_data():
    html=build_live_network_html(sample_graph(),[{'a','b'}],'Force-directed',['#80C9BB'])
    assert 'Alice Example' in html
    assert 'selected-graph collaborators' in html
    assert '"label": ""' in html or '\"label\": \"\"' in html
    assert 'forceAtlas2Based' in html


def test_opt_in_labels_and_circular_positions():
    html=build_live_network_html(sample_graph(),[{'a','b'}],'Circular',['#80C9BB'],show_labels=True)
    assert '"label": "Alice Example"' in html
    assert '"physics": false' in html
