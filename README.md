# University Resource Optimisation (Streamlit)

Discrete Mathematics project: timetabling, room allocation and campus network design.

## Run in VS Code

1. Open this folder in VS Code (File > Open Folder).
2. Open a terminal (Ctrl+`) and create a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS / Linux
   ```
3. Select it as the interpreter: Ctrl+Shift+P > "Python: Select Interpreter".
4. Install and run:
   ```
   pip install -r requirements.txt
   streamlit run app.py
   ```
5. The app opens at http://localhost:8501.

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit interface (sidebar inputs, six tabs, dark mode, CSV downloads) |
| `engine.py` | All the maths: sets, Welsh-Powell colouring, Kuhn matching, counting, Kruskal MST, Edmonds-Karp max-flow |
| `charts.py` | Plotly figures and HTML timetable board |
| `report.py` | PDF report (reportlab + matplotlib) |
| `requirements.txt` | Dependencies |
| `.streamlit/config.toml` | Theme / server settings |

## Courses and labs
The 10 courses are fixed (Discrete Mathematics, Data Structures, Operating Systems, Robotics,
Digital Electronics and Microprocessors, Design Thinking, DBMS, OOPS, CNN, LDM). Each has a theory
session (needs a classroom) and a lab session (needs a lab room), so the timetable has 20 sessions.
To rename a course or make one theory-only, edit `COURSES` / `LAB_COURSES` at the top of `engine.py`.

## Features
- **Dark mode**: toggle at the top of the sidebar (charts, tables and the timetable board all switch).
- **Hover help**: every KPI card, button and input has a tooltip; clickable items show a pointer cursor.
- **Downloads**: PDF report and the timetable as CSV (sidebar), plus a CSV button under each table
  (course details, counting, cabling plan, seating capacity). CSVs open cleanly in Excel.
- Downloads are enabled after you press **Generate & Optimise** with your own values.

## Notes
- Same random dataset ID gives the same data (the random generator matches the original HTML dashboard).
- `engine.py` has no Streamlit dependency, so you can import and test it on its own.
