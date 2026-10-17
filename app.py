"""University Resource Optimisation - Streamlit dashboard.

Run with:  streamlit run app.py
"""
import html

import pandas as pd
import streamlit as st

import charts
from engine import COURSES, DEFAULTS, FIELDS, PALETTE, generate
from report import build_pdf

st.set_page_config(page_title="University Resource Optimisation", page_icon="🎓", layout="wide")

# ---------------------------------------------------------------- state
for k, v in DEFAULTS.items():
    st.session_state.setdefault(f"in_{k}", v)
st.session_state.setdefault("dark", False)
if "res" not in st.session_state:
    st.session_state.res = generate(dict(DEFAULTS))
    st.session_state.sample = True

DARK = st.session_state.dark
charts.set_dark(DARK)

# ------------------------------------------------------------------ CSS
LIGHT_VARS = "--ink:#14203a;--mut:#5d6a82;--line:#e0e7f3;--soft:#f0f4fb;--card:#ffffff;--ac:#1F3864;"
DARK_VARS = "--ink:#e8eefb;--mut:#9fb0cf;--line:#24335a;--soft:#192850;--card:#13203f;--ac:#9dbbff;"

BASE_CSS = f"""
:root{{{LIGHT_VARS}}}
.hero{{background:linear-gradient(120deg,#122347,#1F3864 55%,#2f5aa8);padding:26px 28px;border-radius:18px;margin-bottom:14px}}
.hero .tag{{background:#D9A441;color:#1b2540;font-weight:700;font-size:11px;letter-spacing:.08em;text-transform:uppercase;padding:4px 11px;border-radius:20px}}
.hero h1{{margin:10px 0 4px;font-family:Georgia,serif;font-size:34px;color:#fff!important;padding:0}}
.hero p{{margin:0;color:#cadcfc!important}}
.verdict{{border-radius:16px;padding:18px 22px;margin:8px 0 14px;transition:.15s;cursor:help}}
.verdict:hover{{transform:translateY(-2px)}}
.verdict,.verdict h3,.verdict li,.verdict b{{color:#fff!important}}
.verdict.good{{background:linear-gradient(135deg,#1a8057,#34b97e)}}
.verdict.bad{{background:linear-gradient(135deg,#b3342a,#e8604f)}}
.verdict h3{{margin:0 0 4px;font-family:Georgia,serif}}
.note-box{{background:var(--soft);border:1px solid var(--line);border-left:5px solid #D9A441;border-radius:12px;padding:12px 16px;margin-bottom:12px;color:var(--ink);font-size:14px}}
.warn-box{{background:rgba(192,57,43,.12);border:1px solid #c0392b;border-radius:12px;padding:10px 14px;margin:10px 0;color:var(--ink)}}
.vs{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px}}
.vs div{{border-radius:14px;padding:16px;background:linear-gradient(135deg,#b3342a,#e8604f);text-align:center;cursor:help;transition:.15s}}
.vs div:hover{{transform:translateY(-2px)}}
.vs div.g{{background:linear-gradient(135deg,#1a8057,#34b97e)}}
.vs div,.vs b,.vs span{{color:#fff!important}}
.vs b{{display:block;font:700 28px Georgia,serif}}
.sg{{border-left:5px solid var(--c);background:var(--soft);border-radius:10px;padding:8px 12px;margin-bottom:8px;font-size:13px;color:var(--ink);cursor:help;transition:.15s}}
.sg:hover{{transform:translateX(3px)}}
.tbl-wrap{{overflow-x:auto;margin-bottom:6px}}
table.tbl{{width:100%;border-collapse:collapse;font-size:13px;color:var(--ink)}}
table.tbl th{{background:var(--soft);color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.05em;text-align:left;padding:9px 10px;border-bottom:1px solid var(--line)}}
table.tbl td{{padding:9px 10px;border-bottom:1px solid var(--line)}}
table.tbl tr:hover td{{background:var(--soft)}}
table.tbl tbody tr{{cursor:pointer}}
.ubar{{display:inline-block;width:80px;height:7px;background:var(--line);border-radius:6px;overflow:hidden;vertical-align:middle;margin-right:8px}}
.ubar i{{display:block;height:100%;background:#3a63b5}}
.bcell{{cursor:pointer;transition:.15s}} .bcell:hover{{transform:translateY(-2px);box-shadow:0 6px 14px rgba(0,0,0,.25)}}
.chip{{cursor:help;color:var(--ink)}}
/* hover pointers on every interactive Streamlit control */
button,[role="tab"],[data-testid="stBaseButton-primary"],[data-testid="stBaseButton-secondary"],
[data-testid="stNumberInput"] button,[data-testid="stExpander"] summary,
[data-testid="stToggle"] label,[data-testid="stToggle"] div,[data-baseweb="tab"]{{cursor:pointer!important}}
[data-testid="stMetric"]{{cursor:help;transition:.15s;border-radius:12px;padding:6px 8px}}
[data-testid="stMetric"]:hover{{background:var(--soft)}}
[data-testid="stBaseButton-primary"]:hover,[data-testid="stBaseButton-secondary"]:hover{{transform:translateY(-1px)}}
[data-testid="stBaseButton-secondary"]:disabled{{cursor:not-allowed!important}}
.js-plotly-plot .nsewdrag{{cursor:crosshair}}
"""

DARK_CSS = f"""
:root{{{DARK_VARS}}}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{{background:#0b1429!important;color:#e8eefb}}
[data-testid="stHeader"]{{background:rgba(11,20,41,.85)!important}}
[data-testid="stHeader"] *{{color:#e8eefb!important}}
[data-testid="stSidebar"],[data-testid="stSidebar"]>div{{background:#13203f!important}}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] h1,[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,[data-testid="stMarkdownContainer"] h4,
[data-testid="stCaptionContainer"],[data-testid="stWidgetLabel"] p,[data-testid="stWidgetLabel"] label,
[data-testid="stMetricLabel"] *,[data-testid="stMetricValue"],[data-testid="stHeading"] *,
[data-testid="stExpander"] summary *,[data-testid="stToggle"] p,h1,h2,h3{{color:#e8eefb!important}}
[data-testid="stCaptionContainer"] *{{color:#9fb0cf!important}}
.hero h1{{color:#fff!important}} .hero p{{color:#cadcfc!important}} .hero .tag{{color:#1b2540!important}}
.verdict,.verdict *,.vs *{{color:#fff!important}}
[data-baseweb="input"],[data-baseweb="base-input"],[data-testid="stNumberInputContainer"]{{background:#192850!important;border-color:#24335a!important}}
input,[data-testid="stNumberInput"] input{{background:#192850!important;color:#e8eefb!important;-webkit-text-fill-color:#e8eefb!important}}
[data-testid="stNumberInput"] button{{background:#192850!important;color:#e8eefb!important}}
[data-testid="stNumberInput"] button svg{{fill:#e8eefb!important}}
[data-testid="stBaseButton-secondary"]{{background:#192850!important;border:1px solid #24335a!important;color:#e8eefb!important}}
[data-testid="stBaseButton-secondary"] *{{color:#e8eefb!important}}
[data-testid="stBaseButton-secondary"]:disabled{{opacity:.5}}
[data-testid="stBaseButton-primary"]{{background:linear-gradient(135deg,#3a63b5,#2f5aa8)!important;border:0!important}}
[data-testid="stBaseButton-primary"] *{{color:#fff!important}}
[data-baseweb="tab-list"]{{border-color:#24335a!important}}
[data-baseweb="tab"]{{color:#9fb0cf!important}} [data-baseweb="tab"][aria-selected="true"]{{color:#fff!important}}
[data-baseweb="tab-highlight"]{{background:#D9A441!important}}
[data-testid="stExpander"]{{border-color:#24335a!important;background:#13203f!important}}
[data-testid="stTooltipContent"],[data-baseweb="tooltip"] div,[data-baseweb="popover"] div{{background:#101c3a!important;color:#eaf0ff!important}}
[data-testid="stToggle"] p{{color:#e8eefb!important}}
hr{{border-color:#24335a!important}}
"""

st.markdown(f"<style>{BASE_CSS}{DARK_CSS if DARK else ''}</style>", unsafe_allow_html=True)

st.markdown("""
<div class="hero"><span class="tag">Discrete Mathematics Project</span>
<h1>University Resource Optimisation</h1>
<p>Smart timetabling · Room allocation · Campus network design</p></div>
""", unsafe_allow_html=True)


# ------------------------------------------------------------- helpers
def current_params():
    return {k: int(st.session_state[f"in_{k}"]) for k, *_ in FIELDS}


def on_generate():
    st.session_state.res = generate(current_params())
    st.session_state.sample = False


@st.cache_data(show_spinner="Building PDF…")
def pdf_bytes(items: tuple) -> bytes:
    return build_pdf(generate(dict(items)))


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")  # utf-8-sig so Excel opens it cleanly


def html_table(df: pd.DataFrame) -> str:
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    rows = []
    for _, r in df.iterrows():
        cells = []
        for col, v in r.items():
            if pd.isna(v):
                cells.append("<td>–</td>")
            elif str(col).endswith("usage %"):
                cells.append(f'<td><span class="ubar"><i style="width:{min(100, v)}%"></i></span>{int(v)}%</td>')
            else:
                cells.append(f"<td>{html.escape(str(v))}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def show_table(df: pd.DataFrame, csv_name: str, key: str):
    st.markdown(html_table(df), unsafe_allow_html=True)
    st.download_button("⬇ Download this table (CSV)", csv_bytes(df), file_name=csv_name, mime="text/csv",
                       key=key, help="Saves the table above as a CSV file you can open in Excel.")


def kpis(items):
    cols = st.columns(len(items))
    for col, (v, lbl, tip) in zip(cols, items):
        col.metric(lbl, v, help=tip)


def timetable_df(d):
    rows = []
    for s, m in enumerate(d["slot_members"]):
        for x in m:
            r = d["room_of"].get(x)
            rows.append({"Slot": f"Slot {s + 1}", "Course": COURSES[d["course_of"][x]], "Type": d["kind"][x],
                         "Students": d["sz"][x],
                         "Teacher": f"F{d['fac'][x] + 1}",
                         "Room": d["rooms"][r]["n"] if r is not None else "No room",
                         "Room capacity": d["rooms"][r]["cap"] if r is not None else None,
                         "Room usage %": round(d["sz"][x] / d["rooms"][r]["cap"] * 100) if r is not None else None})
    return pd.DataFrame(rows)


def mst_df(d):
    run, rows = 0.0, []
    for i, (a, b, w) in enumerate(d["mst"], 1):
        run += w
        rows.append({"Step": i, "Cable": f"B{a + 1} – B{b + 1}", "Cost": round(w, 1), "Running total": round(run, 1)})
    return pd.DataFrame(rows)


def flow_df(d):
    return pd.DataFrame(d["fr"], columns=["Slot", "Seats needed", "Seated (max-flow)", "Full rooms (min-cut)", "Status"])


def count_df(d):
    P, n = d["P"], d["n"]
    dens = len(d["E"]) / d["pairs"] * 100
    return pd.DataFrame([
        (f'Possible timetables ({P["t"]}^{n})', f'about 10^{d["log_n"]:.1f}', "Counting principle"),
        ("Session pairs / conflicting pairs", f'{d["pairs"]} / {len(d["E"])} ({dens:.0f}%)', "Set intersection"),
        ("Expected clashes in a random timetable", f'{len(d["E"]) / P["t"]:.2f}', "Linearity of expectation"),
        ("Chance a random timetable is clash-free", f'{d["free"] / d["trials"] * 100:.2f}%',
         f'Monte Carlo, {d["trials"]} trials'),
        ("Clashes in the optimised timetable", "0", "Graph colouring")], columns=["Quantity", "Value", "Method"])


# -------------------------------------------------------------- sidebar
with st.sidebar:
    st.toggle("🌙 Dark mode", key="dark", help="Switch between the light and dark theme.")
    st.header("Input Data")
    st.caption(f"📚 {len(COURSES)} courses (fixed list) · each has a theory session and a lab session")
    for k, label, _, lo, hi, helptext in FIELDS:
        st.number_input(f"{label} ({lo}–{hi})", min_value=lo, max_value=hi, step=1,
                        key=f"in_{k}", help=helptext)
    st.button("Generate & Optimise", type="primary", width="stretch", on_click=on_generate,
              help="Runs the whole pipeline again with the values above.")
    if st.session_state.sample:
        st.button("⬇ Download PDF Report", disabled=True, width="stretch",
                  help="Generate your own results first.", key="pdf_off")
        st.button("⬇ Download CSV (timetable)", disabled=True, width="stretch",
                  help="Generate your own results first.", key="csv_off")
    else:
        Pcur = st.session_state.res["P"]
        st.download_button("⬇ Download PDF Report", pdf_bytes(tuple(sorted(Pcur.items()))),
                           file_name="University_Resource_Optimisation_Report.pdf",
                           mime="application/pdf", width="stretch",
                           help="Full PDF report: inputs, results, graphs and checks.")
        st.download_button("⬇ Download CSV (timetable)", csv_bytes(timetable_df(st.session_state.res)),
                           file_name="timetable.csv", mime="text/csv", width="stretch",
                           help="The final timetable (slot, course, theory/lab, students, teacher, room) as a CSV file.")
    st.caption("Students are enrolled randomly and room capacities are generated automatically.")

d = st.session_state.res
P, c, cn, n = d["P"], d["c"], d["cn"], d["n"]
if st.session_state.sample:
    st.markdown('<div class="note-box"><b>Sample preview.</b> These results use demo data. Enter your own values '
                'in the sidebar and press <b>Generate &amp; Optimise</b>.</div>', unsafe_allow_html=True)

tabs = st.tabs(["Overview", "Conflict Graph", "Timetable", "Counting", "Campus MST", "Resource Flow"])

# ------------------------------------------------------------- overview
with tabs[0]:
    with st.expander("How this dashboard works", expanded=False):
        st.markdown("1. **Enter data** – students, classrooms, labs, teachers, slots (10 fixed courses, each with theory + lab)\n"
                    "2. **Find clashes** – sessions sharing students or a teacher cannot run together\n"
                    "3. **Colour the graph** – each colour becomes one time slot\n"
                    "4. **Assign rooms** – theory goes to a classroom, labs go to a lab, each big enough\n"
                    "5. **Verify and report** – checks prove it works; download the PDF or CSV")
    kpis([(n, "Sessions (theory + labs)", f"{c} courses; {n - c} of them also have a lab session."),
          (len(d["E"]), "Conflict edges", "Pairs of sessions that cannot share a slot (common students or same teacher)."),
          (f'{d["slots"]}/{P["t"]}', "Slots needed / available", "Minimum slots the colouring needs, compared with the slots you have."),
          (f'{n - len(d["unmatched"])}/{n}', "Sessions placed in rooms", "Sessions that received a classroom/lab big enough for their students."),
          (f'{d["mc"]:.1f}', "MST cost (units)", "Total cost of the cheapest network connecting all buildings."),
          (f'{d["seat_got"]}/{d["seat_need"]}', "Seats filled / needed", "Seats filled / seats needed across all slots, found with max-flow.")])
    if d["ok"]:
        st.markdown(f'<div class="verdict good" title="Overall result of all correctness checks below."><h3>✔ TIMETABLE POSSIBLE</h3>'
                    f'All {n} sessions ({c} theory + {n - c} lab) are scheduled without clashes. It needs {d["slots"]} of your {P["t"]} available '
                    f'time slots.</div>', unsafe_allow_html=True)
    else:
        fails = "".join(f"<li><b>{t}</b>: {x}</li>" for p, t, x in d["ck"] if not p)
        st.markdown(f'<div class="verdict bad" title="Overall result of all correctness checks below."><h3>✕ NOT POSSIBLE with this data</h3>'
                    f'This data needs {d["slots"]} time slots and you have {P["t"]}; failed checks:'
                    f'<ul>{fails}</ul></div>', unsafe_allow_html=True)
    a, b, c3 = st.columns(3)
    with a:
        st.subheader("Slots: needed vs available")
        st.plotly_chart(charts.hbar(["Needed", "Available"], [d["slots"], P["t"]], ["#C0504D", "#4F8A5B"]),
                        width="stretch")
    with b:
        st.subheader("Students per slot")
        ps = [sum(d["sz"][x] for x in m) for m in d["slot_members"]]
        st.plotly_chart(charts.hbar([f"Slot {i + 1}" for i in range(len(ps))], ps,
                                    [PALETTE[i % len(PALETTE)] for i in range(len(ps))]), width="stretch")
    with c3:
        st.subheader("Room utilisation")
        use = [sum(1 for x in d["room_of"] if d["room_of"][x] == j) for j in range(len(d["rooms"]))]
        st.plotly_chart(charts.hbar([r["n"] for r in d["rooms"]], use, ["#3a63b5"] * len(use),
                                    [f"{u / d['slots'] * 100:.0f}%" for u in use]), width="stretch")
    st.subheader("Correctness Verification (Proof Techniques)")
    for p, t, x in d["ck"]:
        st.markdown(f"{'✅' if p else '❌'} **{t}**  \n<small>{x}</small>", unsafe_allow_html=True)

# --------------------------------------------------------- conflict graph
with tabs[1]:
    st.caption("Each circle is a theory session and each diamond is a lab. A line means two sessions share students or a teacher, so they cannot "
               "run at the same time. Same colour = same time slot.  ·  Graph Theory · Welsh–Powell Colouring")
    deg = [len(a) for a in d["adj"]]
    dm = max(deg)
    kpis([(n, "Sessions (nodes)", "Each theory or lab session is one node."),
          (len(d["E"]), "Clashes (edges)", "Each line joins two sessions that cannot run together."),
          (f'{round(len(d["E"]) / d["pairs"] * 100)}%', "Clash density", "Share of all session pairs that clash."),
          (dm, "Max clashes (one session)", f"Highest clash count: {cn(deg.index(dm))}. It is the hardest to place."),
          (d["slots"], "Colours = slots needed", "Welsh–Powell uses one colour per time slot.")])
    g1, g2 = st.columns([2.2, 1])
    with g1:
        st.plotly_chart(charts.conflict_graph(d), width="stretch")
        st.caption("Hover a circle or line for details · thicker line = more shared students · dashed = same teacher "
                   "· bigger circle = more clashes")
    with g2:
        st.subheader("Slot groups")
        for s, m in enumerate(d["slot_members"]):
            st.markdown(f'<div class="sg" style="--c:{PALETTE[s % len(PALETTE)]}" title="Slot {s + 1}: these courses share no '
                        f'students or teachers, so they run together."><b>Slot {s + 1}</b><br>'
                        f'{" · ".join(cn(x) for x in m)}</div>', unsafe_allow_html=True)
        st.subheader("Most clash-prone sessions")
        top = sorted(range(n), key=lambda i: -deg[i])[:4]
        st.plotly_chart(charts.hbar([cn(i) for i in top], [deg[i] for i in top],
                                    [PALETTE[d["col"][i] % len(PALETTE)] for i in top]), width="stretch")

# ------------------------------------------------------------ timetable
with tabs[2]:
    st.caption("Each column is a time slot, each row a classroom or lab, each block a session (LAB badge = lab). Hover a block for details.  ·  "
               "Bipartite Matching")
    used_rooms = len(set(d["room_of"].values()))
    fills = [d["sz"][x] / d["rooms"][j]["cap"] for x, j in d["room_of"].items()]
    ps = [sum(d["sz"][x] for x in m) for m in d["slot_members"]]
    kpis([(f'{n - len(d["unmatched"])}/{n}', "Sessions scheduled", "Sessions that have both a slot and a room."),
          (d["slots"], "Time slots used", "Slots the timetable needs."),
          (f'{used_rooms}/{len(d["rooms"])}', "Rooms in use", "Classrooms and labs used at least once."),
          (f'{round(sum(fills) / len(fills) * 100) if fills else 0}%', "Average room fill", "Average students / seats across booked rooms."),
          (f'Slot {ps.index(max(ps)) + 1}', f"Busiest slot ({max(ps)})", "Slot with the most students attending.")])
    st.subheader("Timetable board")
    st.markdown(charts.board_html(d), unsafe_allow_html=True)
    if d["unmatched"]:
        st.markdown('<div class="warn-box"><b>No room found for:</b> ' + ", ".join(cn(x) for x in d["unmatched"]) +
                    ". Add rooms or seats.</div>", unsafe_allow_html=True)
    st.subheader("Teacher workload")
    cols = st.columns(min(P["f"], 5))
    for f in range(P["f"]):
        with cols[f % len(cols)]:
            cnt = sum(1 for x in range(n) if d["fac"][x] == f)
            st.markdown(f"**F{f + 1}** · {cnt} session(s)")
            st.markdown(charts.chips_html(d, f), unsafe_allow_html=True)
    st.subheader("Timetable details")
    show_table(timetable_df(d), "course_details.csv", "dl_tt")

# ------------------------------------------------------------- counting
with tabs[3]:
    st.caption("Why do we need an algorithm? Count the possible timetables and see how unlikely a random guess "
               "is to work.  ·  Counting & Probability")
    free_pct = d["free"] / d["trials"] * 100
    st.markdown(f'<div class="vs"><div title="Simulated: random timetables are tried and the clash-free ones are counted.">'
                f'<b>{free_pct:.2f}%</b><span>chance that a RANDOM timetable has no clashes</span></div>'
                f'<div class="g" title="Graph colouring never puts clashing sessions in the same slot.">'
                f'<b>0 clashes</b><span>using graph colouring</span></div></div>', unsafe_allow_html=True)
    dens = len(d["E"]) / d["pairs"] * 100
    kpis([(f'~10^{d["log_n"]:.1f}', f'Possible timetables ({P["t"]}^{n})', "Slots raised to the power of sessions."),
          (f'{len(d["E"])} / {d["pairs"]}', f"Session pairs that clash ({dens:.0f}%)", "Conflicting pairs out of all pairs."),
          (f'{len(d["E"]) / P["t"]:.2f}', "Expected clashes, random timetable", "Conflicts divided by slots (linearity of expectation).")])
    st.subheader(f'What happens if slots are chosen at random? ({d["trials"]} simulated timetables)')
    st.plotly_chart(charts.histogram(d), width="stretch")
    st.caption("Only the green bar (0 clashes) is valid, and graph colouring always lands there.")
    st.subheader("Calculation details")
    show_table(count_df(d), "counting_probability.csv", "dl_cnt")

# ------------------------------------------------------------------ MST
with tabs[4]:
    st.caption("Circles are buildings, lines are cables with their cost. Gold cables are the cheapest set that "
               "still connects every building. Hover a building or cable.  ·  Minimum Spanning Tree (Kruskal)")
    kpis([(P["b"], "Buildings", "Buildings to connect."),
          (len(d["mst"]), "Cables needed", "A tree over n buildings needs n − 1 cables."),
          (f'{d["mc"]:.1f}', "MST cost (units)", "Total cost of the selected cables."),
          (f'{d["full"]:.1f}', "Cost if every pair is cabled", "Cost of cabling every possible pair."),
          (f'{round((1 - d["mc"] / d["full"]) * 100)}%', "Saved by the MST", "Saving compared with cabling every pair.")])
    m1, m2 = st.columns([1.7, 1])
    with m1:
        st.subheader("Campus map")
        st.plotly_chart(charts.mst_map(d), width="stretch")
    with m2:
        st.subheader("Cabling plan")
        show_table(mst_df(d), "cabling_plan.csv", "dl_mst")
        st.caption("Kruskal: sort every possible cable by cost, add the cheapest that forms no loop, "
                   "until all buildings are connected.")

# ----------------------------------------------------------------- flow
with tabs[5]:
    st.caption("Checks whether every seat request can be filled in each slot. A full room is the bottleneck.  ·  "
               "Max-Flow Min-Cut")
    st.subheader("Seating Capacity per Time Slot")
    show_table(flow_df(d), "seating_capacity.csv", "dl_flow")
    st.caption("Source → sessions (enrolment) → matching rooms (classrooms/labs) → sink (room capacity). Max-Flow = Min-Cut: the rooms listed "
               "are the bottleneck; adding capacity there is the only way to seat more students.")
