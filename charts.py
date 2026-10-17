"""Plotly figures and small HTML helpers for the Streamlit dashboard."""
from __future__ import annotations

import math
import textwrap

import plotly.graph_objects as go

from engine import PALETTE

GRID = "rgba(136,146,166,0.25)"
_DARK = False


def set_dark(flag: bool):
    """Called by app.py so every figure matches the light/dark mode toggle."""
    global _DARK
    _DARK = bool(flag)


def themed(fig):
    fig.update_layout(
        font=dict(color="#e8eefb" if _DARK else "#14203a"),
        hoverlabel=dict(bgcolor="#101c3a", font=dict(color="#eaf0ff", size=13), bordercolor="#3a63b5"),
    )
    return fig


def _base(fig, height=460):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"),
    )
    return themed(fig)


def wrap(text, width=16):
    return "<br>".join(textwrap.wrap(text, width)) or text


def layout_pos(n):
    """Circular layout, first node at the top."""
    return [(math.cos(2 * math.pi * i / n - math.pi / 2), -math.sin(2 * math.pi * i / n - math.pi / 2))
            for i in range(n)]


def conflict_graph(d) -> go.Figure:
    n = d["n"]
    pos = layout_pos(n)
    cn, sz, fac, col, adj, kind = d["cn"], d["sz"], d["fac"], d["col"], d["adj"], d["kind"]
    fig = go.Figure()
    mx, my, mt = [], [], []
    for a, b, sh, fc in d["E"]:
        fig.add_trace(go.Scatter(
            x=[pos[a][0], pos[b][0]], y=[pos[a][1], pos[b][1]], mode="lines",
            line=dict(color="rgba(136,146,166,0.45)", width=min(3.0, 0.6 + sh * 0.3) if sh else 1.0,
                      dash="solid" if sh else "dash"),
            hoverinfo="skip"))
        mx.append((pos[a][0] + pos[b][0]) / 2)
        my.append((pos[a][1] + pos[b][1]) / 2)
        txt = f"<b>{cn(a)} ↔ {cn(b)}</b>"
        if d["course_of"][a] == d["course_of"][b]:
            txt += "<br>Theory and lab of the same course"
        elif sh:
            txt += f"<br>{sh} student(s) take both"
        if fc:
            txt += f"<br>Same teacher (F{fac[a] + 1})"
        mt.append(txt + "<br>Cannot share a time slot")
    fig.add_trace(go.Scatter(x=mx, y=my, mode="markers", marker=dict(size=8, opacity=0),
                             hovertext=mt, hoverinfo="text"))
    dm = max([len(a) for a in adj] + [1])
    hover = []
    for i in range(n):
        r = d["room_of"].get(i)
        room = f"{d['rooms'][r]['n']} (capacity {d['rooms'][r]['cap']})" if r is not None else "none available"
        hover.append(f"<b>{cn(i)}</b> ({kind[i]}) · {sz[i]} students<br>Teacher F{fac[i] + 1}<br>"
                     f"Slot {col[i] + 1}<br>Room: {room}<br>"
                     f"Clashes with {len(adj[i])}: {', '.join(cn(x) for x in adj[i]) or 'none'}")
    fig.add_trace(go.Scatter(
        x=[p[0] for p in pos], y=[p[1] for p in pos], mode="markers",
        marker=dict(size=[20 + len(adj[i]) / dm * 10 for i in range(n)],
                    color=[PALETTE[col[i] % len(PALETTE)] for i in range(n)],
                    symbol=["circle" if kind[i] == "Theory" else "diamond" for i in range(n)],
                    line=dict(color="rgba(255,255,255,0.7)", width=2)),
        hovertext=hover, hoverinfo="text"))
    tpos = []
    for x, y in pos:
        tpos.append("top center" if y > 0.8 else "bottom center" if y < -0.8
                    else "middle right" if x > 0 else "middle left")
    fig.add_trace(go.Scatter(
        x=[p[0] * 1.09 for p in pos], y=[p[1] * 1.09 for p in pos], mode="text",
        text=[wrap(cn(i)) for i in range(n)], textposition=tpos, textfont=dict(size=10),
        hoverinfo="skip"))
    fig = _base(fig, 580)
    fig.update_layout(xaxis=dict(visible=False, range=[-1.95, 1.95]),
                      yaxis=dict(visible=False, range=[-1.45, 1.45], scaleanchor="x"))
    return fig


def mst_map(d) -> go.Figure:
    pts, mst = d["pts"], d["mst"]
    used = {(a, b) for a, b, _ in mst}
    fig = go.Figure()
    for a, b, w in d["ed"]:
        if (a, b) in used:
            continue
        fig.add_trace(go.Scatter(
            x=[pts[a][0], pts[b][0]], y=[-pts[a][1], -pts[b][1]], mode="lines",
            line=dict(color="rgba(136,146,166,0.35)", width=1, dash="dot"),
            hoverinfo="text", hovertext=f"B{a + 1}–B{b + 1}: {w:.1f} units (not used)"))
    for i, (a, b, w) in enumerate(mst, 1):
        fig.add_trace(go.Scatter(
            x=[pts[a][0], pts[b][0]], y=[-pts[a][1], -pts[b][1]], mode="lines",
            line=dict(color="#D9A441", width=5), hoverinfo="text",
            hovertext=f"<b>B{a + 1}–B{b + 1}</b><br>Cost {w:.1f}<br>Cable #{i}"))
    fig.add_trace(go.Scatter(
        x=[(pts[a][0] + pts[b][0]) / 2 for a, b, _ in mst],
        y=[-(pts[a][1] + pts[b][1]) / 2 + 12 for a, b, _ in mst], mode="text",
        text=[f"{w:.1f}" for *_, w in mst], textfont=dict(size=12), hoverinfo="skip"))
    nb = {i: [] for i in range(len(pts))}
    for a, b, w in mst:
        nb[a].append(f"B{b + 1} ({w:.1f})")
        nb[b].append(f"B{a + 1} ({w:.1f})")
    fig.add_trace(go.Scatter(
        x=[p[0] for p in pts], y=[-p[1] for p in pts], mode="markers+text",
        text=[f"B{i + 1}" for i in range(len(pts))], textfont=dict(color="white", size=11),
        marker=dict(size=34, color="#1F3864", line=dict(color="#9dbbff", width=2)),
        hovertext=[f"<b>B{i + 1}</b><br>Cabled to: {', '.join(nb[i])}" for i in range(len(pts))],
        hoverinfo="text"))
    return _base(fig, 420)


def histogram(d) -> go.Figure:
    ks = sorted(d["hist"])
    fig = go.Figure(go.Bar(
        x=ks, y=[d["hist"][k] for k in ks],
        marker_color=["#34b97e" if k == 0 else "#c0504d" for k in ks],
        hovertemplate="%{x} clashes<br>%{y} random timetables<extra></extra>"))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(title="Number of clashes", dtick=1),
                      yaxis=dict(title="Random timetables", gridcolor=GRID))
    return themed(fig)


def hbar(labels, values, colors, texts=None, height=None) -> go.Figure:
    fig = go.Figure(go.Bar(
        y=labels, x=values, orientation="h", marker_color=colors,
        text=texts or values, textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{text}<extra></extra>"))
    fig.update_layout(height=height or 40 + 34 * len(labels), margin=dict(l=10, r=50, t=5, b=5),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(visible=False), yaxis=dict(autorange="reversed", automargin=True))
    return themed(fig)


def board_html(d) -> str:
    """Timetable board: columns = slots, rows = rooms (classrooms first, then labs)."""
    slots, rooms, sz, fac = d["slots"], d["rooms"], d["sz"], d["fac"]
    cn, room_of, kind = d["cn"], d["room_of"], d["kind"]
    cols = f"92px repeat({slots}, minmax(150px, 1fr))"
    h = [f'<div style="overflow-x:auto;padding-bottom:6px"><div style="display:grid;grid-template-columns:{cols};'
         f'gap:8px;min-width:{92 + slots * 158}px">', "<div></div>"]
    for s, cs in enumerate(d["slot_members"]):
        h.append(f'<div style="background:{PALETTE[s % len(PALETTE)]};color:#fff;border-radius:12px;padding:10px 12px">'
                 f'<b>Slot {s + 1}</b><br><small>{len(cs)} session(s) · {sum(sz[x] for x in cs)} students</small></div>')
    for j, r in enumerate(rooms):
        label = "Lab" if r["type"] == "Lab" else "Classroom"
        h.append(f'<div style="display:flex;flex-direction:column;justify-content:center"><b>{r["n"]}</b>'
                 f'<small style="opacity:.75">{label} · {r["cap"]} seats</small></div>')
        for s, cs in enumerate(d["slot_members"]):
            x = next((y for y in cs if room_of.get(y) == j), None)
            if x is None:
                h.append('<div style="border:1.5px dashed rgba(136,146,166,.5);border-radius:12px;'
                         'display:grid;place-items:center;min-height:92px;opacity:.6;font-size:12px">free</div>')
            else:
                pct = min(100, sz[x] / r["cap"] * 100)
                badge = ('<span style="float:right;background:rgba(255,255,255,.25);border-radius:8px;'
                         'padding:0 7px;font-size:10px;letter-spacing:.05em">LAB</span>') if kind[x] == "Lab" else ""
                h.append(f'<div class="bcell" title="{cn(x)} in {r["n"]}, Slot {s + 1}: {sz[x]} students, room {pct:.0f}% full" '
                         f'style="background:{PALETTE[s % len(PALETTE)]};color:#fff;border-radius:12px;padding:10px 12px;'
                         f'min-height:92px;display:flex;flex-direction:column;justify-content:space-between">'
                         f'<div style="font:700 14px/1.25 Georgia,serif">{cn(x)}{badge}</div>'
                         f'<div><div style="font-size:12px;margin-top:4px">{sz[x]} students · F{fac[x] + 1}</div>'
                         f'<div style="height:5px;border-radius:4px;background:rgba(255,255,255,.3);margin-top:6px">'
                         f'<div style="height:100%;width:{pct}%;background:#fff;border-radius:4px"></div></div></div></div>')
    h.append("</div></div>")
    return "".join(h)


def chips_html(d, f) -> str:
    cs = sorted([x for x in range(d["n"]) if d["fac"][x] == f], key=lambda a: d["col"][a])
    return "".join(
        f'<span class="chip" title="{d["cn"](x)} runs in Slot {d["col"][x] + 1}" style="display:inline-block;'
        f'border-left:5px solid {PALETTE[d["col"][x] % len(PALETTE)]};background:rgba(136,146,166,.15);'
        f'border-radius:8px;padding:4px 10px;margin:3px 6px 3px 0;font-size:13px">'
        f'{d["cn"](x)} · Slot {d["col"][x] + 1}</span>' for x in cs) or "<small>No sessions</small>"
