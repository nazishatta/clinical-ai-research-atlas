"""Regression tests for the reset defect seen in a real browser.

Before the fix, Reset deleted widget keys. The headline count reset, but the
topic box kept showing the old topic and re-applied it on the next interaction.
The callbacks must assign defaults so the browser widgets are updated too.
The full browser check is tests/browser/reset_browser.cjs.
"""
from src.state import (ALL_AUTHORS, ALL_TOPICS, NO_AUTHOR, NO_COMMUNITY, SELECTION_DEFAULTS,
                       clear_chart_selections, reset_filters)

DISPLAY_SETTINGS = {'shared': 5, 'cap': 80, 'large_cluster_limit': 200, 'large_cluster_names': True,
                    'show_network_labels': True, 'rank_measure': 'Collaborators'}


def dirty_state():
    return {
        'years': (2020, 2023), 'signals': ['Calibration'], 'topic': 'T1 · care / health / patients',
        'author_focus': 'https://openalex.org/A1', 'pair_author': 'https://openalex.org/A2',
        'focus': 'https://openalex.org/A3', 'community_choice': 'Community 2', 'paper': 'https://openalex.org/W1', 'highlight_topic': 'T2 · patients / prediction / curve',
        'evidence_years': [2024], 'evidence_topics': [1], 'evidence_term': 'calibration',
        'chart_pick_year': [2024], 'chart_pick_topic': [1], 'chart_pick_term': 'calibration',
        **DISPLAY_SETTINGS,
    }


def test_reset_assigns_defaults_instead_of_deleting_widget_keys():
    state = dirty_state()
    reset_filters(state, 2016, 2025)
    assert state['years'] == (2016, 2025)
    assert state['signals'] == []
    assert state['topic'] == ALL_TOPICS
    assert state['evidence_years'] == [] and state['evidence_topics'] == [] and state['evidence_term'] == ''
    assert not {'chart_pick_year', 'chart_pick_topic', 'chart_pick_term'} & set(state)


def test_reset_clears_every_analytical_selection():
    state = dirty_state()
    reset_filters(state, 2016, 2025)
    assert state['author_focus'] == NO_AUTHOR
    assert state['pair_author'] == NO_AUTHOR
    assert state['focus'] == ALL_AUTHORS
    assert state['community_choice'] == NO_COMMUNITY
    assert state['paper'] is None
    assert state['highlight_topic'] == 'No highlight'
    assert set(SELECTION_DEFAULTS) == {'author_focus', 'pair_author', 'focus', 'community_choice', 'paper', 'highlight_topic'}


def test_reset_keeps_network_display_settings():
    state = dirty_state()
    reset_filters(state, 2016, 2025)
    assert {k: state[k] for k in DISPLAY_SETTINGS} == DISPLAY_SETTINGS


def test_clear_chart_selections_keeps_sidebar_filters():
    state = dirty_state()
    clear_chart_selections(state)
    assert state['topic'] == 'T1 · care / health / patients'
    assert state['years'] == (2020, 2023)
    assert state['evidence_years'] == [] and state['evidence_term'] == ''
    assert 'chart_pick_term' not in state
