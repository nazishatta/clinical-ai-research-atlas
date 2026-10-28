import pandas as pd
from src.author_topics import (MUTED_FILL, author_topic_profiles, authors_in_topic, hover_text, node_colour)
from src.evidence import reading_table

NAMES = {0: 'T1 · a', 1: 'T2 · b'}


def works():
    A, B, C = {'id': 'A', 'name': 'Ann'}, {'id': 'B', 'name': 'Bo'}, {'id': 'C', 'name': 'Cy'}
    return pd.DataFrame([
        {'id': 'w1', 'title': 't1', 'year': 2020, 'topic': 0, 'text_eligible': True, 'abstract': 'x', 'authors': [A, B]},
        {'id': 'w2', 'title': 't2', 'year': 2021, 'topic': 0, 'text_eligible': True, 'abstract': 'y', 'authors': [A]},
        {'id': 'w3', 'title': 't3', 'year': 2022, 'topic': 1, 'text_eligible': True, 'abstract': 'z', 'authors': [A, B]},
        {'id': 'w4', 'title': 't4', 'year': 2022, 'topic': -1, 'text_eligible': False, 'abstract': '', 'authors': [B, C, C]},
    ])


def profiles():
    return author_topic_profiles(works(), NAMES).set_index('Author ID')


def test_topic_counts_reconcile_with_author_papers():
    p = profiles()
    assert (p['Selected papers'].to_dict()) == {'A': 3, 'B': 3, 'C': 1}
    assert (p[list(NAMES.values())].sum(axis=1) == p['Topic-assigned papers']).all()


def test_missing_abstracts_are_excluded_from_topic_denominator():
    p = profiles()
    assert p.loc['B', 'Selected papers'] == 3 and p.loc['B', 'Topic-assigned papers'] == 2
    assert p.loc['C', 'Topic-assigned papers'] == 0


def test_dominance_rule_threshold_and_minimum_papers():
    p = profiles()
    assert p.loc['A', 'Classification'] == 'Dominant' and p.loc['A', 'Dominant topic'] == 'T1 · a'   # 2/3 > 50%
    assert p.loc['B', 'Classification'] == 'Mixed'                    # exactly 1/2 = 50% is not dominant
    assert p.loc['C', 'Classification'] == 'Insufficient evidence'    # 0 topic-assigned papers
    single = author_topic_profiles(works().iloc[[1]], NAMES).set_index('Author ID')
    assert single.loc['A', 'Classification'] == 'Insufficient evidence'  # 1/1 = 100% is not enough


def test_topic_selection_highlights_the_right_authors():
    p = author_topic_profiles(works(), NAMES)
    assert authors_in_topic(p, 'T2 · b') == {'A', 'B'}
    assert authors_in_topic(p, 'T1 · a') == {'A', 'B'}
    assert authors_in_topic(p, 'unknown') == set()


def test_node_colour_keeps_community_border_and_mutes_others():
    assert node_colour('#123456', None, 'A', '#E69F00') == '#123456'
    on = node_colour('#123456', {'A': True}, 'A', '#E69F00')
    off = node_colour('#123456', {'A': True}, 'B', '#E69F00')
    assert on['background'] == '#E69F00' and on['border'] == '#123456'
    assert off['background'] == MUTED_FILL and off['border'] == '#123456'


def test_hover_text_and_reading_table():
    hover = hover_text(author_topic_profiles(works(), NAMES))
    assert hover['A'] == 'Topics: T1 2 · T2 1 (mostly T1)' and hover['B'].endswith('(mixed)')
    table = reading_table(works(), NAMES)
    assert table.Source.tolist()[0] in {'w3', 'w4'} and table.Year.is_monotonic_decreasing
    assert table.set_index('Source').loc['w4', 'Abstract excerpt'] == '(no usable abstract)'
