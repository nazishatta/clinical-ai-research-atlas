import json
from pathlib import Path
import networkx as nx
import numpy as np
import pandas as pd
from src.analysis import reconstruct_abstract, filter_works, annual_counts, signal_shares, build_graph, term_frequencies

def fixture():
 return pd.DataFrame([
  {'id':'w1','year':2020,'signals':['Calibration'],'topic':0,'text_eligible':True,'authors':[{'id':'a','name':'A'},{'id':'b','name':'B'},{'id':'c','name':'C'}]},
  {'id':'w2','year':2021,'signals':['Uncertainty'],'topic':1,'text_eligible':True,'authors':[{'id':'a','name':'A'},{'id':'b','name':'B'}]},
  {'id':'w3','year':2021,'signals':['Calibration'],'topic':-1,'text_eligible':False,'authors':[{'id':'d','name':'D'}]},
 ])

def test_abstract_position_reconstruction():
 assert reconstruct_abstract({'world':[1],'hello':[0,2]})=='hello world hello'
 assert reconstruct_abstract(None)==''

def test_shared_filters_or_and_topic():
 df=fixture()
 assert filter_works(df,(2020,2021),['Calibration','Uncertainty']).id.tolist()==['w1','w2','w3']
 assert filter_works(df,(2021,2021),['Calibration']).id.tolist()==['w3']
 assert filter_works(df,(2020,2021),[],1).id.tolist()==['w2']
 assert filter_works(df,(2016,2018),[]).empty

def test_zero_years_and_text_denominator():
 df=fixture();counts=annual_counts(df,2019,2021)
 assert counts.Works.tolist()==[0,1,2]
 shares=signal_shares(df,2019,2021)
 assert shares[(shares.Year==2021)&(shares.Signal=='Calibration')]['Share (%)'].iloc[0]==0
 assert np.isnan(shares[shares.Year==2019]['Share (%)'].iloc[0])

def test_network_unique_authors_weights_and_threshold():
 df=fixture();g=build_graph(df)
 assert g.number_of_edges()==3
 assert g['a']['b']['shared']==2
 assert g['a']['b']['strength']==1.5
 assert g['a']['c']['strength']==.5
 assert set(nx.isolates(g))=={'d'}
 assert not list(nx.selfloop_edges(g))
 assert build_graph(df,2).number_of_edges()==1
 # Duplicate authors in a paper must not create a self-loop or double-count.
 df.at[0,'authors']=df.at[0,'authors']+[{'id':'a','name':'A'}]
 assert build_graph(df)['a']['b']['shared']==2

def test_document_frequency_not_token_count():
 f=term_frequencies(['calibration calibration improves prediction','calibration improves models'],100).set_index('Term')
 assert f.loc['calibration','Documents']==2
 assert term_frequencies([]).empty

def test_frozen_corpus_contract_and_hashes():
 import hashlib
 p=Path(__file__).resolve().parents[1]/'data/processed'
 works=pd.read_json(p/'works.jsonl',lines=True)
 manifest=json.loads((p/'retrieval_manifest.json').read_text())
 assert manifest['retrieval_complete']
 assert works.id.is_unique
 assert works.year.between(2016,2025).all()
 assert works[works.text_eligible].abstract.str.split().str.len().ge(30).all()
 for name,expected in json.loads((p/'checksums.json').read_text()).items():
  assert hashlib.sha256((p/name).read_bytes()).hexdigest()==expected
