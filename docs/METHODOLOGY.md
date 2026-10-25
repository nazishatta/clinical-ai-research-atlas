# Methodology and research boundaries

## Research design
Descriptive, retrospective bibliographic exploration; no clinical prediction model is trained. Three modalities—time, text, and relationships—describe one search-defined corpus. Unit of analysis: unique OpenAlex work; network nodes: OpenAlex author IDs. Shared filters use inclusive publication-year bounds, OR across selected term signals, and optional fixed NMF topic assignment.

## Search and selection
Exact query and API filter are in `configs/study_scope.json` and the frozen retrieval manifest. Title/abstract search combines (clinical prediction OR clinical decision support), (machine learning OR artificial intelligence), and (calibration OR explainability OR uncertainty OR interpretability). Window: 2016–2025. This phrase-based strategy misses synonyms and can retrieve broadly relevant reviews. It is not a systematic review or a census of all clinical AI.

Eligible: English works labeled article/review/preprint; valid 2016–2025 year; stable ID; no retraction flag. Exclude other/unknown languages, other document types, repeated work IDs and normalized DOIs, flagged retractions, invalid years. First encountered DOI version is retained, not necessarily the canonical published version. Document type does NOT prove peer review. These choices are transparent starting decisions for owner review.

All returned rows were collected through basic pagination. At collection the API reported 2,100 results and 2,100 rows were downloaded. One duplicate work ID occurred; the search index may change or pagination ties may repeat records. This is not proof that every distinct matching work was captured. Two additional duplicate-DOI rows were excluded. Freeze the actual snapshot for reproducible analysis.

## Parent and eligible subsets
Temporal counts use all retained works. NLP requires at least 30 reconstructed abstract words. Network uses available identified authors. Do not remove missing-abstract works from temporal totals. A topic filter implicitly restricts to topic-assigned text records; this is displayed in the app.

Term-signal matching is case-insensitive regex over title + abstract. Signals overlap. They are lexical indicators, not assessments that calibration or external validation was correctly performed. 'LIME' and similar short terms can be ambiguous. Rates use text-eligible works as denominator. These denominators and the selection-conditioned meaning are shown on the chart.

## Text pipeline
English stop words plus documented generic scientific words; unigrams/bigrams; TF-IDF sublinear term frequency; min_df=3, max_df=.95, max_features=7,000. Titles and abstracts are concatenated. Frequency chart uses binary CountVectorizer and shows number of documents containing a term, not total token occurrences. Its vocabulary is recomputed within the selection.

NMF candidates: 5, 8, 10 components; seeds 0,7,21,42,99; nndsvdar initialization; max_iter=600. Hungarian alignment compares cosine similarity of components; top-10 Jaccard measures term overlap. Reconstruction error alone does not select the model. Provisional numeric rule: smallest converged candidate with mean aligned cosine >=.90. Five fixed-vocabulary bootstrap resamples additionally test sampling sensitivity of the selected count. This bootstrap does not test changes in preprocessing/vocabulary or establish semantic truth. Human review of representative abstracts and labels remains pending.

Each nonzero document gets its largest-weight component; normalized dominant weight is shown, NOT a calibrated probability. The model is fitted once across the frozen corpus so topic identities remain comparable across years. This is retrospective description, not forecasting; no predictive train/test performance is claimed. No independent yearly refits are compared as identical topics.

## Networks
Deduplicate author IDs within each paper. Every pair of identified coauthors creates an undirected edge; no self-loops. Raw weight counts shared papers. Strength adds 1/(n-1) for a team of n identified authors. Thus each author receives total strength 1 per multi-author paper. Missing author IDs may alter observed team size; OpenAlex author disambiguation errors remain possible.

An edge filter removes relationships below a selected shared-paper threshold while retaining nodes as isolates. Rankings are computed on this selected graph. Default threshold two reduces one-paper cliques. Default ranking uses team-normalized strength; degree is a selectable alternative. A capped induced graph is displayed; its size/edge counts are clearly stated. Communities use greedy modularity with strength on the DISPLAYED subgraph, NOT full-network communities. Layout uses seed42; circular is an alternative. Community colors/shapes are local, not permanent identities. No claim of institutional membership or researcher impact follows from these metrics.

## Missingness and inference
Early-year counts are small. Abstract coverage varies substantially by year. Recent publication indexing, search vocabulary, author matching, language/type exclusions, and reviews/preprints can shift results. Do not infer causal explanations, clinical adoption, scientific quality, or complete field growth. Citation counts at retrieval are stored only as metadata; they are not used to rank scientific merit.

## Sources
https://help.openalex.org/api/filtering/
https://help.openalex.org/data/works/
https://github.com/ourresearch/openalex-docs/blob/main/license.md
https://docs.streamlit.io/develop/api-reference/app-testing
