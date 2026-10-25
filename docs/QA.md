# Verification record and remaining browser QA

## Executed
- Real API retrieval, dated raw pages, page SHA-256 hashes.
- Processed data checksums and unique-ID/date/text eligibility tests.
- Known-answer graph fixture: pair counting, duplicate authors, fractional strength, isolates, edge threshold.
- Known-answer time-series: zero years, denominator excludes text-ineligible works, undefined shares are NaN.
- Known-answer term counts: repeated token counts only once per document.
- Streamlit AppTest: five tabs, year/signal/topic changes, edge threshold, reset, narrow selection.
- `python -m compileall -q app.py src scripts`.
- Streamlit server launched successfully in the build environment.

See test_results.txt for the latest actual test count and duration. AppTest is a simulation, not a browser or accessibility certification.

## Browser limitation
The cloud browser could not reach the build environment's 127.0.0.1:8510 (connection refused). No desktop/mobile screenshot inspection, dropdown contrast measurement, actual CSV browser download, or public deployment audit is claimed for this new project.

## Run manually before submission
1. At desktop 1440x900, tablet 768x1024, and phone 390x844, open all tabs. Check overflow, chart text, tab navigation, sidebar opening, legends, and long paper titles.
2. Change years to 2020–2023, select Calibration, choose a topic. Confirm all counts and tables refer to the same work selection with stated eligibility differences.
3. Force no-record and no-edge selections; verify useful messages rather than tracebacks.
4. Change graph threshold 1/2/5, author cap, focus author, ranking, and both layouts. Confirm descriptions distinguish selected graph from capped display.
5. Read two papers and verify abstract/title links. Compare table values with source records.
6. Download selected CSV and audit JSON; inspect actual filenames and row counts.
7. Use only keyboard to reach and change controls. Check focus visibility and understandable labels. Test with a screen reader where feasible.
8. Check text contrast >=4.5:1 and large-text contrast >=3:1. Color must not be the only way to identify lines/communities. Tabular alternatives must be reachable.
9. Start in a fresh virtual environment and run exactly the README commands. Record Python/OS and result.
10. After public deployment, repeat these checks on the actual URL; do not assume local success proves deployed behavior.

Record actual pass/fail evidence, screenshots if desired, and unresolved issues. Do not pre-fill unexecuted checks as PASS.
