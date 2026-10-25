# Clinical AI Atlas v1.3 + animation integration

This package merges the uploaded animation patch with the v1.3 Connected Explorer project. Open `clinical-ai-research-explorer` in VS Code (not the parent extraction folder).

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m ensurepip --upgrade
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m streamlit run app.py
```

Enable **Animate charts on entry** in the sidebar. A selectable chart displays its animated introduction **followed by the native Plotly chart**, which remains clickable for evidence selections. Nonselectable charts display the animated chart itself. The network remains native/stable. Animations may replay after unrelated Streamlit reruns; they are optional and off by default. Reduced motion prevents autoplay in the embedded animation. Verify playback and Streamlit selections in your own browser.

Scientific relevance review, NMF topic approval and live browser QA remain pending; do not present these as completed. Snapshot data and analyses are unchanged.
