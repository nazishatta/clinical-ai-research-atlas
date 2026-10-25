"""Pure analysis functions shared by preprocessing, application, and tests."""
from __future__ import annotations
from itertools import combinations
import re
import networkx as nx
import numpy as np
import pandas as pd

SIGNALS = {
    'Calibration': r'\bcalibrat(?:ion|ed|ing|e|or|ors)\b',
    'Explainability': r'\b(?:explainab\w*|interpretab\w*|shap|lime)\b',
    'Uncertainty': r'\b(?:uncertain\w*|conformal|out.of.distribution)\b',
    'Validation & reliability': r'\b(?:external validation|reliab\w*|robust\w*|generaliz\w*|generalis\w*)\b',
}

def reconstruct_abstract(index: dict | None) -> str:
    if not index:
        return ''
    positions = [(int(p), word) for word, values in index.items() for p in values]
    return ' '.join(word for _, word in sorted(positions))

def signals(text: str) -> list[str]:
    return [name for name, pattern in SIGNALS.items() if re.search(pattern, text, re.I)]

def filter_works(df: pd.DataFrame, years: tuple[int, int], selected_signals: list[str], topic: int | None = None) -> pd.DataFrame:
    out = df[df.year.between(*years)]
    if selected_signals:
        out = out[out.signals.map(lambda values: bool(set(values) & set(selected_signals)))]
    if topic is not None:
        out = out[out.topic == topic]
    return out.copy()

def annual_counts(df: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    return df.groupby('year').size().reindex(range(start,end+1),fill_value=0).rename_axis('Year').reset_index(name='Works')

def signal_shares(df: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    rows = []
    # Denominator uses only records with reconstructable abstract text.
    text_df = df[df.text_eligible]
    for year in range(start,end+1):
        group = text_df[text_df.year == year]
        for name in SIGNALS:
            count = sum(name in values for values in group.signals)
            rows.append({'Year':year,'Signal':name,'Works':count,'Denominator':len(group),
                         'Share (%)':100*count/len(group) if len(group) else np.nan})
    return pd.DataFrame(rows)

def term_frequencies(texts: list[str], top_n: int = 20) -> pd.DataFrame:
    from sklearn.feature_extraction.text import CountVectorizer
    if not texts:
        return pd.DataFrame(columns=['Term','Documents'])
    vectorizer = CountVectorizer(stop_words='english', binary=True, ngram_range=(1,2), min_df=1, max_features=12000)
    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError:
        return pd.DataFrame(columns=['Term','Documents'])
    counts = np.asarray(matrix.sum(axis=0)).ravel()
    return pd.DataFrame({'Term':vectorizer.get_feature_names_out(),'Documents':counts}).sort_values(['Documents','Term'],ascending=[False,True]).head(top_n)

def build_graph(df: pd.DataFrame, min_shared: int = 1) -> nx.Graph:
    graph = nx.Graph()
    for row in df.itertuples():
        authors = {a['id']:a['name'] for a in row.authors if a.get('id')}
        for author_id,name in authors.items():
            if author_id not in graph:
                graph.add_node(author_id, name=name, papers=0)
            graph.nodes[author_id]['papers'] += 1
        # Team-normalized strength: each author's total strength per paper is 1.
        increment = 1/(len(authors)-1) if len(authors)>1 else 0
        for a,b in combinations(sorted(authors),2):
            if graph.has_edge(a,b):
                graph[a][b]['shared'] += 1
                graph[a][b]['strength'] += increment
            else:
                graph.add_edge(a,b,shared=1,strength=increment)
    if min_shared > 1:
        graph.remove_edges_from([(a,b) for a,b,d in graph.edges(data=True) if d['shared'] < min_shared])
    return graph

def graph_ranking(graph: nx.Graph) -> pd.DataFrame:
    rows = [{'Author ID':n,'Author':d['name'],'Collaborators':graph.degree(n),
             'Team-normalized strength':graph.degree(n,weight='strength'),'Corpus papers':d.get('papers',0)} for n,d in graph.nodes(data=True)]
    if not rows:
        return pd.DataFrame(columns=['Author ID','Author','Collaborators','Team-normalized strength','Corpus papers'])
    return pd.DataFrame(rows).sort_values(['Collaborators','Author ID'],ascending=[False,True])
