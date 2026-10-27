"""Regression tests for the reset defect seen in a real browser.

Before the fix, Reset deleted widget keys. The headline count reset, but the
topic box kept showing the old topic and re-applied it on the next interaction.
The callbacks must assign defaults so the browser widgets are updated too.
"""
from src.state import ALL_TOPICS, NO_AUTHOR, clear_chart_selections, reset_filters


def dirty_state():
    return {
        'years': (2020, 2023), 'signals': ['Calibration'], 'topic': 'T1 · care / health / patients',
        'author_focus': 'https://openalex.org/A1', 'evidence_years': [2024], 'evidence_topics': [1],
        'evidence_term': 'calibration', 'chart_pick_year': [2024], 'chart_pick_topic': [1],
        'chart_pick_term': 'calibration', 'shared': 5,
    }


def test_reset_assigns_defaults_instead_of_deleting_widget_keys():
    state = dirty_state()
    reset_filters(state, 2016, 2025)
    assert state['years'] == (2016, 2025)
    assert state['signals'] == []
    assert state['topic'] == ALL_TOPICS
    assert state['author_focus'] == NO_AUTHOR
    assert state['evidence_years'] == [] and state['evidence_topics'] == [] and state['evidence_term'] == ''
    assert not {'chart_pick_year', 'chart_pick_topic', 'chart_pick_term'} & set(state)


def test_reset_leaves_network_display_settings_alone():
    state = dirty_state()
    reset_filters(state, 2016, 2025)
    assert state['shared'] == 5


def test_clear_chart_selections_keeps_sidebar_filters():
    state = dirty_state()
    clear_chart_selections(state)
    assert state['topic'] == 'T1 · care / health / patients'
    assert state['years'] == (2020, 2023)
    assert state['evidence_years'] == [] and state['evidence_term'] == ''
    assert 'chart_pick_term' not in state
