# ConfReview — Academic Conference Paper Submission & Review System

A Flask + SQLite prototype for DBMS Project-Based Learning. It demonstrates a relational database-backed workflow for academic conference submissions, reviewer assignment, structured review, editorial decisions, presentation scheduling, reporting, and CSV export.

> **Prototype note:** This is an academic demonstration, not a production service. The application currently stores manuscript filenames as metadata rather than uploading PDF bytes. It has no authentication/role-based access control, automatic conflict-of-interest detection, minimum-review enforcement, or overlapping-slot prevention. Do not use real personal data or deploy publicly without security work.

## Run locally

Requirements: Python 3.10+

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. A local `conference.db` and fictional sample records are created on first launch. `/health` provides a basic health check.

## Main modules

- Dashboard and paper search/filter
- New paper submission and version metadata
- Reviewer directory and assignment
- Review scores and recommendation
- Editorial decision and status workflow
- Presentation slot scheduling
- Status, track, reviewer-workload and paper-score reports
- CSV export

## Repository map

- `app.py` — Flask routes, database initialization, and queries
- `schema.sql` — logical SQLite schema and indexes
- `templates/`, `static/` — UI
- `docs/` — ERD, schema/normalization notes, data dictionary, testing plan and submission checklist
- `presentations/` — add the approved Phase 1, Phase 2 and Phase 3 PPT/PDF files here
- `tests/` — add/maintain automated tests here

## Database documentation

Start with [`docs/DBMS_DESIGN_AND_TESTING.md`](docs/DBMS_DESIGN_AND_TESTING.md) and [`docs/ERD.mmd`](docs/ERD.mmd). These documents are a draft aligned to the current `schema.sql`; check them against the final code and your faculty's approved requirements before submission.

## GitHub submission checklist

- [ ] Run the app locally and verify the workflows in the testing plan
- [ ] Capture genuine screenshots of data entry, search/display, update/review, and reports
- [ ] Add the approved Phase 1, Phase 2, and Phase 3 presentations to `presentations/`
- [ ] Complete the university report template, including actual test results and figure/table numbering
- [ ] Record the 5-minute demo and add a document containing its public Google Drive link
- [ ] Remove local databases, virtual environments, secrets, and personal data before pushing
