"""One-sentence text alternatives for charts.

Each function turns the exact table behind a chart into a plain sentence. The
sentence is shown under the chart ("In short") and used as the alt text of
embedded animated charts, so screen-reader users get the chart's point, not
only its title.
"""
from __future__ import annotations
import pandas as pd


def annual_works(counts: pd.DataFrame) -> str:
    if counts.empty or counts.Works.sum() == 0:
        return 'No works match this selection in any year.'
    first, last = counts.iloc[0], counts.iloc[-1]
    peak = counts.loc[counts.Works.idxmax()]
    return (f'Works per year go from {int(first.Works):,} in {int(first.Year)} to {int(last.Works):,} in '
            f'{int(last.Year)}; the highest year is {int(peak.Year)} with {int(peak.Works):,} works.')


def signal_shares(shares: pd.DataFrame) -> str:
    valid = shares.dropna(subset=['Share (%)'])
    if valid.empty:
        return 'No text-eligible works in this selection, so signal shares cannot be computed.'
    def top(year: int) -> str:
        rows = valid[valid.Year == year].sort_values(['Share (%)', 'Signal'], ascending=[False, True])
        row = rows.iloc[0]
        return f"{row.Signal} ({row['Share (%)']:.0f}% of {int(row.Denominator):,} works)"
    first, last = int(valid.Year.min()), int(valid.Year.max())
    if first == last:
        return f'In {last}, the most frequent trustworthiness signal is {top(last)}.'
    return f'The most frequent trustworthiness signal is {top(first)} in {first} and {top(last)} in {last}.'


def document_terms(frequency: pd.DataFrame, n: int = 3) -> str:
    if frequency.empty:
        return 'No terms are available for this selection.'
    top = frequency.sort_values(['Documents', 'Term'], ascending=[False, True]).head(n)
    listed = ', '.join(f'"{r.Term}" ({int(r.Documents):,} documents)' for r in top.itertuples())
    return f'The most common terms are {listed}.'


def topic_distribution(dist: pd.DataFrame) -> str:
    if dist.empty:
        return 'No topic-assigned works in this selection.'
    ordered = dist.sort_values(['Works', 'Topic'], ascending=[False, True])
    big, small = ordered.iloc[0], ordered.iloc[-1]
    total = int(dist.Works.sum())
    return (f'{len(dist)} topics cover {total:,} works. The largest is {big.Topic} with {int(big.Works):,} works '
            f'({big.Works / total * 100:.0f}%); the smallest is {small.Topic} with {int(small.Works):,}.')


def topic_shares(shares: pd.DataFrame) -> str:
    valid = shares.dropna(subset=['Share (%)'])
    periods = list(dict.fromkeys(valid.Period))
    if len(periods) < 2:
        return 'Too few periods in this selection to compare topic shares over time.'
    first, last = periods[0], periods[-1]
    wide = valid.pivot_table(index='Topic', columns='Period', values='Share (%)')
    change = (wide[last] - wide[first]).sort_values()
    fall, rise = change.index[0], change.index[-1]
    return (f'From {first} to {last}, {rise} grows the most ({wide.at[rise, first]:.0f}% to {wide.at[rise, last]:.0f}% '
            f'of text-eligible works) and {fall} shrinks the most ({wide.at[fall, first]:.0f}% to {wide.at[fall, last]:.0f}%).')


def communities(table: pd.DataFrame) -> str:
    if table.empty:
        return 'No communities in the displayed graph.'
    big = table.sort_values('Researchers', ascending=False).iloc[0]
    return (f'{len(table)} communities in the displayed graph; the largest, {big.Community}, '
            f'has {int(big.Researchers):,} researchers.')


def ranking(top: pd.DataFrame, measure: str) -> str:
    if top.empty:
        return 'No authors match the current selection.'
    lead = top.iloc[0]
    value = lead[measure]
    shown = f'{value:.2f}' if isinstance(value, float) else f'{int(value):,}'
    return f'{lead.Author} ranks first by {measure.lower()} ({shown}) among the top {len(top)} authors shown.'


def network(authors: int, edges: int, n_communities: int, label: str) -> str:
    return (f'{label}: {authors:,} authors joined by {edges:,} coauthorship links in {n_communities} '
            'algorithmic communities. Use the author selectors and tables below for the same information as text.')
