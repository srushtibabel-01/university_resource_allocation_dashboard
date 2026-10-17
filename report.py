"""PDF report builder (reportlab + matplotlib)."""
from __future__ import annotations

import io
import math
import textwrap
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from engine import COURSES, FIELDS, PALETTE

NAVY = colors.HexColor("#1F3864")


def _table(head, rows, widths=None):
    st = getSampleStyleSheet()["BodyText"]
    st.fontSize = 8
    st.leading = 10
    data = [head] + [[Paragraph(str(x), st) for x in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8), ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _fig_img(fig, w_mm=170):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    img = Image(buf)
    ratio = img.imageHeight / img.imageWidth
    w = w_mm * mm
    if w * ratio > 110 * mm:  # keep tall figures (e.g. 2 nodes) inside the page frame
        w = 110 * mm / ratio
    img.drawWidth, img.drawHeight = w, w * ratio
    return img


def _graph_fig(d):
    n = d["n"]
    fig, ax = plt.subplots(figsize=(7.5, 6))
    pos = [(math.cos(2 * math.pi * i / n - math.pi / 2), -math.sin(2 * math.pi * i / n - math.pi / 2))
           for i in range(n)]
    for a, b, sh, _ in d["E"]:
        ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]], color="#8892a6", lw=0.4,
                ls="-" if sh else "--", zorder=1, alpha=0.6)
    for i, (x, y) in enumerate(pos):
        ax.scatter(x, y, s=130, marker="o" if d["kind"][i] == "Theory" else "D",
                   color=PALETTE[d["col"][i] % len(PALETTE)], zorder=2, edgecolor="white")
        ha = "left" if x > 0.2 else "right" if x < -0.2 else "center"
        va = "bottom" if abs(x) <= 0.2 and y > 0 else "top" if abs(x) <= 0.2 else "center"
        ax.text(x * 1.1, y * 1.1, textwrap.fill(d["cn"](i), 18), fontsize=5.5, ha=ha, va=va)
    ax.set_xlim(-1.9, 1.9)
    ax.set_ylim(-1.35, 1.35)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig


def _mst_fig(d):
    fig, ax = plt.subplots(figsize=(6, 3.8))
    pts = d["pts"]
    for a, b, w in d["mst"]:
        ax.plot([pts[a][0], pts[b][0]], [-pts[a][1], -pts[b][1]], color="#D9A441", lw=3, zorder=1)
        ax.text((pts[a][0] + pts[b][0]) / 2, -(pts[a][1] + pts[b][1]) / 2 + 8, f"{w:.1f}",
                fontsize=7, ha="center")
    for i, (x, y) in enumerate(pts):
        ax.scatter(x, -y, s=420, color="#1F3864", zorder=2)
        ax.text(x, -y, f"B{i + 1}", color="white", ha="center", va="center", fontsize=7, weight="bold")
    ax.set_aspect("equal")
    ax.axis("off")
    return fig


def build_pdf(d: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title="University Resource Optimisation Report")
    ss = getSampleStyleSheet()
    h1 = ss["Title"]
    h1.textColor = NAVY
    h2 = ss["Heading2"]
    h2.textColor = NAVY
    body = ss["BodyText"]
    S = []
    S += [Paragraph("University Resource Optimisation", h1),
          Paragraph("Smart timetabling, room allocation and campus network design", body),
          Paragraph("Generated: " + datetime.now().strftime("%d %b %Y, %H:%M"), body), Spacer(1, 8)]

    S += [Paragraph("1. Input Parameters", h2),
          _table(["Parameter", "Value", "Meaning"],
                 [("Courses", len(COURSES), "Fixed list: " + ", ".join(COURSES) + ". Each has a theory and a lab session.")]
                 + [(l, d["P"][k], h) for k, l, _, _, _, h in FIELDS],
                 [45 * mm, 18 * mm, 111 * mm])]

    verdict = ("CERTIFIED: schedule is conflict-free, fully allocated and within available slots"
               if d["ok"] else "WARNING: some constraints are not satisfied (see checks below)")
    S += [Paragraph("2. Result Summary", h2),
          Paragraph(f'<font color="{"#2e8b57" if d["ok"] else "#c0392b"}"><b>{verdict}</b></font>', body),
          Spacer(1, 4),
          _table(["Metric", "Value"], [
              ("Sessions (theory + lab)", f'{d["n"]} ({d["c"]} theory + {d["n"] - d["c"]} lab)'), ("Conflict edges", len(d["E"])),
              ("Time slots needed / available", f'{d["slots"]} / {d["P"]["t"]}'),
              ("Sessions placed in rooms", f'{len(d["room_of"])} / {d["n"]}'),
              ("Seats filled / needed", f'{d["seat_got"]} / {d["seat_need"]}'),
              ("MST network cost", f'{d["mc"]:.1f} (full cabling {d["full"]:.1f})')],
                 [80 * mm, 94 * mm])]

    S += [Paragraph("3. Correctness Verification", h2),
          _table(["Result", "Check", "Detail"],
                 [("PASS" if p else "FAIL", t, x) for p, t, x in d["ck"]],
                 [16 * mm, 78 * mm, 80 * mm])]

    S += [Paragraph("4. Conflict Graph and Time-Slot Colouring", h2), _fig_img(_graph_fig(d), 140),
          Paragraph("Circle = theory, diamond = lab, colour = time slot, solid edge = shared students, dashed = same faculty.", body)]

    rows = []
    for s, cs in enumerate(d["slot_members"]):
        for x in cs:
            r = d["room_of"].get(x)
            rows.append((f"Slot {s + 1}", COURSES[d["course_of"][x]], d["kind"][x], d["sz"][x], f"F{d['fac'][x] + 1}",
                         f'{d["rooms"][r]["n"]} (cap {d["rooms"][r]["cap"]})' if r is not None else "NO ROOM"))
    S += [Paragraph("5. Timetable and Room Allocation", h2),
          _table(["Slot", "Course", "Type", "Students", "Faculty", "Room"], rows)]

    pairs = d["pairs"]
    S += [Paragraph("6. Counting and Probability", h2), _table(["Quantity", "Value", "Method"], [
        (f'Possible timetables ({d["P"]["t"]}^{d["n"]})', f'about 10^{d["log_n"]:.1f}', "Counting principle"),
        ("Session pairs / conflicting pairs", f'{pairs} / {len(d["E"])}', "Set intersection"),
        ("Expected clashes, random timetable", f'{len(d["E"]) / d["P"]["t"]:.2f}', "Linearity of expectation"),
        ("Chance random timetable is clash-free", f'{d["free"] / d["trials"] * 100:.2f}%',
         f'Monte Carlo, {d["trials"]} trials'),
        ("Clashes in optimised timetable", "0", "Graph colouring")])]

    S += [Paragraph("7. Campus Network (Minimum Spanning Tree)", h2), _fig_img(_mst_fig(d), 140),
          Paragraph(f'MST cost {d["mc"]:.1f} vs full cabling {d["full"]:.1f} units: saving '
                    f'{(1 - d["mc"] / d["full"]) * 100:.0f}%.', body)]

    S += [Paragraph("8. Seating Capacity (Max-Flow Min-Cut)", h2),
          _table(["Slot", "Seats needed", "Seated (max-flow)", "Full rooms (min-cut)", "Status"], d["fr"])]

    def footer(canvas, doc_):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(A4[0] / 2, 10 * mm, f"University Resource Optimisation | Page {doc_.page}")

    doc.build(S, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
