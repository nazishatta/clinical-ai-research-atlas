# Real-data feasibility audit

Retrieved at: 2026-10-22T06:23:36.781569+00:00

API-reported candidate rows: 2,100; downloaded rows: 2,100.
Retained unique eligible works: 1,395.
Reconstructable abstracts: 86.74%; text-eligible (>=30 words): 1,209.
Full coauthorship: 6,464 authors; 30,067 edges; 1,093 components; largest component 134 authors.
Repeated collaboration edges: 1,400; largest observed team 78 identified authors.

## Eligibility exclusions

- ineligible_document_type: 375
- non_english_or_unknown_language: 327
- duplicate_doi: 2
- duplicate_work_id: 1

## Yearly coverage

| Year | Works | Abstract available | Text eligible |
|---|---:|---:|---:|
| 2016 | 5 | 60.0% | 60.0% |
| 2017 | 10 | 80.0% | 80.0% |
| 2018 | 15 | 73.33% | 73.33% |
| 2019 | 28 | 71.43% | 71.43% |
| 2020 | 72 | 83.33% | 83.33% |
| 2021 | 104 | 85.58% | 85.58% |
| 2022 | 129 | 86.05% | 86.05% |
| 2023 | 172 | 83.72% | 83.72% |
| 2024 | 216 | 91.2% | 91.2% |
| 2025 | 644 | 88.04% | 87.89% |

## Decision

**PROCEED WITH SCIENTIFIC CONDITIONS.** All three modalities are computationally feasible. Corpus relevance precision and semantic topic quality are not established by metadata checks. Early years are sparse; 2025 dominates; coverage varies. The term-defined search is not representative of all clinical AI.

## Provisional topic evaluation

Selected 5 topics using the documented smallest-stable-candidate rule. Initialization stability is not semantic validation. Fixed-vocabulary bootstrap mean aligned cosine across five resamples: 0.968, 0.959, 0.957, 0.963, 0.960.

## Human review still outstanding

- 95 papers sampled across years for relevance decisions. No decisions prefilled.
- Review representative abstracts for five topics; propose meaningful labels and record weaknesses.
- Independently assemble a known-relevant-paper benchmark, then assess misses.
- Check suspicious author identities and very large teams.

## Retrieval caveat

One repeated work ID appeared across API pages; two repeated DOIs were also removed. Downloaded-row completion does not prove exhaustive unique-work coverage. The frozen snapshot, not a future API search, is the reproducibility reference.

## Proposed thresholds and current status

| Check | Target | Result |
|---|---|---|
| Unique retained work IDs | 100% | PASS |
| Valid eligible publication years | 100% | PASS |
| Abstract availability | Aim >=80% overall | PASS overall; early-year coverage lower |
| Relevance precision | Aim >=85% on manual review | PENDING |
| Known-paper retrieval | Aim >=90% of independent benchmark | PENDING |
| Informative actual graph | Real edges + repeated collaboration | PASS computationally; interpretation pending |
| Topic interpretability | Representative-document review | PENDING |

These are project quality targets, not the professor’s grading rubric.