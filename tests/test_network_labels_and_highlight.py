"""Network defaults: few names, physics kept."""
import json, re
import networkx as nx
import pytest
pytest.importorskip("pyvis")
from src.clustered_network import build_clustered_network_html
from src.dense_clusters import moving_community_html
from src.live_network import build_live_network_html
from src.labels import top_label_nodes


def star_graph(n=20):
    g = nx.Graph()
    for i in range(n):
        g.add_node(f'a{i:02}', name=f'Author {i:02}', papers=1)
    for i in range(1, n):
        g.add_edge('a00', f'a{i:02}', shared=1, strength=1.0)
    for i in range(1, 6):  # a01..a05 get extra links, so they rank above the rest
        for j in range(i + 1, 6):
            g.add_edge(f'a{i:02}', f'a{j:02}', shared=1, strength=1.0)
    return g


def node_labels(html):
    nodes = json.loads(re.search(r'nodes = new vis\.DataSet\((\[.*?\])\);', html, re.S).group(1))
    return {n['id']: n.get('label', '') for n in nodes}, nodes


def test_top_label_nodes_ranks_by_collaborators():
    g = star_graph()
    top = top_label_nodes(g, 6)
    assert top == {'a00', 'a01', 'a02', 'a03', 'a04', 'a05'}


@pytest.mark.parametrize('builder', ['clustered', 'live', 'dense'])
def test_labels_hidden_by_default_except_top_12_and_all_on_request(builder):
    g = star_graph(20)
    comms = [set(g.nodes)]
    make = {
        'clustered': lambda show: build_clustered_network_html(g, comms, ['#56B4E9'], show_labels=show),
        'live': lambda show: build_live_network_html(g, comms, 'Force-directed', ['#56B4E9'], show_labels=show),
        'dense': lambda show: moving_community_html(g, show)[0],
    }[builder]
    labels, _ = node_labels(make(False))
    assert sum(bool(v.strip()) for v in labels.values()) == 12
    # Hidden names must be blank, never the raw OpenAlex id that PyVis substitutes for ''.
    assert not any(v.startswith('a') and v == k for k, v in labels.items())
    labels_all, _ = node_labels(make(True))
    assert all(v.strip() for v in labels_all.values())


def test_physics_stays_enabled_in_moving_modes():
    g = star_graph(10)
    assert 'forceAtlas2Based' in build_live_network_html(g, [set(g.nodes)], 'Force-directed', ['#56B4E9'])
    _, nodes = node_labels(moving_community_html(g)[0])
    assert all(n.get('physics') for n in nodes)
