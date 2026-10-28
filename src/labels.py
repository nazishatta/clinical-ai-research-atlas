"""Which author names a network draws by default.

Drawing every name on a 350-author network makes it unreadable. By default only
the most-connected authors are labelled; every other name stays available on
hover, in the author selectors and in the tables, and "Show all names" draws all.
"""
from __future__ import annotations
import networkx as nx

DEFAULT_TOP_LABELS = 12
# PyVis replaces an empty label with the node id (a raw OpenAlex URL), so a hidden
# name must be a single space, not an empty string.
HIDDEN_LABEL = ' '


def top_label_nodes(graph: nx.Graph, n: int = DEFAULT_TOP_LABELS) -> set:
    """The ``n`` authors with the most collaborators; ties broken by node id."""
    ranked = sorted(graph.nodes, key=lambda node: (-graph.degree(node), str(node)))
    return set(ranked[:max(0, n)])
