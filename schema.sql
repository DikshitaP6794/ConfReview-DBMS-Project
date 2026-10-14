-- Academic Conference Paper Submission and Review System
-- SQLite schema. The application creates these tables automatically on first run.
PRAGMA foreign_keys = ON;
CREATE TABLE conferences(id INTEGER PRIMARY KEY, name TEXT NOT NULL, year INTEGER NOT NULL, venue TEXT NOT NULL);
CREATE TABLE tracks(id INTEGER PRIMARY KEY, conference_id INTEGER NOT NULL REFERENCES conferences(id), name TEXT NOT NULL, UNIQUE(conference_id,name));
CREATE TABLE authors(id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, affiliation TEXT NOT NULL);
CREATE TABLE papers(id INTEGER PRIMARY KEY, submission_code TEXT NOT NULL UNIQUE, title TEXT NOT NULL, abstract TEXT NOT NULL, track_id INTEGER NOT NULL REFERENCES tracks(id), corresponding_author_id INTEGER NOT NULL REFERENCES authors(id), status TEXT NOT NULL DEFAULT 'Submitted' CHECK(status IN ('Submitted','Under Review','Revision Required','Accepted','Rejected')), submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE paper_versions(id INTEGER PRIMARY KEY, paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE, version_no INTEGER NOT NULL, file_name TEXT NOT NULL, uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(paper_id,version_no));
CREATE TABLE reviewers(id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, expertise TEXT NOT NULL);
CREATE TABLE assignments(id INTEGER PRIMARY KEY, paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE, reviewer_id INTEGER NOT NULL REFERENCES reviewers(id), assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(paper_id,reviewer_id));
CREATE TABLE reviews(id INTEGER PRIMARY KEY, assignment_id INTEGER NOT NULL UNIQUE REFERENCES assignments(id) ON DELETE CASCADE, originality INTEGER NOT NULL CHECK(originality BETWEEN 1 AND 10), quality INTEGER NOT NULL CHECK(quality BETWEEN 1 AND 10), clarity INTEGER NOT NULL CHECK(clarity BETWEEN 1 AND 10), recommendation TEXT NOT NULL CHECK(recommendation IN ('Accept','Minor Revision','Major Revision','Reject')), comments TEXT NOT NULL, reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE decisions(id INTEGER PRIMARY KEY, paper_id INTEGER NOT NULL UNIQUE REFERENCES papers(id) ON DELETE CASCADE, decision TEXT NOT NULL CHECK(decision IN ('Accepted','Rejected','Revision Required')), notes TEXT NOT NULL DEFAULT '', decided_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE presentation_slots(id INTEGER PRIMARY KEY, paper_id INTEGER NOT NULL UNIQUE REFERENCES papers(id) ON DELETE CASCADE, room TEXT NOT NULL, starts_at TEXT NOT NULL, duration_minutes INTEGER NOT NULL CHECK(duration_minutes BETWEEN 5 AND 180));
CREATE INDEX idx_papers_status ON papers(status);
CREATE INDEX idx_papers_track ON papers(track_id);
CREATE INDEX idx_assignments_reviewer ON assignments(reviewer_id);
