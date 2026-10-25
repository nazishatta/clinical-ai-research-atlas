"""Interactive physics network for the selected, capped coauthorship graph.

This is visualization only; no changes to graph metrics or research corpus.
"""
from __future__ import annotations

from html import escape
import networkx as nx
from pyvis.network import Network


def build_live_network_html(
    graph: nx.Graph, communities: list, layout: str, colors: list[str], show_labels: bool = False
) -> str:
    """Produce self-contained, draggable vis.js network HTML for Streamlit.

    Force-directed layout runs live physics; circular layout has truly fixed positions.
    No network data is sent to an external CDN.
    """
    network = Network(height="620px", width="100%", bgcolor="#1B222C", font_color="#ECF3F9", cdn_resources="in_line", directed=False)
    groups = {author: idx for idx, group in enumerate(communities) for author in group}
    for author, data in graph.nodes(data=True):
        degree = graph.degree(author)
        name = str(data.get("name", author))
        # HTML escaped because metadata may originate from OpenAlex.
        title = f"{escape(name)} · {degree} selected-graph collaborators · {data.get('papers', 0)} selected papers"
        network.add_node(str(author), label=name[:34] if show_labels else "", title=title,
            size=11 + 2.0 * (degree ** 0.5),
            color=colors[groups.get(author,0) % len(colors)],
            borderWidth=1, borderWidthSelected=3)
    for u,v,d in graph.edges(data=True):
        weight=float(d.get('strength',1.0))
        count=int(d.get('shared',1))
        network.add_edge(str(u),str(v),title=f"{count} shared paper(s)",
            width=min(5.0, 0.7 + count * 0.55), color="#7D90A7", value=max(0.1,weight))
    if layout == "Circular":
        positions=nx.circular_layout(graph,scale=380)
        for node in network.nodes:
            x,y=positions[node["id"]]
            node["x"]=float(x)
            node["y"]=float(y)
            node["physics"]=False
        network.toggle_physics(False)
        network.set_options('''{"interaction":{"hover":true,"dragNodes":true,"zoomView":true,"navigationButtons":true},"physics":{"enabled":false},"edges":{"smooth":false},"nodes":{"font":{"color":"#E7EDF5"}}}''')
    else:
        # Disable pre-stabilization: visitors see nodes move rather than only the final drawing.
        network.set_options('''{"interaction":{"hover":true,"dragNodes":true,"zoomView":true,"navigationButtons":true},"physics":{"enabled":true,"solver":"forceAtlas2Based","forceAtlas2Based":{"gravitationalConstant":-65,"centralGravity":0.015,"springLength":130,"springConstant":0.045,"damping":0.55},"stabilization":{"enabled":false},"minVelocity":0.05},"edges":{"smooth":false},"nodes":{"font":{"color":"#E7EDF5"}}}''')
    return network.generate_html(notebook=False)
