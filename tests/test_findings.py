import json
from pathlib import Path
import pandas as pd
from src.findings import corpus_growth, key_findings, load_spike_audit, network_meaning, signal_overlap, text_coverage, top_sources

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    rows = []
    for i in range(2):
        rows.append({'id': f'a{i}', 'year': 2024, 'type': 'article', 'text_eligible': True, 'signals': ['Calibration'], 'topic': 0})
    for i in range(6):
        rows.append({'id': f'b{i}', 'year': 2025, 'type': 'article' if i < 4 else 'preprint', 'text_eligible': i != 5,
                     'signals': ['Calibration', 'Uncertainty'] if i < 3 else [], 'topic': i % 2 if i != 5 else -1})
    return pd.DataFrame(rows)


def test_growth_coverage_and_overlap_numbers_come_from_the_data():
    w = fixture()
    g = corpus_growth(w)
    assert (g['prev'], g['last'], g['ratio']) == (2024, 2025, 3.0)
    assert '6 works from 2025 against 2 from 2024' in g['text'] and '(2 → 4)' in g['text']
    assert 'not proof' in g['text']
    c = text_coverage(w)
    assert (c['eligible'], c['total']) == (7, 8)
    assert signal_overlap(w)['multi'] == 3


def test_network_finding_states_what_an_edge_means():
    text = network_meaning({'network_components': 12, 'largest_component_authors': 40})['text']
    assert '12 separate groups' in text and 'not influence' in text


def test_real_snapshot_findings_match_audited_counts():
    works = pd.read_json(ROOT / 'data/processed/works.jsonl', lines=True, convert_dates=False)
    names = {t['id']: t['label'] for t in json.loads((ROOT / 'data/processed/topics.json').read_text())}
    audit = json.loads((ROOT / 'data/processed/audit.json').read_text())
    findings = key_findings(works, names, audit)
    assert len(findings) == 5 and all(f['text'] and not f['table'].empty for f in findings)
    spike = load_spike_audit(ROOT)['summary']
    growth = findings[0]
    assert growth['table']['All retained works'].tolist() == [spike['baseline_2024'], spike['baseline_2025']]
    assert growth['table']['Articles only'].tolist() == [spike['article_only_2024'], spike['article_only_2025']]


def test_top_sources_orders_by_later_year_and_fills_missing_with_zero():
    src = pd.DataFrame({'year': [2024, 2025, 2025], 'source': ['X', 'X', 'Y'], 'Works': [3, 1, 5]})
    out = top_sources(src, (2024, 2025))
    assert out.Source.tolist() == ['Y', 'X'] and out['2024 works'].tolist() == [0, 3]
