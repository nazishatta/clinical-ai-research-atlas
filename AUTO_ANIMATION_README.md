# Automatic animation fix

- All four supported bar/line charts animate automatically on entering view.
- Coauthorship nodes now animate from a compact starting layout into their deterministic final positions; edges move with nodes.
- Animation is enabled on first launch. Uncheck **Animate charts on entry** to show static native Plotly charts.
- Controls: Replay arrival, Pause/Resume, Show final values.
- Reduced-motion preference bypasses playback.
- For native evidence-selection charts, the animated preview remains above the native selectable Plotly chart.
- Network animation is **not** an interactive force physics simulation and does not imply spatial distance.
- This bundle has not been browser-verified on your Mac; test animation and native selections on localhost.

## Install
Extract in its own folder, then from the `clinical-ai-research-explorer` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m ensurepip --upgrade
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m streamlit run app.py
```

Do not copy this bundle's `app.py` over a separate working version. This is a full project candidate built from the integrated v1.3 baseline. Scientific human review is still pending.
