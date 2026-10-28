"""Reduced-motion-aware chart reveals with visible playback controls.

Each animated chart gets three keyboard-operable buttons above it:
Pause/Resume, Replay and Show final values, plus a polite live-region status.
When the operating system asks for reduced motion, the chart is shown in its
final state immediately and the playback buttons are disabled with a note.
The animation only clips chart marks; the data and the Plotly figure are unchanged.
"""
import json
import plotly.io as pio

CONTROL_LABELS = ('Pause', 'Replay', 'Show final values')

_SCRIPT = r"""
document.documentElement.style.overflow='hidden';
document.body.style.margin='0';
document.body.style.overflow='hidden';
const gd = document.getElementById('{plot_id}');
if (!gd) { console.warn('Atlas chart element missing'); } else {
const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
const isBar = gd.data.length > 0 && gd.data.every(t => t.type === 'bar');
const isHorizontal = isBar && gd.data.every(t => t.orientation === 'h');
const duration = 5000;
let visible = false, done = false, paused = false;
let frame = null, start = null, elapsed = 0;

// Controls ---------------------------------------------------------------
const bar = document.createElement('div');
bar.setAttribute('role','group');
bar.setAttribute('aria-label','Chart animation controls');
bar.style.cssText='display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:6px 8px;font:14px system-ui,-apple-system,sans-serif;background:#101318;color:#EDF2F7';
const css = document.createElement('style');
css.textContent='.atlas-btn{background:#1B222C;color:#EDF2F7;border:1px solid #8A99AD;border-radius:6px;padding:5px 12px;font:inherit;cursor:pointer}'+
  '.atlas-btn:hover{border-color:#56B4E9}.atlas-btn:focus-visible{outline:3px solid #F0E442;outline-offset:2px}'+
  '.atlas-btn[disabled]{opacity:.55;cursor:not-allowed}';
document.head.appendChild(css);
function button(label){ const b=document.createElement('button'); b.type='button'; b.className='atlas-btn'; b.textContent=label; bar.appendChild(b); return b; }
const pauseBtn = button('Pause');
const replayBtn = button('Replay');
const finalBtn = button('Show final values');
const status = document.createElement('span');
status.setAttribute('role','status'); status.setAttribute('aria-live','polite');
status.style.cssText='color:#CBD5E1;margin-left:4px';
bar.appendChild(status);
gd.parentNode.insertBefore(bar, gd);
pauseBtn.setAttribute('aria-pressed','false');

const targets = () => Array.from(gd.querySelectorAll(isBar ? '.barlayer' : '.scatterlayer, .barlayer'));
function restore(){ targets().forEach(el => { el.style.clipPath='none'; el.style.webkitClipPath='none'; }); }
function apply(progress){
  const pct = Math.max(0, 100 - progress*100);
  const clip = isBar && !isHorizontal ? `inset(${pct}% 0 0 0)` : `inset(0 ${pct}% 0 0)`;
  targets().forEach(el => { el.style.clipPath=clip; el.style.webkitClipPath=clip; });
}
function setStatus(text){ status.textContent=text; gd.dataset.motionState=text; }
function refresh(){
  if (reduced.matches){
    pauseBtn.disabled=true; replayBtn.disabled=true;
    setStatus('Showing final values (reduced motion is on)');
    return;
  }
  replayBtn.disabled=false;
  pauseBtn.disabled=done;
  pauseBtn.textContent = paused ? 'Resume' : 'Pause';
  pauseBtn.setAttribute('aria-pressed', paused ? 'true' : 'false');
  setStatus(done ? 'Showing final values' : (paused ? 'Paused' : 'Playing'));
}
function cancel(){ if(frame!==null){ cancelAnimationFrame(frame); frame=null; } }
function finish(){ cancel(); done=true; paused=false; elapsed=duration; restore(); refresh(); }
function tick(now){
  frame=null;
  if (done || paused) return;
  if (!visible || document.hidden || reduced.matches){ restore(); return; }
  if (start===null) start = now - elapsed;
  elapsed = now - start;
  if (elapsed >= duration){ finish(); return; }
  apply(elapsed/duration);
  frame=requestAnimationFrame(tick);
}
function play(){ if(!done && !paused && frame===null){ start=null; frame=requestAnimationFrame(tick); } }
function sync(){
  if (reduced.matches){ cancel(); done=true; restore(); refresh(); return; }
  if (visible && !document.hidden) play(); else { cancel(); }
  refresh();
}
pauseBtn.addEventListener('click',()=>{
  if (done || reduced.matches) return;
  paused=!paused;
  if (paused){ cancel(); } else { play(); }
  refresh();
});
replayBtn.addEventListener('click',()=>{
  if (reduced.matches) return;
  cancel(); done=false; paused=false; elapsed=0; start=null; apply(0); refresh(); play();
});
finalBtn.addEventListener('click',finish);
new IntersectionObserver(entries => { visible = entries.some(e => e.isIntersecting); sync(); },{threshold:0.15}).observe(gd);
document.addEventListener('visibilitychange',sync);
reduced.addEventListener('change',sync);
refresh();
}
"""


def animated_html(fig, auto_loop=False):
    """Progressive reveal with Pause/Resume, Replay and Show final values controls.

    ``auto_loop`` is accepted for backward compatibility and ignored: charts play
    once and then rest on their final values.
    """
    payload = json.loads(pio.to_json(fig))
    return pio.to_html(payload, include_plotlyjs=True, full_html=True,
                       config={"responsive": True, "displaylogo": False}, post_script=_SCRIPT)


def animated_network_html(fig):
    """Progressively reveal the fixed Plotly network, with the same controls.

    For physics-driven moving nodes, use the PyVis cluster view.
    """
    return animated_html(fig)
