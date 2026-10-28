"""Author topic profiles: which NMF topics each author's selected papers fall in.

An author is not assigned one permanent topic. For every author in the current
selection we count their topic-assigned papers per topic and classify them:

* **Dominant** - at least ``MIN_PAPERS`` topic-assigned papers and one topic holds
  strictly more than ``THRESHOLD`` (50%) of them. Exactly 50% is not dominant.
* **Mixed** - at least ``MIN_PAPERS`` topic-assigned papers, no topic above 50%.
* **Insufficient evidence** - fewer than ``MIN_PAPERS`` topic-assigned papers, so a
  single paper never gives an author a research identity (1/1 = 100% is not enough).

Papers without a usable abstract (not text-eligible) have no topic and are left
out of the topic denominator, but still count in "Selected papers".
"""
from __future__ import annotations
import pandas as pd

MIN_PAPERS = 2
THRESHOLD = 0.5
NO_HIGHLIGHT = 'No highlight'
MUTED_FILL = '#3A4250'

COLUMNS = ['Author ID', 'Author', 'Selected papers', 'Topic-assigned papers', 'Classification',
           'Dominant topic', 'Topic profile']


def author_topic_profiles(works: pd.DataFrame, topic_names: dict[int, str],
                          min_papers: int = MIN_PAPERS, threshold: float = THRESHOLD) -> pd.DataFrame:
    """One row per author in ``works``, with per-topic counts and a classification."""
    counts: dict[str, dict] = {}
    for row in works.itertuples():
        topic = getattr(row, 'topic', None)
        assigned = bool(getattr(row, 'text_eligible', False)) and topic in topic_names
        seen = set()
        for author in row.authors if isinstance(row.authors, list) else []:
            if not isinstance(author, dict) or not author.get('id') or author['id'] in seen:
                continue
            seen.add(author['id'])
            entry = counts.setdefault(author['id'], {'name': author.get('name', author['id']), 'papers': 0,
                                                     'topics': {name: 0 for name in topic_names.values()}})
            entry['papers'] += 1
            if assigned:
                entry['topics'][topic_names[topic]] += 1
    rows = []
    for author_id, entry in counts.items():
        topic_counts = entry['topics']
        assigned = sum(topic_counts.values())
        best = max(topic_counts, key=lambda name: (topic_counts[name], -list(topic_counts).index(name))) if topic_counts else None
        if assigned < min_papers:
            label, dominant = 'Insufficient evidence', ''
        elif topic_counts[best] / assigned > threshold:
            label, dominant = 'Dominant', best
        else:
            label, dominant = 'Mixed', ''
        profile = ' · '.join(f'{name.split(" · ")[0]} {n}' for name, n in topic_counts.items() if n) or 'no topic-assigned papers'
        rows.append({'Author ID': author_id, 'Author': entry['name'], 'Selected papers': entry['papers'],
                     'Topic-assigned papers': assigned, 'Classification': label, 'Dominant topic': dominant,
                     'Topic profile': profile, **{name: n for name, n in topic_counts.items()}})
    frame = pd.DataFrame(rows, columns=COLUMNS + list(topic_names.values()))
    return frame.sort_values(['Selected papers', 'Author ID'], ascending=[False, True]).reset_index(drop=True)


def authors_in_topic(profiles: pd.DataFrame, topic_label: str) -> set:
    """Authors with at least one selected, topic-assigned paper in ``topic_label``."""
    if topic_label not in profiles.columns:
        return set()
    return set(profiles.loc[profiles[topic_label] > 0, 'Author ID'])


def hover_text(profiles: pd.DataFrame) -> dict:
    """Short plain-text topic summary per author, for network tooltips."""
    out = {}
    for row in profiles.itertuples(index=False):
        text = f'Topics: {row[6]}'
        if row[4] == 'Dominant':
            text += f' (mostly {row[5].split(" · ")[0]})'
        elif row[4] == 'Mixed':
            text += ' (mixed)'
        out[row[0]] = text
    return out


def node_colour(community_colour: str, highlight: dict | None, node, topic_colour: str | None) -> dict | str:
    """vis.js colour for a node.

    Without a highlight the node keeps its community colour. With a highlight, the
    fill shows the topic (topic colour if the author has a paper in it, muted grey
    if not) and the border keeps the community colour, so both meanings survive.
    """
    if not highlight:
        return community_colour
    fill = topic_colour if highlight.get(node) else MUTED_FILL
    return {'background': fill, 'border': community_colour,
            'highlight': {'background': fill, 'border': '#FFFFFF'}}
