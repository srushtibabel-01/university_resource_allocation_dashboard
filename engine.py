"""Discrete-mathematics engine for the University Resource Optimisation dashboard.

Pure Python (no Streamlit), so it can be tested on its own.

Every course has a THEORY session (needs a classroom) and, if listed in
LAB_COURSES, a LAB session (needs a lab room). Each session is one node of the
conflict graph.

Topics covered
--------------
1. Sets            - student enrolment sets, clash detection by intersection
2. Graph colouring - Welsh-Powell colouring -> time slots
3. Bipartite match - Kuhn's algorithm -> session-to-room allocation
4. Counting/prob.  - |slots|^|sessions|, Monte-Carlo random timetables
5. Spanning tree   - Kruskal's algorithm -> cheapest campus cabling
6. Max-flow/min-cut- Edmonds-Karp -> seating capacity per slot
"""
from __future__ import annotations

import colorsys
import math
from collections import deque

# The fixed list of 10 courses (edit the names here if needed).
COURSES = [
    "Discrete Mathematics", "Data Structures", "Operating Systems", "Robotics",
    "Digital Electronics and Microprocessors", "Design Thinking", "DBMS", "OOPS", "CNN", "LDM",
]
# Courses that also have a lab session. Remove a name to make it theory-only.
LAB_COURSES = set(COURSES)

# key, label, default, min, max, help text
FIELDS = [
    ("s", "Number of students", 60, 10, 2000, "Total students enrolled in the university."),
    ("k", "Courses per student", 2, 1, 6,
     "How many of the 10 courses each student registers for. More courses per student means more clashes."),
    ("r", "Classrooms available", 4, 1, 20,
     "Rooms for theory sessions. A room hosts only one session per time slot."),
    ("l", "Labs available", 4, 1, 10,
     "Lab rooms for lab sessions. A lab hosts only one session per time slot."),
    ("f", "Faculty members", 5, 1, 15,
     "Teachers available. A teacher cannot teach two sessions in the same slot."),
    ("t", "Time slots available", 12, 1, 30,
     "Time periods in your week. The system calculates how many slots are really needed and checks they fit."),
    ("b", "Campus buildings", 6, 3, 12,
     "Buildings to be connected at the lowest cabling cost (Minimum Spanning Tree)."),
    ("seed", "Random dataset ID", 3, 1, 9999,
     "Controls the random enrolments. Same ID = same data; new ID = different dataset."),
]
DEFAULTS = {k: d for k, _, d, *_ in FIELDS}

_BASE = ["#2F63C9", "#C0504D", "#4F8A5B", "#D9A441", "#7B5EA7", "#2A9D8F",
         "#E76F51", "#457B9D", "#8D6E63", "#6C757D", "#B5179E", "#3A86FF"]


def _extra_colours(n):
    out = []
    for i in range(n):
        h = (i * 0.381966) % 1.0  # golden-angle spacing
        r, g, b = colorsys.hls_to_rgb(h, 0.42 + 0.08 * (i % 2), 0.55)
        out.append("#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255)))
    return out


PALETTE = _BASE + _extra_colours(18)  # 30 colours: enough for 30 time slots


class Rng:
    """Same linear congruential generator as the original JavaScript dashboard,
    so a given dataset ID reproduces the same data."""

    def __init__(self, seed: int):
        self.s = seed & 0xFFFFFFFF

    def __call__(self) -> float:
        self.s = (self.s * 1664525 + 1013904223) & 0xFFFFFFFF
        return self.s / 4294967296


def _round(x: float) -> int:
    return int(math.floor(x + 0.5))  # round-half-up like JS Math.round


def max_flow(cap, n, s, t):
    """Edmonds-Karp. Returns (flow value, set of nodes reachable from s in the residual graph).
    The reachable set is the source side of a minimum cut."""
    f = [row[:] for row in cap]
    total = 0
    while True:
        parent = [-1] * n
        parent[s] = s
        dq = deque([s])
        while dq and parent[t] < 0:
            u = dq.popleft()
            for v in range(n):
                if parent[v] < 0 and f[u][v] > 0:
                    parent[v] = u
                    dq.append(v)
        if parent[t] < 0:
            break
        b = float("inf")
        v = t
        while v != s:
            b = min(b, f[parent[v]][v])
            v = parent[v]
        v = t
        while v != s:
            f[parent[v]][v] -= b
            f[v][parent[v]] += b
            v = parent[v]
        total += b
    seen = {s}
    dq = deque([s])
    while dq:
        u = dq.popleft()
        for v in range(n):
            if v not in seen and f[u][v] > 0:
                seen.add(v)
                dq.append(v)
    return int(total), seen


def generate(P: dict) -> dict:
    """Run the whole pipeline for parameters P and return every result."""
    R = Rng(P["seed"])
    n_courses = len(COURSES)
    n_students, k = P["s"], P["k"]

    # Sessions: all theory sessions first, then the lab sessions.
    course_of = list(range(n_courses)) + [i for i in range(n_courses) if COURSES[i] in LAB_COURSES]
    kind = ["Theory"] * n_courses + ["Lab"] * (len(course_of) - n_courses)
    n = len(course_of)

    def cn(i):
        return COURSES[course_of[i]] + (" Lab" if kind[i] == "Lab" else "")

    # 1. Sets: enrolment (per course; a course's lab has the same students) ----
    en = [set() for _ in range(n_courses)]
    for stu in range(n_students):
        chosen = set()
        while len(chosen) < min(k, n_courses):
            chosen.add(int(R() * n_courses))
        for x in chosen:
            en[x].add(stu)
    fac_course = [i % P["f"] for i in range(n_courses)]
    sz = [len(en[course_of[i]]) for i in range(n)]
    fac = [fac_course[course_of[i]] for i in range(n)]

    # 2. Relations: clash edges via set intersection ----------------------
    E, adj = [], [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            shared = len(en[course_of[i]] & en[course_of[j]])
            same_teacher = fac[i] == fac[j]
            if shared or same_teacher:
                E.append((i, j, shared, same_teacher))
                adj[i].append(j)
                adj[j].append(i)

    # 3. Welsh-Powell graph colouring -------------------------------------
    order = sorted(range(n), key=lambda a: -len(adj[a]))
    col = [-1] * n
    cur = 0
    while any(x < 0 for x in col):
        for v in order:
            if col[v] < 0 and not any(col[u] == cur for u in adj[v]):
                col[v] = cur
        cur += 1
    slots = max(col) + 1
    max_deg = max(len(a) for a in adj)

    # 4. Bipartite matching (Kuhn) per slot, separately for classrooms and labs
    avg = n_students * min(k, n_courses) / n_courses
    rooms = [{"n": f"R{i + 1}", "cap": _round(avg * (0.9 + R() * 0.9)), "type": "Theory"} for i in range(P["r"])]
    rooms += [{"n": f"L{i + 1}", "cap": _round(avg * (0.9 + R() * 0.9)), "type": "Lab"} for i in range(P["l"])]
    room_of: dict[int, int] = {}
    unmatched: list[int] = []
    slot_members = [[x for x in range(n) if col[x] == s] for s in range(slots)]
    for s in range(slots):
        for kd in ("Theory", "Lab"):
            cs = sorted([x for x in slot_members[s] if kind[x] == kd], key=lambda a: -sz[a])
            ridx = [j for j, r in enumerate(rooms) if r["type"] == kd]
            match_room = {j: -1 for j in ridx}

            def try_session(u, seen):
                for j in ridx:
                    if rooms[j]["cap"] >= sz[cs[u]] and j not in seen:
                        seen.add(j)
                        if match_room[j] < 0 or try_session(match_room[j], seen):
                            match_room[j] = u
                            return True
                return False

            for u in range(len(cs)):
                try_session(u, set())
            for j, u in match_room.items():
                if u >= 0:
                    room_of[cs[u]] = j
            unmatched += [x for x in cs if x not in room_of]

    # Correctness checks ---------------------------------------------------
    ck = [
        (all(col[a] != col[b] for a, b, *_ in E),
         "No two conflicting sessions share a time slot",
         "Proof by contradiction: a shared colour on an edge is impossible by construction"),
        (all(len({fac[x] for x in m}) == len(m) for m in slot_members),
         "No faculty member is double-booked",
         "Faculty to session is injective within every slot"),
        (all(col[course_of[l_]] != col[l_] for l_ in range(n_courses, n)),
         "Each course's theory and lab never overlap",
         "Same students attend both, so the two sessions are joined by an edge"),
        (not unmatched,
         "Every session has a room of the right type with capacity >= enrolment",
         ("Unplaced: " + ", ".join(cn(x) for x in unmatched) + " (add rooms/labs or capacity)")
         if unmatched else "Perfect matching found in every slot (classrooms for theory, labs for labs)"),
        (slots <= max_deg + 1,
         "Colours used <= Delta+1 (Welsh-Powell bound)", f"{slots} <= {max_deg}+1"),
        (slots <= P["t"],
         "Slots needed fit the available time slots", f"Needs {slots}, available {P['t']}"),
    ]
    ok = all(x[0] for x in ck)

    # 5. Counting & probability -------------------------------------------
    trials = 4000
    hist: dict[int, int] = {0: 0}
    free = 0
    for _ in range(trials):
        a = [int(R() * P["t"]) for _ in range(n)]
        clashes = sum(1 for x, y, *_ in E if a[x] == a[y])
        hist[clashes] = hist.get(clashes, 0) + 1
        if clashes == 0:
            free += 1
    pairs = n * (n - 1) // 2
    log_n = n * math.log10(P["t"])

    # 6. Minimum spanning tree (Kruskal) ----------------------------------
    pts, tries = [], 0
    while len(pts) < P["b"]:
        z = (50 + R() * 460, 45 + R() * 260)
        lim = 45 if tries > 1500 else 85
        if tries > 3000 or all(math.hypot(o[0] - z[0], o[1] - z[1]) > lim for o in pts):
            pts.append(z)
        tries += 1
    ed = sorted(
        [(i, j, math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]) / 10)
         for i in range(P["b"]) for j in range(i + 1, P["b"])],
        key=lambda e: e[2])
    par = list(range(P["b"]))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    mst, mc = [], 0.0
    for a, b, w in ed:
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb
            mst.append((a, b, w))
            mc += w
    full = sum(e[2] for e in ed)

    # 7. Max-flow / min-cut: can everyone be seated in each slot? --------
    seat_need = seat_got = 0
    fr = []
    nr = len(rooms)
    for s in range(slots):
        cs = slot_members[s]
        nn = len(cs) + nr + 2
        cap = [[0] * nn for _ in range(nn)]
        for i, x in enumerate(cs):
            cap[0][1 + i] = sz[x]
            for j, r in enumerate(rooms):
                if r["type"] == kind[x]:
                    cap[1 + i][1 + len(cs) + j] = sz[x]
        for j, r in enumerate(rooms):
            cap[1 + len(cs) + j][nn - 1] = r["cap"]
        flow, seen = max_flow(cap, nn, 0, nn - 1)
        need = sum(sz[x] for x in cs)
        seat_need += need
        seat_got += flow
        full_rooms = [rooms[u - 1 - len(cs)]["n"] for u in range(len(cs) + 1, nn - 1) if u in seen]
        fr.append((f"Slot {s + 1}", need, flow, ", ".join(full_rooms) or "none",
                   "All seated" if flow >= need else f"Short by {need - flow}"))

    return dict(
        P=P, c=n_courses, n=n, kind=kind, course_of=course_of, sz=sz, fac=fac, E=E, adj=adj, col=col,
        slots=slots, max_deg=max_deg, rooms=rooms, room_of=room_of, unmatched=unmatched, ck=ck, ok=ok,
        slot_members=slot_members, hist=hist, free=free, trials=trials, pairs=pairs,
        log_n=log_n, pts=pts, ed=ed, mst=mst, mc=mc, full=full, fr=fr,
        seat_got=seat_got, seat_need=seat_need, cn=cn,
    )
