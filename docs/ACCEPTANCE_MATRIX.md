# Assignment acceptance matrix

Status separates software implementation from scientific approval. These are checks against the supplied assignment, not invented professor weights.

| Requirement | Implemented evidence | Verification | Status |
|---|---|---|---|
| Real-world dataset | Frozen OpenAlex API pages, manifest, hashes, processed works | Source retrieval and hash tests | Implemented; relevance screening pending |
| Three complex modalities | Time-series, abstract text/NMF, coauthorship graph | Pure calculation tests and AppTest rendering | Implemented |
| Well-designed visuals | Zero-based counts, labeled shares, document-frequency bars, encoded graph + matrix | Automated rendering; manual browser QA still needed | Partial verification |
| Streamlit with widgets | Years, lexical signals, topics, paper browser, edge threshold, rank, author focus, cap, layout, downloads | AppTest filter/reset/empty/network tests | Implemented; browser verification pending |
| Multi-tab design | Five analysis tabs | AppTest asserts five tabs | Verified |
| Narrative | Question, dynamic coverage, snapshot findings, limitations | Text review against computed data | Implemented; owner interpretation approval pending |
| Accessibility | Colour-blind-safe palette with measured contrast, non-colour encodings, alt text and generated chart summaries, data tables, keyboard-operable Pause/Resume, Replay and Show final values controls, reduced-motion support, top-12 network labels | Palette contrast/CVD computed; alt text, motion controls (incl. reduced motion and keyboard focus) and reset checked in Chromium by asserting scripts; manual screen-reader and mobile checks outstanding | Improved; partial |
| Reproducible code/data | Pinned direct dependencies, raw snapshot, build scripts, checksums | Tests, compile, source/hash checks | Verified computationally; clean Mac install pending |
| Accompanying narrative | METHODS, DATA_AUDIT, findings in app, presentation guide | Owner review | Draft complete |
| Public deployment | Live at https://clinical-ai-research-atlas.streamlit.app/ | Live URL; complete browser audit pending | Deployed |

## Release gate
Complete human corpus and topic review, inspect representative papers, approve analytical claims, perform live browser accessibility/responsiveness checks, and publish through the user's own account. Do not label the application submission-certified or claim a guaranteed grade before these steps.
