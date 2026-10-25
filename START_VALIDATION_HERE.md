# Clinical AI Research Atlas — focused professor-aligned refinement

This revision preserves the frozen OpenAlex corpus, NMF outputs, graph metrics and evidence filters from v1.5. It changes only the live-network presentation and initial animation control.

## Changes
- In force-directed PyVis mode, labels are hidden initially to prevent collisions during movement; all author names remain in node hover titles.
- Users may enable **Show all author names** if desired.
- The sidebar animation opt-in checkbox is removed; existing chart previews are enabled by default, subject to the existing reduced-motion handling and replay controls.
- The existing author/pair dropdowns and evidence downloads remain available as alternatives to pointing and dragging.

## Start in VS Code (Mac)
Open the `clinical-ai-research-explorer` directory, not its parent.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m ensurepip --upgrade
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m streamlit run app.py
```

## Manual acceptance checks
1. Visit Collaboration Network in a fresh browser session; confirm PyVis + Force-directed is selected and the nodes move briefly.
2. Confirm author labels are not crowded by default; hover a node to read the name, selected degree, and paper count.
3. Check the Show all author names checkbox; names should appear.
4. Change to Circular; verify positions are fixed by design.
5. Use author and author-pair dropdowns and verify the exported paper list.
6. Verify the Year, Topic, and Term filters still reconcile with evidence downloads.
7. Verify chart animation starts automatically and reduced-motion preferences are respected.

## Outstanding research approvals
The manual 95-paper relevance screen, NMF interpretation review, 2025 spike investigation, and browser/deployment acceptance checks are **not certified** by this update. Do not claim final scientific validation until those are completed.

## Verification bounds
Source compilation passed here. Full app tests cannot run in this container without installing the complete requirements. Run the full test suite on your Mac and retain its output.
