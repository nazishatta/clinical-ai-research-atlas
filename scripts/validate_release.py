"""Audit frozen corpus and human-review progress without inventing review decisions."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'processed'
REVIEWS = ROOT / 'reviews'
VALID = {'INCLUDE', 'EXCLUDE', 'UNCERTAIN'}


def locate_review(name: str) -> Path:
    preferred = REVIEWS / name
    return preferred if preferred.exists() else DATA / name


def review_table(name: str, fields: list[str]) -> pd.DataFrame:
    path = locate_review(name)
    frame = pd.read_csv(path, keep_default_na=False)
    missing = set(fields) - set(frame.columns)
    if missing:
        raise ValueError(f'{path}: missing {sorted(missing)}')
    if frame['id'].duplicated().any():
        raise ValueError(f'{path}: duplicate review IDs')
    return frame


def relevance_summary(works: pd.DataFrame, review: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    review = review.copy()
    review['decision'] = review.decision.astype(str).str.strip().str.upper()
    invalid = review[~review.decision.isin(VALID | {''})]
    if not invalid.empty:
        raise ValueError(f'Invalid relevance decisions: {invalid.decision.unique().tolist()}')
    known = set(works.id)
    if not set(review.id).issubset(known):
        raise ValueError('Review sample includes IDs absent from the retained corpus')
    pop = works.groupby('year').size().to_dict()
    rows = []
    for year, group in review.groupby('year', sort=True):
        N = int(pop[int(year)])
        inc = int((group.decision == 'INCLUDE').sum())
        exc = int((group.decision == 'EXCLUDE').sum())
        uncertain = int((group.decision == 'UNCERTAIN').sum())
        pending = int((group.decision == '').sum())
        if inc + exc + uncertain + pending != len(group):
            raise AssertionError('Unexpected review count mismatch')
        rows.append({'year': int(year), 'population': N, 'sample': len(group), 'include': inc, 'exclude': exc, 'uncertain': uncertain, 'pending': pending, 'complete': pending == 0 and uncertain == 0, 'precision': (inc/len(group)) if pending == 0 and uncertain == 0 else None})
    detail = pd.DataFrame(rows)
    all_done = bool(detail.complete.all()) and len(review) > 0
    covered_years = set(detail.year)
    all_done = all_done and covered_years == set(pop)
    estimate = (sum(row.population * row.precision for row in detail.itertuples()) / len(works)) if all_done else None
    # Intentionally no misleading inferential CI: stratified variance needs an explicit uncertainty method.
    return detail, {'reviewed': int((review.decision != '').sum()), 'sample_total': len(review), 'unresolved': int((review.decision.isin(['', 'UNCERTAIN'])).sum()), 'all_strata_complete': all_done, 'year_weighted_precision': estimate, 'precision_status': 'calculated; uncertainty interval not estimated' if all_done else 'NOT ESTIMATED: incomplete review'}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--strict', action='store_true', help='Exit nonzero while human sign-offs remain outstanding')
    args = ap.parse_args()
    works = pd.read_json(DATA/'works.jsonl', lines=True, convert_dates=False)
    if len(works) != works.id.nunique():
        raise ValueError('Duplicate work IDs')
    if works.year.isna().any():
        raise ValueError('Missing publication years')
    review = review_table('manual_review.csv', ['id', 'year', 'decision', 'reason', 'reviewer'])
    strata, relevance = relevance_summary(works, review)
    topics = review_table('topic_review.csv', ['id','topic','interpretability_1_to_5','proposed_label','notes'])
    grades = pd.to_numeric(topics.interpretability_1_to_5, errors='coerce')
    if grades.notna().any() and (~grades.dropna().between(1,5)).any():
        raise ValueError('Topic scores must be 1–5')
    topic_done = (grades.notna() & topics.proposed_label.astype(str).str.strip().ne('')).sum()
    # Reconcile all-year count and denominator invariants against the source records.
    counts = works.groupby('year').size().to_dict()
    text_counts = works[works.text_eligible].groupby('year').size().to_dict()
    invariant_errors = []
    for year in counts:
        count = int(counts[year]); text_n = int(text_counts.get(year,0))
        if text_n > count:
            invariant_errors.append(f'{year}: text count exceeds work count')
    signal_categories = sorted({signal for values in works.signals for signal in values})
    for y in counts:
        rows = works[(works.year == y) & works.text_eligible]
        for signal in signal_categories:
            matches = sum(signal in vals for vals in rows.signals)
            if matches > len(rows):
                invariant_errors.append(f'{y} {signal}: numerator exceeds denominator')
    if invariant_errors:
        raise ValueError('; '.join(invariant_errors))
    details_dir = ROOT / 'validation'
    details_dir.mkdir(exist_ok=True)
    strata.to_csv(details_dir/'relevance_by_year.csv', index=False)
    pd.DataFrame([{'year':int(y),'works':int(counts[y]),'text_eligible':int(text_counts.get(y,0)),'excluded_from_text':int(counts[y]-text_counts.get(y,0))} for y in sorted(counts)]).to_csv(details_dir/'population_denominators.csv',index=False)
    benchmark = REVIEWS/'independent_benchmark.csv'
    if benchmark.exists():
        bench_df = pd.read_csv(benchmark,keep_default_na=False)
        benchmark_count = int((bench_df.get('retrieved',pd.Series(dtype=str)).astype(str).str.upper() == 'YES').sum())
        benchmark_complete = len(bench_df) >= 10 and (bench_df.get('retrieved',pd.Series(dtype=str)).astype(str).str.upper().isin(['YES','NO']).sum() == len(bench_df))
    else:
        bench_df = pd.DataFrame(); benchmark_count=0; benchmark_complete=False
    status = {
        'source_record_count':len(works), 'unique_work_ids':int(works.id.nunique()),
        'abstract_available_count':int(works.abstract_available.sum()),
        'text_eligible_count':int(works.text_eligible.sum()),
        'relevance':relevance,
        'topic_review':{'completed_rows':int(topic_done),'total_rows':len(topics),'interpretation_approved':bool(topic_done == len(topics) and len(topics)>0)},
        'benchmark':{'rows':len(bench_df),'retrieved_yes':benchmark_count,'completed':bool(benchmark_complete)},
        'denominator_invariants_pass':True,
        'not_automatically_verified':['independent human screening','NMF semantic interpretation','search recall','2025 spike cause','author identity correctness','browser accessibility','deployment']
    }
    (details_dir/'validation_status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    lines = ['# Validation status — generated from local files','',f"Frozen works: **{len(works):,}**; distinct IDs: **{works.id.nunique():,}**.",f"Relevance decisions entered: **{relevance['reviewed']}/{relevance['sample_total']}**; unresolved: **{relevance['unresolved']}**.",f"Year-weighted relevance precision: **{relevance['year_weighted_precision'] if relevance['year_weighted_precision'] is not None else 'NOT AVAILABLE'}**.",f"Topic rows scored and labeled: **{topic_done}/{len(topics)}**.",f"Independent benchmark complete: **{'YES' if benchmark_complete else 'NO'}**.",'','Automated denominator invariants: **PASS**.','', 'This report does not certify human validation, semantic validity, field-wide trends, browser accessibility, or deployment.','', 'Review the original protocol in `docs/REVIEW_PROTOCOL.md` and do not mislabel AI-assisted judgments as independent human screening.']
    (details_dir/'VALIDATION_STATUS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines))
    ready = relevance['all_strata_complete'] and topic_done == len(topics) and benchmark_complete
    return 2 if args.strict and not ready else 0

if __name__ == '__main__':
    sys.exit(main())
