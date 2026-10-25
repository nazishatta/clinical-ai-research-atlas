# Live interactive network — v1.5

Uses the instructor's Week 6 method: NetworkX + PyVis vis.js force physics. The live network is the default in the Collaboration Network tab; the alternative Plotly fixed network remains available. Circular layout deliberately does not move. Other charts keep their existing Plotly animation previews. Author/pair evidence controls remain unchanged.

Open **this** project folder in VS Code, not Downloads or previous versions.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m ensurepip --upgrade
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m streamlit run app.py
```

Go to Collaboration Network → Live moving network (PyVis) → Force-directed. Nodes should move and respond to dragging. Circular intentionally freezes positions.

**Compatibility:** This code uses `streamlit.components.v1.html`, matching the course demonstration. Streamlit displays a deprecation warning for this API in newer versions. This is a transitional implementation and should be migrated to Streamlit's supported custom-component approach before any later breaking removal.

**Validation:** Python compile and ZIP integrity were checked when packaged. Browser playback and full regression suite must still be verified locally. No scientific review decisions have been filled in.
