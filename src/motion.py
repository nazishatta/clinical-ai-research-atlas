"""Automatic, reduced-motion-aware visual chart reveals for the Atlas."""
import json
import plotly.io as pio


def animated_html(fig, auto_loop=False):
    """Create a one-time progressive reveal, without playback buttons.

    The graph and data are unchanged; reveal is presentation only. Native Plotly
    selection chart is rendered separately by app.py where required.
    """
    code = r"""
const gd = document.getElementById('{plot_id}');
if (!gd) { console.warn('Atlas chart element missing'); } else {
const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
const isBar = gd.data.length > 0 && gd.data.every(t => t.type === 'bar');
const isHorizontal = isBar && gd.data.every(t => t.orientation === 'h');
const duration = 5000;
let visible = false;
let stopped = false;
let frame = null;
let start = null;
const targets = () => Array.from(gd.querySelectorAll(isBar ? '.barlayer' : '.scatterlayer, .barlayer'));
function restore() {
  targets().forEach(el => { el.style.clipPath='none'; el.style.webkitClipPath='none'; });
}
function apply(progress) {
  const pct = Math.max(0, 100 - progress*100);
  // Hide/reveal chart marks rather than repeatedly recreating Plotly traces.
  const clip = isBar && !isHorizontal ? `inset(${pct}% 0 0 0)` : `inset(0 ${pct}% 0 0)`;
  targets().forEach(el => { el.style.clipPath=clip; el.style.webkitClipPath=clip; });
}
function tick(now) {
  frame = null;
  if (!visible || document.hidden || reduced.matches || stopped) { restore(); return; }
  if (start === null) start=now;
  const elapsed = now - start;
  if (elapsed >= duration) {
    stopped = true;
    restore();
    return;
  }
  apply(elapsed / duration);
  frame = requestAnimationFrame(tick);
}
function sync() {
  if (reduced.matches) { if(frame!==null)cancelAnimationFrame(frame);frame=null;restore();return; }
  if (visible && !document.hidden) {
    if(frame===null && !stopped) {start=null;frame=requestAnimationFrame(tick);}
  } else {if(frame!==null)cancelAnimationFrame(frame);frame=null;restore();}
}
const observer = new IntersectionObserver(entries => {
  visible=entries.some(e => e.isIntersecting);
  sync();
},{threshold:0.15});
observer.observe(gd);
document.addEventListener('visibilitychange',sync);
reduced.addEventListener('change',sync);
gd.on('plotly_afterplot', () => {
  if(visible && frame!==null && start!==null) {
    // Filter changes and redraws restore the current reveal on the next frame.
  }
});
}
"""
    payload=json.loads(pio.to_json(fig))
    return pio.to_html(payload,include_plotlyjs=True,full_html=True,
                       config={"responsive":True,"displaylogo":False},post_script=code)


def animated_network_html(fig):
    """Progressively reveal the fixed Plotly network automatically.

    For actual physics-driven moving nodes, use the PyVis cluster view.
    """
    return animated_html(fig)
