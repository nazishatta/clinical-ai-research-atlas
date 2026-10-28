"""Key findings for the Overview, computed from the frozen snapshot.

Every number here is calculated from the bundled data at run time, never typed in,
and every finding carries its limitation. Findings use the full snapshot so they
do not change with the sidebar filters.
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

from src.analysis import topic_shares_by_period


def corpus_growth(works: pd.DataFrame, spike: dict | None = None) -> dict:
    by_year = works.groupby('year').size()
    last, prev = int(by_year.index.max()), int(by_year.index.max()) - 1
    n_last, n_prev = int(by_year.get(last, 0)), int(by_year.get(prev, 0))
    ratio = n_last / n_prev if n_prev else float('nan')
    articles = works[works.type == 'article'].groupby('year').size()
    text = (f'**Corpus growth.** The snapshot holds {n_last:,} works from {last} against {n_prev:,} from {prev} '
            f'(about {ratio:.1f} times as many). The rise persists among records typed as articles '
            f'({int(articles.get(prev, 0)):,} → {int(articles.get(last, 0)):,}). This is a pattern in the retrieved OpenAlex corpus, '
            'not proof that the field grew this much: indexing coverage, search vocabulary and abstract availability may have changed.')
    table = pd.DataFrame({'Year': [prev, last], 'All retained works': [n_prev, n_last],
                          'Articles only': [int(articles.get(prev, 0)), int(articles.get(last, 0))]})
    return {'text': text, 'table': table, 'ratio': ratio, 'last': last, 'prev': prev}


def text_coverage(works: pd.DataFrame) -> dict:
    eligible = int(works.text_eligible.sum())
    total = len(works)
    by_year = works.groupby('year').agg(Works=('id', 'size'), Text_eligible=('text_eligible', 'sum')).reset_index()
    by_year['Coverage (%)'] = (100 * by_year.Text_eligible / by_year.Works).round(1)
    by_year = by_year.rename(columns={'year': 'Year', 'Text_eligible': 'Text-eligible'})
    text = (f'**Text coverage.** Topic and term results use the {eligible:,} of {total:,} works ({100 * eligible / total:.0f}%) '
            'with an abstract of at least 30 words. The other works still count in the timeline and the network.')
    return {'text': text, 'table': by_year, 'eligible': eligible, 'total': total}


def signal_overlap(works: pd.DataFrame) -> dict:
    eligible = works[works.text_eligible]
    n_signals = eligible.signals.map(len)
    multi = int((n_signals >= 2).sum())
    table = (n_signals.value_counts().sort_index().rename_axis('Signals mentioned').reset_index(name='Works'))
    text = (f'**Signals overlap.** {multi:,} of {len(eligible):,} text-eligible works ({100 * multi / len(eligible):.0f}%) mention two or more '
            'trustworthiness signals (calibration, explainability, uncertainty, validation and reliability), so signal shares do not add up to 100%. '
            'Signals are term matches, not quality labels.')
    return {'text': text, 'table': table, 'multi': multi}


def topic_shift(works: pd.DataFrame, topic_names: dict[int, str]) -> dict:
    shares = topic_shares_by_period(works[works.text_eligible], topic_names, int(works.year.min()), int(works.year.max()))
    periods = list(dict.fromkeys(shares.Period))
    wide = shares.pivot_table(index='Topic', columns='Period', values='Share (%)')[[periods[0], periods[-1]]]
    change = (wide[periods[-1]] - wide[periods[0]]).sort_values()
    fall, rise = change.index[0], change.index[-1]
    text = (f'**Topic mix shifted.** {fall} falls from {wide.at[fall, periods[0]]:.0f}% of text-eligible works in {periods[0]} '
            f'to {wide.at[fall, periods[-1]]:.0f}% in {periods[-1]}, while {rise} rises from {wide.at[rise, periods[0]]:.0f}% '
            f'to {wide.at[rise, periods[-1]]:.0f}%. Topic labels are automatic keyword lists until they are reviewed against their representative papers.')
    table = wide.round(1).reset_index().rename(columns={periods[0]: f'{periods[0]} share (%)', periods[-1]: f'{periods[-1]} share (%)'})
    table['Change (points)'] = (table.iloc[:, 2] - table.iloc[:, 1]).round(1)
    return {'text': text, 'table': table}


def network_meaning(audit: dict) -> dict:
    comps = int(audit.get('network_components', 0))
    largest = audit.get('largest_component_authors', 'unreported')
    text = (f'**Collaboration is fragmented.** The full coauthorship graph splits into {comps:,} separate groups; the largest connects '
            f'{largest} authors. An edge means two people share a paper in this corpus, not influence, quality or institutional membership.')
    table = pd.DataFrame([{'Measure': 'Connected groups (components)', 'Value': comps},
                          {'Measure': 'Authors in the largest group', 'Value': largest}])
    return {'text': text, 'table': table}


def key_findings(works: pd.DataFrame, topic_names: dict[int, str], audit: dict) -> list[dict]:
    return [corpus_growth(works), text_coverage(works), signal_overlap(works),
            topic_shift(works, topic_names), network_meaning(audit)]


def load_spike_audit(root: Path) -> dict:
    """The saved 2025 spike investigation (docs/spike_audit); empty dict if missing."""
    folder = root / 'docs' / 'spike_audit'
    if not (folder / 'summary.json').exists():
        return {}
    out = {'summary': json.loads((folder / 'summary.json').read_text())}
    for name in ['document_types_by_year', 'sources_by_year', 'repeated_titles', 'repeated_abstracts', 'query_variants']:
        path = folder / f'{name}.csv'
        out[name] = pd.read_csv(path) if path.exists() else pd.DataFrame()
    return out


def top_sources(sources: pd.DataFrame, years: tuple[int, int], n: int = 8) -> pd.DataFrame:
    """Largest sources in the later year, with their counts in the earlier year."""
    if sources.empty:
        return sources
    a, b = years
    wide = sources[sources.year.isin([a, b])].pivot_table(index='source', columns='year', values='Works', aggfunc='sum', fill_value=0)
    for year in (a, b):
        if year not in wide.columns:
            wide[year] = 0
    wide = wide[[a, b]].sort_values(b, ascending=False).head(n).reset_index()
    wide.columns = ['Source', f'{a} works', f'{b} works']
    return wide
