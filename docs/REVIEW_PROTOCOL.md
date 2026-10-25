# Human review protocol

## Corpus relevance: 95-paper worksheet
Use `data/processed/manual_review.csv`. It samples up to ten records per publication year with seed42, giving 95 records because 2016 contains only five. This is stratified, not a simple random sample. The overall unweighted acceptance proportion does not estimate corpus precision when strata sizes differ.

### Decisions
- INCLUDE: substantive research/review on ML/AI for clinical prediction or clinical decision support, with a relevant trustworthiness connection in title/abstract. Do not infer that a method was correctly validated from a mention alone.
- EXCLUDE: unrelated domain; no clinical prediction/support relevance; generic AI mention only; duplicate version needing consolidation; other documented scope violation.
- UNCERTAIN: insufficient abstract, ambiguous application, or unresolved version. Do not silently treat this as exclusion or inclusion.

Read title and abstract; use source record/full text where necessary and available. Record decision, specific reason, reviewer, and review date in your retained copy. Re-review uncertain cases and a small random subset after an interval; this is a consistency check, not independent inter-rater reliability.

Report included/excluded/uncertain counts per year. If estimating corpus relevance precision, weight year-specific reviewed acceptance proportions by each year's share of retained corpus records and report uncertainty/limitations. Do not call 95 hand-reviewed papers proof of complete search recall.

## Independent coverage benchmark
Before inspecting query hits, assemble 10–20 eligible relevant papers using known literature or an independent search. Record DOI, title, why eligible, and whether retrieved. Investigate misses. This is a recall diagnostic on a small benchmark, not full-field recall.

## NMF topic review: 25 representative documents
Use `data/processed/topic_review.csv`. Read five representative abstracts per topic, then inspect a few lower-weight and boundary documents. Score interpretability, propose a plain label, list ambiguous/overlapping themes, and record why the chosen topic count is useful. The top-five examples are selected for representativeness, not a random topic quality sample. Do not claim blinded validation.

The numeric count-selection rule is provisional. High cosine/Jaccard across seeds or bootstrap resamples is not proof of meaningful scientific categories. If revising topics, preserve the old artifacts and record the new configuration. Do not overwrite completed review sheets when regenerating outputs.

## Targeted 2025 check
Compare 2024 and 2025 relevance, types, source mix, date distributions, and uncertain cases using `docs/spike_audit/`. Even if similar query variants show growth, indexing coverage and publication-quality changes remain plausible. Do not infer causal explanations or clinical adoption.

## Completion record
After reviewing, write the number reviewed, unresolved cases, protocol changes, conclusions justified by the evidence, and remaining limitations. Keep the original blank worksheets as provenance and final annotated copies in `reviews/`.
