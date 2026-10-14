# ConfReview — DBMS Design and Testing Notes

**Status:** Draft supporting documentation, based on the current `schema.sql` and Flask source. Update it after code changes and replace all proposed test outcomes with observed outcomes before submission.

## 1. Problem statement

Academic conference workflows need to keep paper details, authors, tracks, manuscript versions, reviewers, review scores, editorial decisions and presentation slots connected. Tracking these details in separate spreadsheets or messages can cause duplicate records, inconsistent statuses, missing review history and difficulty preparing reports. ConfReview provides a single relational database-backed prototype for organizing these records and demonstrating common DBMS operations.

## 2. Objectives

1. Design a relational schema for conference, track, author, paper, version, reviewer, assignment, review, decision and presentation data.
2. Enforce key relationships and basic integrity rules using primary keys, foreign keys, UNIQUE, NOT NULL, CHECK and DEFAULT constraints.
3. Implement submission, search, version metadata, reviewer assignment, scoring, decisions and scheduling through a Flask interface.
4. Generate summary reports using joins, aggregation and grouping, and export paper records as CSV.
5. Validate the prototype with positive and negative tests and document any limitations honestly.

## 3. Scope and assumptions

**In scope:** local single-conference prototype; paper metadata; author and reviewer directory; version filename metadata; reviewer assignment; three 1–10 review scores; recommendation; editorial decision; one presentation slot per paper; reports and CSV export.

**Assumptions:** one corresponding author is stored per paper; each paper belongs to one track; a reviewer can be assigned to multiple papers; each paper-reviewer pair can be assigned only once; each assignment can have at most one current review; each paper can have at most one editorial decision and one presentation slot.

**Out of scope in the current code:** real PDF file upload/storage; authentication and authorization; conflict-of-interest detection; enforcing minimum review counts before decision; preventing time/room overlaps; multi-conference administration UI; production deployment and security hardening.

## 4. Proposed workflow

1. Conference and tracks are initialized in the database.
2. An author submits a paper with title, abstract, affiliation, email and track.
3. The system creates paper metadata and an initial version filename record.
4. The administrator adds reviewers and assigns them to papers.
5. Reviewers' scores, recommendation and comments are recorded against assignments.
6. The administrator updates status and records an editorial decision.
7. Accepted/presented papers can be assigned a room, start time and duration.
8. The reports module summarizes status counts, track distribution, reviewer workload and paper scores; CSV export provides a paper summary.

## 5. ER model

The current ER model is in [`ERD.mmd`](ERD.mmd). Render it to an image for the final report and verify all cardinalities against the final schema. The design has ten entities: `conferences`, `tracks`, `authors`, `papers`, `paper_versions`, `reviewers`, `assignments`, `reviews`, `decisions`, and `presentation_slots`.

## 6. Relational schema summary

- `conferences(id PK, name, year, venue)`
- `tracks(id PK, conference_id FK → conferences.id, name, UNIQUE(conference_id, name))`
- `authors(id PK, full_name, email UNIQUE, affiliation)`
- `papers(id PK, submission_code UNIQUE, title, abstract, track_id FK → tracks.id, corresponding_author_id FK → authors.id, status, submitted_at)`
- `paper_versions(id PK, paper_id FK → papers.id, version_no, file_name, uploaded_at, UNIQUE(paper_id, version_no))`
- `reviewers(id PK, full_name, email UNIQUE, expertise)`
- `assignments(id PK, paper_id FK → papers.id, reviewer_id FK → reviewers.id, assigned_at, UNIQUE(paper_id, reviewer_id))`
- `reviews(id PK, assignment_id UNIQUE FK → assignments.id, originality, quality, clarity, recommendation, comments, reviewed_at)`
- `decisions(id PK, paper_id UNIQUE FK → papers.id, decision, notes, decided_at)`
- `presentation_slots(id PK, paper_id UNIQUE FK → papers.id, room, starts_at, duration_minutes)`

## 7. Important integrity constraints

| Constraint | Implemented rule |
|---|---|
| Primary keys | Integer primary key on every table |
| Foreign keys | Child rows reference their parent conference/track/author/paper/reviewer/assignment |
| Unique | Author email, reviewer email, submission code, track name per conference, version number per paper, assignment pair, one review per assignment, one decision per paper, one slot per paper |
| NOT NULL | Required identifiers and core descriptive/business fields cannot be null |
| CHECK | Paper status limited to Submitted, Under Review, Revision Required, Accepted, Rejected; review scores 1–10; recommendation and decision limited to enumerated values; presentation duration 5–180 minutes |
| DEFAULT | Initial paper status and creation timestamps; empty decision notes |
| Referential action | Version, assignment, review, decision and slot rows are configured to cascade when their parent paper/assignment is deleted, as defined in the SQL schema |

## 8. Functional dependencies and normalization

The following are the principal key-based functional dependencies in the implemented design. They describe the intended relational model; the final report should explain any partial/transitive dependency checks explicitly.

- `conferences`: `id → name, year, venue`
- `tracks`: `id → conference_id, name`; `(conference_id, name) → id`
- `authors`: `id → full_name, email, affiliation`; `email → id, full_name, affiliation`
- `papers`: `id → submission_code, title, abstract, track_id, corresponding_author_id, status, submitted_at`; `submission_code → the same non-key attributes`
- `paper_versions`: `id → paper_id, version_no, file_name, uploaded_at`; `(paper_id, version_no) → file_name, uploaded_at`
- `reviewers`: `id → full_name, email, expertise`; `email → id, full_name, expertise`
- `assignments`: `id → paper_id, reviewer_id, assigned_at`; `(paper_id, reviewer_id) → assigned_at`
- `reviews`: `id → assignment_id, originality, quality, clarity, recommendation, comments, reviewed_at`; `assignment_id → the review attributes`
- `decisions`: `id → paper_id, decision, notes, decided_at`; `paper_id → decision, notes, decided_at`
- `presentation_slots`: `id → paper_id, room, starts_at, duration_minutes`; `paper_id → room, starts_at, duration_minutes`

**1NF:** Each table has a primary key and stores single-valued attributes; repeating reviewer/version details are represented in separate rows rather than repeating columns.

**2NF:** Most relations use a single-column primary key, so non-key attributes are fully dependent on that key. Where a composite candidate key exists (for example `(paper_id, version_no)` in `paper_versions` and `(conference_id, name)` in `tracks`), the attributes depend on the whole candidate key, not only one part.

**3NF:** Descriptive attributes for conferences, tracks, authors and reviewers are stored in their own relations. In `papers`, track and corresponding author are referenced by keys rather than copying their descriptive details. Reviews, decisions, versions and presentation slots are separated into relations with their own keys. Based on these declared dependencies, the schema is designed to satisfy 3NF, assuming the listed functional dependencies and business rules are complete.

## 9. Data dictionary

| Table | Column | Type | Key / rule | Meaning |
|---|---|---|---|---|
| conferences | id | INTEGER | PK | Conference identifier |
| conferences | name | TEXT | NOT NULL | Conference name |
| conferences | year | INTEGER | NOT NULL | Conference year |
| conferences | venue | TEXT | NOT NULL | Conference venue |
| tracks | id | INTEGER | PK | Track identifier |
| tracks | conference_id | INTEGER | FK, NOT NULL | Parent conference |
| tracks | name | TEXT | NOT NULL; unique with conference_id | Track name |
| authors | id | INTEGER | PK | Author identifier |
| authors | full_name | TEXT | NOT NULL | Author name |
| authors | email | TEXT | UNIQUE, NOT NULL | Author email |
| authors | affiliation | TEXT | NOT NULL | Institution/affiliation |
| papers | id | INTEGER | PK | Internal paper identifier |
| papers | submission_code | TEXT | UNIQUE, NOT NULL | Public submission code |
| papers | title | TEXT | NOT NULL | Paper title |
| papers | abstract | TEXT | NOT NULL | Paper abstract |
| papers | track_id | INTEGER | FK, NOT NULL | Track selected for paper |
| papers | corresponding_author_id | INTEGER | FK, NOT NULL | Corresponding author |
| papers | status | TEXT | CHECK, DEFAULT, NOT NULL | Current workflow status |
| papers | submitted_at | TEXT | DEFAULT timestamp, NOT NULL | Submission time |
| paper_versions | id | INTEGER | PK | Version-row identifier |
| paper_versions | paper_id | INTEGER | FK, cascade delete | Related paper |
| paper_versions | version_no | INTEGER | Unique with paper_id, NOT NULL | Sequential version number |
| paper_versions | file_name | TEXT | NOT NULL | Filename metadata; not file contents |
| paper_versions | uploaded_at | TEXT | DEFAULT timestamp, NOT NULL | Version record time |
| reviewers | id | INTEGER | PK | Reviewer identifier |
| reviewers | full_name | TEXT | NOT NULL | Reviewer name |
| reviewers | email | TEXT | UNIQUE, NOT NULL | Reviewer email |
| reviewers | expertise | TEXT | NOT NULL | Expertise keywords |
| assignments | id | INTEGER | PK | Assignment identifier |
| assignments | paper_id | INTEGER | FK, cascade delete | Assigned paper |
| assignments | reviewer_id | INTEGER | FK, NOT NULL | Assigned reviewer |
| assignments | assigned_at | TEXT | DEFAULT timestamp, NOT NULL | Assignment time |
| reviews | id | INTEGER | PK | Review identifier |
| reviews | assignment_id | INTEGER | FK, UNIQUE, NOT NULL | Assignment reviewed |
| reviews | originality | INTEGER | CHECK 1–10 | Originality score |
| reviews | quality | INTEGER | CHECK 1–10 | Quality score |
| reviews | clarity | INTEGER | CHECK 1–10 | Clarity score |
| reviews | recommendation | TEXT | CHECK, NOT NULL | Reviewer recommendation |
| reviews | comments | TEXT | NOT NULL | Reviewer comments |
| reviews | reviewed_at | TEXT | DEFAULT timestamp, NOT NULL | Review timestamp |
| decisions | id | INTEGER | PK | Decision-row identifier |
| decisions | paper_id | INTEGER | FK, UNIQUE, NOT NULL | Paper decided |
| decisions | decision | TEXT | CHECK, NOT NULL | Editorial decision |
| decisions | notes | TEXT | DEFAULT empty, NOT NULL | Decision rationale |
| decisions | decided_at | TEXT | DEFAULT timestamp, NOT NULL | Decision timestamp |
| presentation_slots | id | INTEGER | PK | Slot identifier |
| presentation_slots | paper_id | INTEGER | FK, UNIQUE, NOT NULL | Scheduled paper |
| presentation_slots | room | TEXT | NOT NULL | Room/venue |
| presentation_slots | starts_at | TEXT | NOT NULL | Start date/time text |
| presentation_slots | duration_minutes | INTEGER | CHECK 5–180, NOT NULL | Presentation length |

## 10. Application/database mapping

| Screen/module | Tables | Main database operations |
|---|---|---|
| Dashboard | papers, tracks, authors, reviewers, reviews | SELECT, JOIN, COUNT |
| Paper list/search | papers, tracks, authors | SELECT, JOIN, LIKE, filters |
| New submission | authors, papers, paper_versions | INSERT; author upsert by email |
| Paper workspace | papers, paper_versions, assignments, reviewers, reviews, decisions, presentation_slots | SELECT, INSERT, UPDATE, upsert |
| Reviewer directory | reviewers, assignments, reviews | INSERT, SELECT, aggregate workload |
| Schedule | presentation_slots, papers, authors | SELECT, JOIN, ORDER BY |
| Reports | papers, tracks, reviewers, assignments, reviews | GROUP BY, COUNT, AVG, LEFT JOIN |
| CSV export | papers, tracks, authors | SELECT and CSV serialization |

## 11. Testing plan — record actual results before submission

**Important:** The “Actual result” and “Status” cells are intentionally marked **Not run**. Execute each test on your machine, capture evidence, and replace these entries with the observed result. Do not claim tests passed without running them.

| ID | Test/action | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-01 | Open `/` after first launch | Dashboard loads with sample counts | Not run | Pending |
| TC-02 | Open `/health` | JSON response reports status `ok` | Not run | Pending |
| TC-03 | Submit a paper with all required fields | Paper is created, version 1 metadata is created, success message appears | Not run | Pending |
| TC-04 | Submit with one required field blank | Submission is rejected and validation message appears | Not run | Pending |
| TC-05 | Search by a known title or author | Matching paper appears | Not run | Pending |
| TC-06 | Filter papers by status | Only matching statuses appear | Not run | Pending |
| TC-07 | Add a reviewer with a new email | Reviewer appears in directory | Not run | Pending |
| TC-08 | Add a reviewer with an existing email | Duplicate is rejected with an error message | Not run | Pending |
| TC-09 | Assign a reviewer to a paper twice | Unique constraint rejects duplicate assignment | Not run | Pending |
| TC-10 | Save review scores within 1–10 | Review is stored and appears in the paper workspace | Not run | Pending |
| TC-11 | Attempt a score outside 1–10 using a direct SQL test | CHECK constraint rejects the row | Not run | Pending |
| TC-12 | Record editorial decision | Decision and paper status update are persisted | Not run | Pending |
| TC-13 | Create/update presentation slot with duration 5–180 | Slot is saved and shown in schedule | Not run | Pending |
| TC-14 | Attempt a duration outside 5–180 using a direct SQL test | CHECK constraint rejects the row | Not run | Pending |
| TC-15 | Open `/reports` | Status, track, workload and score summaries render | Not run | Pending |
| TC-16 | Download `/export.csv` | CSV downloads with header and paper rows | Not run | Pending |

## 12. Limitations and future enhancements

The current version is a local prototype. Filename metadata is used instead of actual PDF upload/storage. It has no user login or role separation, automatic conflict-of-interest checks, minimum-review-count enforcement before decisions, or room/time conflict detection. Future improvements should add secure authentication and authorization, safe file upload handling, server-side validation, audit logging, reviewer-conflict checks, scheduling conflict validation, automated tests and deployment hardening.

## 13. Final report evidence to add

Before final submission, add actual screenshots showing: (1) paper data entry, (2) search/display, (3) reviewer assignment and review/update, (4) reports or CSV output, and (5) an observed validation/negative test. Render `ERD.mmd` to a readable figure. Include the complete `schema.sql` in Appendix A and cite the repository in Appendix B. Use IEEE-style references only for sources you actually consulted.
