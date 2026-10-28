"""Filter-reset callbacks.

"Reset all filters" returns every analytical selection to its default: the corpus
filters, the evidence filters, chart selections, the selected paper, the network
focus author, the author pair and the community choice. Display preferences
(network size caps, layout, label visibility, edge threshold, ranking measure)
are kept, because they change how results are drawn, not which records are used.

Streamlit widgets must be reset by assigning their default values. Deleting a
widget key from ``st.session_state`` updates the server but, in a real browser,
the widget keeps showing the old value and sends it back on the next
interaction, silently re-applying a filter the reader thought was cleared.
"""
from __future__ import annotations
from collections.abc import MutableMapping

CHART_PICKS = ('chart_pick_year', 'chart_pick_topic', 'chart_pick_term')
ALL_TOPICS = 'All topics'
NO_AUTHOR = 'None'
ALL_AUTHORS = 'All authors'
NO_COMMUNITY = 'Choose a community'

# Selection widgets and their default values (None = nothing selected).
SELECTION_DEFAULTS = {
    'author_focus': NO_AUTHOR,   # Inspect author papers
    'pair_author': NO_AUTHOR,    # Inspect shared papers with another author
    'focus': ALL_AUTHORS,        # Focus author and direct collaborators (network)
    'community_choice': NO_COMMUNITY,
    'paper': None,               # Read a selected paper
    'highlight_topic': 'No highlight',  # Topic highlighted on the networks
}


def clear_chart_selections(state: MutableMapping) -> None:
    state['evidence_years'] = []
    state['evidence_topics'] = []
    state['evidence_term'] = ''
    for key in CHART_PICKS:
        state.pop(key, None)


def reset_filters(state: MutableMapping, start_year: int, end_year: int) -> None:
    state['years'] = (start_year, end_year)
    state['signals'] = []
    state['topic'] = ALL_TOPICS
    for key, default in SELECTION_DEFAULTS.items():
        state[key] = default
    clear_chart_selections(state)
