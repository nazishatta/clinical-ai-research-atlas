# Clinical AI Research Atlas — connected evidence update

This is a **working-source candidate**, not a claim of full scientific or browser sign-off. It builds on the supplied v1.2 bundle and preserves its frozen OpenAlex snapshot.

## Mac / VS Code installation

1. Extract this ZIP to a **new directory**. Do not overwrite your previous v1.2 copy.
2. In VS Code, open the `clinical-ai-research-explorer` folder itself.
3. Open Terminal > New Terminal and confirm `app.py` appears when running `ls`.
4. Run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/validate_release.py
python -m pytest -q
python -m streamlit run app.py
```

If a dependency installation fails, record the exact error. Do not report tests as passed unless the commands complete.

## New evidence exploration

- Sidebar chart-selection controls: one or more years, NMF topics, and exact unigram/bigram term. OR applies within a category; AND applies between categories.
- Click an annual bar to restrict the selection to its year.
- Click a topic bar or term bar to focus on matching records. Chart clicks take precedence for that category until **Clear chart selections**.
- Shared counts and all tabs derive from the same selected paper population.
- Download **selected evidence CSV** and verify that its number of rows matches **Selected works**.
- In the collaboration tab, inspect an author, inspect an author pair, and download the matching shared papers. The author focus does not silently restrict the global corpus.
- Author node and adjacency-matrix direct-click-to-filter actions are **not implemented**; author ID dropdowns and the relationship table are the supported alternatives.

## Not yet complete

- Human review of the 95-paper relevance sample and 25 NMF topic examples is still required. Numeric model stability does not validate scientific labels.
- The 2025 spike remains subject to search/index/sampling effects.
- Browser-level accessibility and performance tests must be run on the actual deployed app.
- The independently described animation patch was **not supplied with this request**, so animated entrance sequences, pause/resume/replay, and reduced-motion handling have **not been merged**.
- Streamlit's automatic bar click selection must be verified on your Mac; selection via sidebar remains available even if chart-click behavior differs by runtime version.
- Current `st.tabs` executes tab bodies; heavy-graph on-demand optimization is still outstanding.

## Suggested acceptance walkthrough

1. Reset all filters, record Selected works count.
2. Select a year from a publication bar, confirm counts across tabs and CSV rows.
3. Choose a topic, confirm the subset and paper list, then clear chart selections.
4. Choose a term, confirm selected documents use identical tokenization rules.
5. Choose an author and second author, cross-check shared-paper count manually.
6. Test no-match terms, empty graphs, download filenames, chart zoom, keyboard-based filters, mobile view.
7. Perform the existing relevance, NMF, network-identity and 2025 investigation reviews before submitting scientific conclusions.

## Academic integrity

The syllabus permits AI support but requires attribution, and graded scientific judgments must remain your own. Keep the accurate disclosure in submitted documentation even if you remove on-screen presentation captions.
