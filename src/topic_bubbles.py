"""Deterministic, accessible SVG bubble packing for NMF topic counts.

Circle areas are proportional to publication counts. This visual is a
five-category overview, not a semantic similarity map.
"""
from __future__ import annotations
import html
import json
import math

from src.palette import CATEGORICAL as COLORS


def _luminance(hex_colour: str) -> float:
    channels = [int(hex_colour.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def label_colour(fill: str) -> str:
    """Dark or white label text, whichever has more contrast on the fill."""
    lum = _luminance(fill)
    dark = (lum + 0.05) / (_luminance('#132234') + 0.05)
    white = 1.05 / (lum + 0.05)
    return '#132234' if dark >= white else '#FFFFFF'


def topic_bubbles_html(records: list[dict], colours: dict[str, str] | None = None) -> str:
    """``colours`` maps topic label to fill so a topic keeps one colour across charts."""
    clean = [(str(r["Topic"]), int(r["Works"])) for r in records if int(r["Works"]) > 0]
    clean.sort(key=lambda x: (-x[1], x[0]))
    if not clean:
        return '<p>No text-eligible documents in this selection.</p>'
    total = sum(count for _, count in clean)
    colour_of = lambda i, label: (colours or {}).get(label, COLORS[i % len(COLORS)])
    # Actual display area pi*r^2 is proportional to count.
    max_count = max(n for _, n in clean)
    radii = [90 * math.sqrt(n / max_count) for _, n in clean]
    # Start in a deterministic spiral then relax overlapping disks.
    n = len(clean)
    positions = [[0.0, 0.0]]
    for i in range(1, n):
        a = (i - 1) * math.pi * (3 - math.sqrt(5))
        d = 105 + 32 * math.sqrt(i)
        positions.append([d * math.cos(a), d * math.sin(a)])
    for _ in range(700):
        moved = False
        for i in range(n):
            for j in range(i + 1, n):
                dx = positions[j][0] - positions[i][0]
                dy = positions[j][1] - positions[i][1]
                dist = math.hypot(dx, dy)
                need = radii[i] + radii[j] + 9
                if dist < need:
                    if dist < 1e-8:
                        dx, dy, dist = 1, 0, 1
                    push = (need - dist) * .51
                    positions[i][0] -= push * dx / dist
                    positions[i][1] -= push * dy / dist
                    positions[j][0] += push * dx / dist
                    positions[j][1] += push * dy / dist
                    moved = True
        if not moved:
            break
    lowx = min(p[0] - r for p, r in zip(positions, radii))
    highx = max(p[0] + r for p, r in zip(positions, radii))
    lowy = min(p[1] - r for p, r in zip(positions, radii))
    highy = max(p[1] + r for p, r in zip(positions, radii))
    sc = min(760 / max(1, highx - lowx), 450 / max(1, highy - lowy))
    xoff = (960 - (highx - lowx) * sc) / 2 - lowx * sc
    yoff = (535 - (highy - lowy) * sc) / 2 - lowy * sc
    items = []
    for i, ((label, count), (x, y), rad) in enumerate(zip(clean, positions, radii)):
        cx, cy, rr = x * sc + xoff, y * sc + yoff, rad * sc
        pct = count / total * 100
        label_short = label if len(label) <= 27 else label[:25] + '…'
        fill = colour_of(i, label)
        ink = label_colour(fill)
        # Tooltip gives complete label and exact percentages, without risking SVG text overflow.
        circle = (
            f'<g class="bubble" style="transform-origin:{cx:.2f}px {cy:.2f}px;animation-delay:{i*.12:.2f}s">'
            f'<title>{html.escape(label)}: {count:,} works, {pct:.1f}% of topic-assigned works</title>'
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{rr:.2f}" fill="{fill}" fill-opacity="1" stroke="#EAF1FF" stroke-opacity=".65" stroke-width="2"/>'
            f'<text x="{cx:.2f}" y="{cy-5:.2f}" fill="{ink}" text-anchor="middle" font-weight="700" font-size="{max(11, min(17, rr*.21)):.1f}">{html.escape(label_short)}</text>'
            f'<text x="{cx:.2f}" y="{cy+19:.2f}" fill="{ink}" text-anchor="middle" font-size="14">{count:,} works · {pct:.1f}%</text>'
            '</g>'
        )
        items.append(circle)
    legend = ''.join(
        f'<li><span style="background:{colour_of(i, label)}"></span><b>{html.escape(label)}</b> · {count:,} works · {count/total*100:.1f}%</li>'
        for i, (label, count) in enumerate(clean)
    )
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
html,body{{margin:0;background:#101318;color:#e7ecf6;font-family:system-ui,-apple-system,sans-serif}}
main{{padding:10px 12px}}h2{{font-size:20px;margin:4px 0 6px}}p{{font-size:13px;color:#b8c5d5;margin:0 0 7px}}
svg{{display:block;width:100%;height:auto;max-height:555px;background:#141d2b;border:1px solid #354458;border-radius:12px}}
.bubble{{transform:scale(1)}} .ready .bubble{{animation:grow .95s cubic-bezier(.18,.85,.28,1.12) both}}
@keyframes grow{{from{{transform:scale(0);opacity:0}}to{{transform:scale(1);opacity:1}}}}
ul{{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:6px 18px;font-size:12px}}li span{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:7px}}
@media(prefers-reduced-motion:reduce){{.ready .bubble{{animation:none!important}}}}
</style></head><body><main><h2>NMF research topics · circle packing</h2>
<p>Circle <b>area</b> indicates assigned works; position does not encode semantic similarity. Hover for exact counts.</p>
<svg id="packing" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 535" role="img" aria-label="NMF topic distribution, circles sized by number of research papers">{''.join(items)}</svg>
<ul aria-label="Topic distribution as text">{legend}</ul>
</main><script>
const svg=document.getElementById('packing');
const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if(!reduce){{const watch=new IntersectionObserver((entries)=>{{if(entries.some(e=>e.isIntersecting)){{svg.classList.add('ready');watch.disconnect();}}}},{{threshold:.15}});watch.observe(svg);}}
</script></body></html>'''
