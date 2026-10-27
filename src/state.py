"""Filter-reset callbacks.

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
    state['author_focus'] = NO_AUTHOR
    clear_chart_selections(state)
