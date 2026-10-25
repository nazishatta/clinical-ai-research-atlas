# Investigation of the 2025 rise

Frozen retained corpus: **216 works (2024)** and **644 (2025)**; ratio **2.98**.

## What the actual records establish

- Article-only counts: 179 → 561. Preprints/reviews alone therefore do not account for the increase.
- Excluding the five largest 2025 source-ID groups from BOTH years: 202 → 579. This is a sensitivity check, not a defensible revised sampling rule.
- Exact case-normalized repeated-title rows: 42; exact repeated abstract rows among eligible text records: 10. Inspect the CSVs; matching titles do not prove duplicate works.
- Source and monthly distributions are supplied as CSV. Source concentration can be inspected without assigning unsupported journal-quality labels.

## What remains unresolved

The snapshot did not retain created/updated indexing timestamps. It cannot determine whether publication growth, newly indexed sources, indexing backfill, evolving terminology, or relevance differences caused the rise. Original dates, versions, and source records need review.
Query-variant counts, where requested and successful, are API metadata counts on the new query date. They use language/type/retraction filters but not the frozen DOI deduplication; do not compare them as perfectly identical populations.
Relevance and topic review are still required, particularly a stratified comparison of 2024 versus 2025. Known relevant papers should be assembled independently of these results.

## Defensible presentation wording

> Within this query-defined frozen corpus, retained 2025 records outnumber 2024 records by roughly three to one. The increase persists in article-only counts. Its cause and its representativeness of clinical-AI research remain unverified.

Do not call this an acceleration in the whole clinical-AI field. Do not claim that similar query-variant ratios establish absence of coverage bias.

## Search-variant execution status

3 of 8 requests succeeded. Failed requests are missing counts, not zeros. No complete 2024/2025 variant pair was verified, so cross-query trend agreement remains unverified. Exact filters and individual statuses are saved in query_variants.json/CSV.
