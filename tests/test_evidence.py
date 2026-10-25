import pandas as pd
from src.evidence import apply_evidence_filters, papers_for_author, papers_for_pair, population_counts, export_columns


def example():
    return pd.DataFrame([
        dict(id='1',year=2024,topic=0,title='Clinical calibration',abstract='Calibration calibration model',text_eligible=True,authors=[{'id':'a'},{'id':'b'}]),
        dict(id='2',year=2025,topic=1,title='Prediction',abstract='Clinical explainability',text_eligible=True,authors=[{'id':'b'},{'id':'c'}]),
        dict(id='3',year=2025,topic=0,title='Clinical calibration',abstract='',text_eligible=False,authors=[]),
    ])


def test_year_topic_term_and():
    df=example()
    assert apply_evidence_filters(df, years=[2025],topics=[0]).id.tolist()==['3']
    assert apply_evidence_filters(df,term='calibration').id.tolist()==['1','3']
    assert apply_evidence_filters(df,years=[2024,2025],topics=[0,1],term='clinical').shape[0]==3
    assert apply_evidence_filters(df,term='unfound').empty


def test_author_pairs_and_population():
    df=example()
    assert papers_for_author(df,'b').id.tolist()==['1','2']
    assert papers_for_pair(df,'a','b').id.tolist()==['1']
    assert papers_for_pair(df,'a','c').empty
    assert papers_for_pair(df,'a','a').empty
    assert population_counts(df)==dict(selected_works=3,text_eligible=2,network_eligible=2,unique_authors=3)
    assert export_columns(df).id.tolist()==['2','3','1']
