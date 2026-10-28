"""Deterministic evidence selection and reconciliation helpers."""
from __future__ import annotations
from itertools import combinations
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer


def apply_evidence_filters(df: pd.DataFrame, years: list[int] | None = None,
                           topics: list[int] | None = None, term: str | None = None) -> pd.DataFrame:
    """OR within a category; AND between categories. Term uses sklearn tokenization."""
    out = df
    if years:
        out = out[out['year'].isin(years)]
    if topics:
        out = out[out['topic'].isin(topics)]
    if term:
        corpus = (out['title'].fillna('') + ' ' + out['abstract'].fillna('')).tolist()
        if corpus:
            vectorizer = CountVectorizer(vocabulary=[term], binary=True, ngram_range=(1, 2))
            matches = (vectorizer.transform(corpus).getnnz(axis=1) > 0)
            out = out.loc[matches]
    return out.copy()


def papers_for_author(df: pd.DataFrame, author_id: str) -> pd.DataFrame:
    return df[df['authors'].map(lambda people: any(p.get('id') == author_id for p in people))].copy()


def papers_for_pair(df: pd.DataFrame, author_a: str, author_b: str) -> pd.DataFrame:
    if author_a == author_b:
        return df.iloc[0:0].copy()
    return df[df['authors'].map(lambda people: {author_a, author_b}.issubset({p.get('id') for p in people}))].copy()


def population_counts(df: pd.DataFrame) -> dict[str, int]:
    return {
        'selected_works': len(df),
        'text_eligible': int(df['text_eligible'].sum()),
        'network_eligible': int(df['authors'].map(lambda a: any(p.get('id') for p in a)).sum()),
        'unique_authors': len({p['id'] for authors in df['authors'] for p in authors if p.get('id')}),
    }


def export_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = ['id', 'doi', 'title', 'year', 'type', 'topic', 'topic_weight_share', 'author_count']
    return df[[c for c in cols if c in df.columns]].sort_values(['year','id'],ascending=[False,True]).reset_index(drop=True)


def reading_table(df: pd.DataFrame, topic_names: dict[int, str], excerpt_chars: int = 280) -> pd.DataFrame:
    """Papers as a reader sees them: title, year, topic, abstract excerpt and source link."""
    def excerpt(text) -> str:
        text = str(text or '').strip()
        if not text:
            return '(no usable abstract)'
        return text if len(text) <= excerpt_chars else text[:excerpt_chars].rsplit(' ', 1)[0] + ' …'
    out = pd.DataFrame({
        'Title': df['title'], 'Year': df['year'],
        'Topic': df['topic'].map(topic_names).fillna('No topic (abstract too short or missing)'),
        'Abstract excerpt': df['abstract'].map(excerpt) if 'abstract' in df else '(no usable abstract)',
        'Source': df['id'],
    })
    return out.sort_values(['Year', 'Source'], ascending=[False, True]).reset_index(drop=True)
