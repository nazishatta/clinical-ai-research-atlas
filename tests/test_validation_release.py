import pandas as pd
import pytest
from scripts.validate_release import relevance_summary


def test_stratified_weighting_not_naive_average():
    works = pd.DataFrame({'id':['a','b','c','d','e','f'], 'year':[2024,2024,2024,2024,2025,2025]})
    sample = pd.DataFrame({'id':['a','e'], 'year':[2024,2025], 'decision':['INCLUDE','EXCLUDE']})
    _, result = relevance_summary(works,sample)
    assert result['all_strata_complete'] is True
    assert result['year_weighted_precision'] == pytest.approx(4/6)


def test_incomplete_reviews_do_not_generate_precision():
    works = pd.DataFrame({'id':['a','b'], 'year':[2024,2024]})
    sample = pd.DataFrame({'id':['a'], 'year':[2024], 'decision':['']})
    _, result = relevance_summary(works,sample)
    assert result['year_weighted_precision'] is None


def test_uncertain_review_blocks_signoff():
    works = pd.DataFrame({'id':['a'], 'year':[2024]})
    sample = pd.DataFrame({'id':['a'], 'year':[2024], 'decision':['UNCERTAIN']})
    _, result = relevance_summary(works,sample)
    assert not result['all_strata_complete']
