"""Community-island moving visualization, based on the selected NetworkX subgraph.

This is a view only. It does not alter graph statistics or clustering.
"""
from __future__ import annotations

from html import escape
import math

import networkx as nx
from pyvis.network import Network

from src.labels import HIDDEN_LABEL, top_label_nodes


def build_clustered_network_html(graph: nx.Graph, communities: list, colors: list[str], show_labels: bool = False) -> str:
    """Show detected communities as separated islands with live draggable physics."""
    net = Network(height="760px", width="100%", bgcolor="#0B101A", font_color="#F2F6FC", cdn_resources="in_line")
    membership = {node: idx for idx, group in enumerate(communities) for node in group}
    labelled = set(graph.nodes) if show_labels else top_label_nodes(graph)
    count = max(1, len(communities))
    # Place connected researchers near their community center before the live solver starts.
    # Centers are a visualization aid, not measured dissimilarities.
    spread = 300.0 if count < 5 else 145.0 + 40.0 * math.sqrt(count)
    positions = {}
    for idx, members in enumerate(communities):
        angle = 2 * math.pi * idx / count
        cx = spread * math.cos(angle)
        cy = spread * math.sin(angle)
        local = graph.subgraph(members)
        if len(members) == 1:
            local_positions = {next(iter(members)): (0.0, 0.0)}
        else:
            local_positions = nx.spring_layout(local, seed=42 + idx, weight='strength', scale=min(105.0, 22.0 * math.sqrt(len(members))))
        for node, loc in local_positions.items():
            positions[node] = (cx + float(loc[0]), cy + float(loc[1]))

    for node, data in graph.nodes(data=True):
        degree = graph.degree(node)
        name = str(data.get('name', node))
        group_id = membership.get(node, 0)
        x, y = positions.get(node, (0.0, 0.0))
        net.add_node(
            str(node),
            label=name[:29] if node in labelled else HIDDEN_LABEL,
            title=f"{escape(name)} · Community {group_id+1} · {degree} displayed collaborators · {int(data.get('papers',0))} corpus papers",
            color=colors[group_id % len(colors)],
            size=min(37, 9 + 3.1 * math.sqrt(degree)),
            x=x, y=y, physics=True, borderWidth=1, borderWidthSelected=3,
        )
    for u, v, data in graph.edges(data=True):
        same_group = membership.get(u) == membership.get(v)
        shared = int(data.get('shared', 1))
        net.add_edge(
            str(u), str(v),
            title=f'{shared} shared paper(s)',
            width=min(3.2, 0.5 + 0.3 * shared),
            color='#8E9DBB' if same_group else '#495567',
            value=max(0.1, float(data.get('strength', 1.0))),
        )
    # Initial cluster islands are visible at once; physics then moves nodes.
    # Long springs and weak central gravity reduce overlap between communities.
    net.set_options("""{
      "interaction":{"hover":true,"tooltipDelay":100,"dragNodes":true,"dragView":true,"zoomView":true,"navigationButtons":true,"keyboard":true},
      "nodes":{"shape":"dot","font":{"color":"#F2F6FC","size":13,"strokeWidth":3,"strokeColor":"#0B101A"}},
      "edges":{"smooth":false},
      "physics":{"enabled":true,"solver":"forceAtlas2Based",
        "forceAtlas2Based":{"gravitationalConstant":-90,"centralGravity":0.002,"springLength":180,"springConstant":0.025,"damping":0.64,"avoidOverlap":0.8},
        "stabilization":{"enabled":false},"minVelocity":0.07}
    }""")
    return net.generate_html(notebook=False)
