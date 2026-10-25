# Clinical AI Research Atlas — VS Code implementation bundle (v1.2 validation toolkit)

This release **preserves the original v1.1 application and frozen OpenAlex data**. Its new validation script, review templates, tests, and VS Code tasks make the remaining checks executable. It **does not** fabricate human paper decisions or certify deployed browser behavior.

## Start on macOS in VS Code

1. Unzip the bundle and use **File → Open Folder** to open `clinical-ai-research-explorer`.
2. Open **Terminal → New Terminal** and enter:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python scripts/validate_release.py
python -m pytest -q
python -m streamlit run app.py
```

The terminal prints a local Streamlit URL. Use the VS Code Command Palette → **Tasks: Run Task** for shortcuts after setup.

### Existing Mac shortcuts

`Setup_Mac.command`, `Launch_Mac.command`, and `Test_Mac.command` remain from v1.1. If the OS blocks them, the terminal commands above are the portable source of truth.

## Perform the unfinished human reviews

- Source (blank) relevance sample: `data/processed/manual_review.csv`. Copy it to `reviews/manual_review.csv` and fill **decision**, **reason**, **reviewer**. Allowed decisions: INCLUDE, EXCLUDE, UNCERTAIN. Preserve all IDs and years.
- Source (blank) topic examples: `data/processed/topic_review.csv`. Copy to `reviews/topic_review.csv` and enter interpretation score (1–5), proposed label, notes; inspect boundary cases separately.
- Add independently found reference papers to `reviews/independent_benchmark.csv` (**10–20** genuinely independent examples; YES/NO for `retrieved`). Do not select these by browsing the retrieved corpus.
- Read `docs/REVIEW_PROTOCOL.md` for inclusion and sample-weighting rules.
- Complete `reviews/browser_qa.csv` only after observing the real local or public application.

Run `python scripts/validate_release.py` after each review session. Outputs update under `validation/`:

- `validation_status.json` — machine-readable completion counts
- `VALIDATION_STATUS.md` — readable progress report
- `relevance_by_year.csv` — year-stratified decision counts and estimates when complete
- `population_denominators.csv` — work/text eligibility by year

The script intentionally **withholds year-weighted precision** while sampled decisions remain unfinished. It does not yet compute a confidence interval; any reported precision requires a separately documented uncertainty calculation. Use `--strict` if you want it to exit nonzero until relevance, topic reviews, and benchmark are complete.

## Validation workflow

1. Record screening decisions and investigate uncertain titles using originals as needed.
2. Inspect topic-label fit and boundary documents. Do not treat NMF stability as semantic validation.
3. Review duplicate candidates and the 2024–2025 spike using `docs/spike_audit/`.
4. Reconcile every app chart with the specific eligible population and selection.
5. Perform manual browser QA and confirm the deployment URL.

## Provenance and status

The `data/raw` snapshot and previous audit remain untouched. The existing v1.1 `BUNDLE_MANIFEST.json` is **historical** and does not hash the new v1.2 files. Use the new ZIP checksum provided separately for distribution integrity. Existing v1.1 test evidence is not treated as a substitute for testing this version on your machine.

## Coursework integrity

The course permits AI as a supplement but requires disclosure. AI-generated code and screening suggestions must be acknowledged; the substantive scientific judgments and graded interpretations should be reviewed and completed by you.
