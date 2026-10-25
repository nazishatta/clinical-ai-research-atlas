# Clinical AI Research Atlas

A three-modality Streamlit research explorer: publication time-series, text/NLP, and coauthorship networks. Built for a DATS 6401 multimodality project and research-analytics portfolio.

**Status:** implemented with real OpenAlex data and automated validation. Human relevance screening, topic interpretation, browser accessibility/mobile QA, and public deployment are not yet certified. Do not claim this corpus represents all clinical AI or that papers are clinically trustworthy.

## Run on your Mac

Install Python 3.12, then open Terminal in this extracted folder:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, normally http://localhost:8501. Prepared data are bundled: the application does **not** need an API key or an internet connection to compute charts. Source-record buttons require internet.

## Research question

Within a search-defined corpus of clinical prediction and decision-support research, how do trustworthiness-related language, publication activity, and coauthorship patterns vary across 2016–2025?

## Five tabs

1. Overview: research question, selected coverage, traceable papers.
2. Research Evolution: yearly counts, overlapping signal shares, denominator/missingness tables.
3. Research Language: document-frequency bars, fixed NMF topics, actual abstracts, model evaluation.
4. Collaboration Network: structural encodings, author focus, layouts, threshold, adjacency matrix, rankings.
5. Synthesis & Methods: limits, provenance, eligibility, audit, filtered CSV export.

Shared year/signal/topic controls use one filtering function. Text and network eligibility rules are explicit. Color is supplemented by line styles, marker shapes, text summaries, and data tables.

## Understand the data before presenting

Read `docs/DATA_AUDIT.md`, `docs/METHODOLOGY.md`, and `docs/ACCEPTANCE_MATRIX.md`. Complete `data/processed/manual_review.csv` and `data/processed/topic_review.csv` yourself. No human labels have been invented. Work type is metadata, not proof of peer review. The selection includes reviews and preprints where identified by OpenAlex.

## Reproduce preprocessing from the bundled raw snapshot

```bash
python scripts/build_outputs.py --snapshot data/raw/snapshot_final_20261022
```

This regenerates processed outputs, including blank review sheets; COPY completed review sheets to `reviews/` before rebuilding. Topic models are not pickled; the fixed assignments and evaluation tables are portable JSON/CSV. Exact direct package versions are pinned in `requirements.txt`; `docs/environment.txt` records the complete observed environment.

## Fetch a NEW dated snapshot

```bash
python scripts/fetch_openalex.py --output data/raw/snapshot_NEW_DATE
python scripts/build_outputs.py --snapshot data/raw/snapshot_NEW_DATE
```

The output directory must be new. OpenAlex may impose budgets or require an API key for some requests. If needed, set `OPENALEX_API_KEY` in your environment; never commit it. The fetch script preserves exact filters, counts, page hashes, and retrieval time. Basic pagination supports only the first 10,000 results: larger searches require partitioning or authenticated cursor pagination. API search results can change; reproducing the bundled raw snapshot is distinct from re-querying today's database.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

AppTest simulates Streamlit runs; it does not certify browser pixels, touch behavior, or screen-reader usability. See `docs/QA.md` for the remaining checks.

## Deploy

1. Create your own GitHub repository and add this project.
2. Retain the manageable `data/processed/` files. The app needs them at runtime.
3. Raw data are ignored by default; preserve the bundled raw snapshot separately or provide a versioned download/source regeneration route.
4. In Streamlit Community Cloud, select the repository, `app.py`, and Python 3.12.
5. After deployment, perform `docs/QA.md` against the real URL, including all five tabs.
6. Submit the live URL, repository, and narrative required by Blackboard.

No repository has been published and no public deployment is claimed in this package.

## Attribution and AI assistance

Source: OpenAlex, https://openalex.org and https://help.openalex.org. Retrieval details are in `data/processed/retrieval_manifest.json`. OpenAlex publishes its data under CC0; abstract text may retain rights of its original authors/publishers. Retain source links and check intended redistribution conditions. Source attribution is also good scholarly practice.

AI assisted coding, documentation, computational checks, and QA design. The project owner must inspect the data, make and defend analytical decisions, verify interpretations, and disclose assistance according to the actual course policy. The software does not substitute for that review.

Code license: MIT (`LICENSE`). Third-party data are not relicensed by the code license.

## Full-bundle additions

Mac helpers: `Setup_Mac.command`, `Launch_Mac.command`, and `Test_Mac.command`. These scripts are provided and shell-syntax checked; they have not been executed on your Mac. See `docs/DEPLOYMENT.md`.

The 2025 increase is investigated in `docs/2025_SPIKE_AUDIT.md`, with underlying source/type/month tables and query-variant evidence in `docs/spike_audit/`. Human relevance/topic evaluation follows `docs/REVIEW_PROTOCOL.md`. Use `python scripts/verify_bundle.py` to verify the packaged file hashes.
