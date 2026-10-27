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


def period_buckets(year_counts: dict[int, int], start: int, end: int, min_works: int = 30) -> list[tuple[int, int]]:
    """Group consecutive years until each period has at least ``min_works`` works.

    Sparse early years are pooled instead of shown as unstable single-year shares.
    A short final period is merged into the previous one.
    """
    buckets: list[list[int]] = []
    current: list[int] = []
    total = 0
    for year in range(start, end + 1):
        current.append(year)
        total += year_counts.get(year, 0)
        if total >= min_works:
            buckets.append(current)
            current, total = [], 0
    if current:
        if buckets:
            buckets[-1].extend(current)
        else:
            buckets.append(current)
    return [(b[0], b[-1]) for b in buckets]


def topic_shares_by_period(df: pd.DataFrame, topic_names: dict[int, str], start: int, end: int,
                           min_works: int = 30) -> pd.DataFrame:
    """Share of text-eligible works per NMF topic in each period.

    Every text-eligible work has exactly one dominant topic, so shares in a period
    sum to 100%. Periods pool sparse years (see ``period_buckets``).
    """
    columns = ['Period', 'Start', 'End', 'Topic', 'Works', 'Denominator', 'Share (%)']
    text_df = df[df.text_eligible & df.topic.isin(list(topic_names))]
    if text_df.empty:
        return pd.DataFrame(columns=columns)
    counts = text_df.groupby('year').size().to_dict()
    rows = []
    for first, last in period_buckets(counts, start, end, min_works):
        group = text_df[text_df.year.between(first, last)]
        label = str(first) if first == last else f'{first}–{last}'
        for topic_id, name in topic_names.items():
            works = int((group.topic == topic_id).sum())
            rows.append({'Period': label, 'Start': first, 'End': last, 'Topic': name, 'Works': works,
                         'Denominator': len(group),
                         'Share (%)': 100 * works / len(group) if len(group) else np.nan})
    return pd.DataFrame(rows, columns=columns)


SMALL_DENOMINATOR = 30


def topic_shares_by_year(df: pd.DataFrame, topic_names: dict[int, str], start: int, end: int) -> pd.DataFrame:
    """Complete year x topic grid of shares, with explicit zeros.

    Every year in ``start``..``end`` appears for every topic. A year with no
    text-eligible works keeps its rows with Denominator 0 and a missing share.
    ``Small sample`` flags years whose denominator is below ``SMALL_DENOMINATOR``.
    """
    columns = ['Period', 'Start', 'End', 'Topic', 'Works', 'Denominator', 'Share (%)', 'Small sample']
    text_df = df[df.text_eligible & df.topic.isin(list(topic_names))]
    rows = []
    for year in range(start, end + 1):
        group = text_df[text_df.year == year]
        for topic_id, name in topic_names.items():
            works = int((group.topic == topic_id).sum())
            rows.append({'Period': str(year), 'Start': year, 'End': year, 'Topic': name, 'Works': works,
                         'Denominator': len(group),
                         'Share (%)': 100 * works / len(group) if len(group) else np.nan,
                         'Small sample': 0 < len(group) < SMALL_DENOMINATOR})
    return pd.DataFrame(rows, columns=columns)


def representative_papers(works: pd.DataFrame, topics: list[dict]) -> pd.DataFrame:
    """The papers the topic model lists as most representative of each topic."""
    lookup = works.set_index('id')
    rows = []
    for topic in topics:
        for rank, work_id in enumerate(topic.get('representative_ids', []), start=1):
            if work_id not in lookup.index:
                continue
            record = lookup.loc[work_id]
            rows.append({'Topic': topic['label'], 'Rank': rank, 'Title': record.title, 'Year': int(record.year),
                         'Top terms': ', '.join(topic.get('terms', [])[:8]), 'Source': work_id})
    return pd.DataFrame(rows, columns=['Topic', 'Rank', 'Title', 'Year', 'Top terms', 'Source'])
