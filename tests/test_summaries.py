import pandas as pd
from src import summaries


def test_annual_and_empty():
    counts = pd.DataFrame({'Year': [2020, 2021, 2022], 'Works': [5, 20, 12]})
    text = summaries.annual_works(counts)
    assert '5 in 2020' in text and '12 in 2022' in text and '2021 with 20' in text
    assert 'No works' in summaries.annual_works(pd.DataFrame({'Year': [2020], 'Works': [0]}))


def test_signal_shares_ignores_missing_denominators():
    shares = pd.DataFrame({'Year': [2019, 2020, 2020], 'Signal': ['Calibration', 'Calibration', 'Uncertainty'],
                           'Works': [0, 3, 5], 'Denominator': [0, 10, 10], 'Share (%)': [float('nan'), 30.0, 50.0]})
    assert summaries.signal_shares(shares) == 'In 2020, the most frequent trustworthiness signal is Uncertainty (50% of 10 works).'


def test_topic_shares_names_biggest_rise_and_fall():
    shares = pd.DataFrame({'Period': ['2020', '2020', '2025', '2025'], 'Topic': ['A', 'B', 'A', 'B'],
                           'Share (%)': [80.0, 20.0, 30.0, 70.0]})
    text = summaries.topic_shares(shares)
    assert 'B grows the most (20% to 70%' in text and 'A shrinks the most (80% to 30%)' in text


def test_terms_topics_communities_ranking():
    assert '"ai" (9 documents)' in summaries.document_terms(pd.DataFrame({'Term': ['ai', 'ml'], 'Documents': [9, 4]}))
    assert 'largest is T2 with 6 works (60%)' in summaries.topic_distribution(pd.DataFrame({'Topic': ['T1', 'T2'], 'Works': [4, 6]}))
    assert 'Community 2' in summaries.communities(pd.DataFrame({'Community': ['Community 1', 'Community 2'], 'Researchers': [3, 9]}))
    top = pd.DataFrame({'Author': ['Ada'], 'Collaborators': [12]})
    assert summaries.ranking(top, 'Collaborators') == 'Ada ranks first by collaborators (12) among the top 1 authors shown.'
