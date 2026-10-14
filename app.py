from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3, os, csv, io
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'change-this-before-deployment'
BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, 'conference.db')

def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    return con

def init_db():
    con = connect()
    con.executescript('''
    CREATE TABLE IF NOT EXISTS conferences(id INTEGER PRIMARY KEY, name TEXT NOT NULL, year INTEGER NOT NULL, venue TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS tracks(id INTEGER PRIMARY KEY, conference_id INTEGER NOT NULL REFERENCES conferences(id), name TEXT NOT NULL, UNIQUE(conference_id,name));
    CREATE TABLE IF NOT EXISTS authors(id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, affiliation TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS papers(id INTEGER PRIMARY KEY, submission_code TEXT NOT NULL UNIQUE, title TEXT NOT NULL, abstract TEXT NOT NULL, track_id INTEGER NOT NULL REFERENCES tracks(id), corresponding_author_id INTEGER NOT NULL REFERENCES authors(id), status TEXT NOT NULL DEFAULT 'Submitted' CHECK(status IN ('Submitted','Under Review','Revision Required','Accepted','Rejected')), submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS paper_versions(id INTEGER PRIMARY KEY, paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE, version_no INTEGER NOT NULL, file_name TEXT NOT NULL, uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(paper_id,version_no));
    CREATE TABLE IF NOT EXISTS reviewers(id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, expertise TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS assignments(id INTEGER PRIMARY KEY, paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE, reviewer_id INTEGER NOT NULL REFERENCES reviewers(id), assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(paper_id,reviewer_id));
    CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY, assignment_id INTEGER NOT NULL UNIQUE REFERENCES assignments(id) ON DELETE CASCADE, originality INTEGER NOT NULL CHECK(originality BETWEEN 1 AND 10), quality INTEGER NOT NULL CHECK(quality BETWEEN 1 AND 10), clarity INTEGER NOT NULL CHECK(clarity BETWEEN 1 AND 10), recommendation TEXT NOT NULL CHECK(recommendation IN ('Accept','Minor Revision','Major Revision','Reject')), comments TEXT NOT NULL, reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY, paper_id INTEGER NOT NULL UNIQUE REFERENCES papers(id) ON DELETE CASCADE, decision TEXT NOT NULL CHECK(decision IN ('Accepted','Rejected','Revision Required')), notes TEXT NOT NULL DEFAULT '', decided_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS presentation_slots(id INTEGER PRIMARY KEY, paper_id INTEGER NOT NULL UNIQUE REFERENCES papers(id) ON DELETE CASCADE, room TEXT NOT NULL, starts_at TEXT NOT NULL, duration_minutes INTEGER NOT NULL CHECK(duration_minutes BETWEEN 5 AND 180));
    ''')
    if con.execute('SELECT COUNT(*) FROM conferences').fetchone()[0] == 0:
        con.execute("INSERT INTO conferences(name,year,venue) VALUES('Woxsen Research & Innovation Conference',2026,'Woxsen University, Hyderabad')")
        con.executemany('INSERT INTO tracks(conference_id,name) VALUES(1,?)',[('Artificial Intelligence & Machine Learning',),('Data Science & Analytics',),('Computing Systems',)])
        con.executemany('INSERT INTO authors(full_name,email,affiliation) VALUES(?,?,?)',[
          ('Aarav Sharma','aarav@example.edu','Woxsen University'),('Meera Reddy','meera@example.edu','School of Technology'),('Kabir Patel','kabir@example.edu','Research Scholar')])
        con.executemany('INSERT INTO reviewers(full_name,email,expertise) VALUES(?,?,?)',[
          ('Dr. Ananya Rao','ananya.rao@example.edu','Machine Learning, AI'),('Dr. Rahul Menon','rahul.menon@example.edu','Data Science, Analytics'),('Dr. Sara Khan','sara.khan@example.edu','Systems, Databases')])
        con.executemany('INSERT INTO papers(submission_code,title,abstract,track_id,corresponding_author_id,status) VALUES(?,?,?,?,?,?)',[
          ('CONF-2026-001','Explainable AI for Student Performance Prediction','A study of interpretable models for educational analytics.',1,1,'Under Review'),
          ('CONF-2026-002','Privacy-Aware Campus Analytics','A framework for responsible data use in smart campuses.',2,2,'Submitted'),
          ('CONF-2026-003','Efficient Indexing for Research Repositories','An evaluation of indexing strategies for academic search.',3,3,'Accepted')])
        con.executemany('INSERT INTO paper_versions(paper_id,version_no,file_name) VALUES(?,?,?)',[(1,1,'explainable_ai_v1.pdf'),(2,1,'campus_analytics_v1.pdf'),(3,1,'indexing_v1.pdf')])
        con.execute('INSERT INTO assignments(paper_id,reviewer_id) VALUES(1,1)')
        con.execute("INSERT INTO reviews(assignment_id,originality,quality,clarity,recommendation,comments) VALUES(1,8,9,8,'Minor Revision','Strong approach; clarify the evaluation dataset.')")
        con.execute("INSERT INTO decisions(paper_id,decision,notes) VALUES(3,'Accepted','Accepted after review.')")
        con.execute("INSERT INTO presentation_slots(paper_id,room,starts_at,duration_minutes) VALUES(3,'Innovation Hall','2026-11-05T10:00',15)")
    con.commit(); con.close()

@app.context_processor
def common():
    return {'year': datetime.now().year}

@app.route('/')
def dashboard():
    con=connect()
    stats={
      'papers':con.execute('SELECT COUNT(*) FROM papers').fetchone()[0],
      'pending':con.execute("SELECT COUNT(*) FROM papers WHERE status IN ('Submitted','Under Review','Revision Required')").fetchone()[0],
      'reviewers':con.execute('SELECT COUNT(*) FROM reviewers').fetchone()[0],
      'accepted':con.execute("SELECT COUNT(*) FROM papers WHERE status='Accepted'").fetchone()[0],
      'reviews':con.execute('SELECT COUNT(*) FROM reviews').fetchone()[0]}
    recent=con.execute('''SELECT p.*,t.name track,a.full_name author FROM papers p JOIN tracks t ON p.track_id=t.id JOIN authors a ON p.corresponding_author_id=a.id ORDER BY p.id DESC LIMIT 6''').fetchall()
    con.close(); return render_template('dashboard.html',stats=stats,recent=recent,active='dashboard')

@app.route('/papers')
def papers():
    q=request.args.get('q','').strip(); status=request.args.get('status','')
    con=connect(); sql='''SELECT p.*,t.name track,a.full_name author FROM papers p JOIN tracks t ON p.track_id=t.id JOIN authors a ON p.corresponding_author_id=a.id WHERE (p.title LIKE ? OR p.submission_code LIKE ? OR a.full_name LIKE ?)'''; args=[f'%{q}%']*3
    if status: sql+=' AND p.status=?'; args.append(status)
    rows=con.execute(sql+' ORDER BY p.id DESC',args).fetchall(); con.close()
    return render_template('papers.html',papers=rows,q=q,status=status,active='papers')

@app.route('/papers/new',methods=['GET','POST'])
def new_paper():
    con=connect()
    if request.method=='POST':
        title=request.form.get('title','').strip(); abstract=request.form.get('abstract','').strip(); author_name=request.form.get('author','').strip(); email=request.form.get('email','').strip().lower(); affiliation=request.form.get('affiliation','').strip(); track_id=request.form.get('track_id','')
        if not all([title,abstract,author_name,email,affiliation,track_id]): flash('Please complete every field.','error')
        else:
            try:
                cur=con.execute('INSERT INTO authors(full_name,email,affiliation) VALUES(?,?,?) ON CONFLICT(email) DO UPDATE SET full_name=excluded.full_name, affiliation=excluded.affiliation',(author_name,email,affiliation))
                author=con.execute('SELECT id FROM authors WHERE email=?',(email,)).fetchone()['id']
                code='CONF-2026-'+str(con.execute('SELECT COALESCE(MAX(id),0)+1 FROM papers').fetchone()[0]).zfill(3)
                cur=con.execute('INSERT INTO papers(submission_code,title,abstract,track_id,corresponding_author_id) VALUES(?,?,?,?,?)',(code,title,abstract,int(track_id),author)); pid=cur.lastrowid
                con.execute('INSERT INTO paper_versions(paper_id,version_no,file_name) VALUES(?,?,?)',(pid,1,'submission_pending_upload.pdf')); con.commit(); con.close(); flash(f'Paper {code} submitted successfully.','success'); return redirect(url_for('papers'))
            except sqlite3.Error as e: con.rollback(); flash('Could not submit paper: '+str(e),'error')
    tracks=con.execute('SELECT * FROM tracks ORDER BY name').fetchall(); con.close(); return render_template('new_paper.html',tracks=tracks,active='papers')

@app.route('/papers/<int:pid>',methods=['GET','POST'])
def paper_detail(pid):
    con=connect()
    if request.method=='POST':
        action=request.form.get('action')
        try:
            if action=='status': con.execute('UPDATE papers SET status=? WHERE id=?',(request.form['status'],pid))
            elif action=='assign': con.execute('INSERT INTO assignments(paper_id,reviewer_id) VALUES(?,?)',(pid,int(request.form['reviewer_id'])))
            elif action=='review':
                aid=int(request.form['assignment_id']); scores=[int(request.form[k]) for k in ('originality','quality','clarity')]
                con.execute('INSERT INTO reviews(assignment_id,originality,quality,clarity,recommendation,comments) VALUES(?,?,?,?,?,?) ON CONFLICT(assignment_id) DO UPDATE SET originality=excluded.originality,quality=excluded.quality,clarity=excluded.clarity,recommendation=excluded.recommendation,comments=excluded.comments,reviewed_at=CURRENT_TIMESTAMP',(aid,*scores,request.form['recommendation'],request.form['comments']))
                con.execute("UPDATE papers SET status='Under Review' WHERE id=? AND status='Submitted'",(pid,))
            elif action=='decision':
                decision=request.form['decision']; con.execute('INSERT INTO decisions(paper_id,decision,notes) VALUES(?,?,?) ON CONFLICT(paper_id) DO UPDATE SET decision=excluded.decision,notes=excluded.notes,decided_at=CURRENT_TIMESTAMP',(pid,decision,request.form.get('notes',''))); con.execute('UPDATE papers SET status=? WHERE id=?',(decision,pid))
            elif action=='schedule': con.execute('INSERT INTO presentation_slots(paper_id,room,starts_at,duration_minutes) VALUES(?,?,?,?) ON CONFLICT(paper_id) DO UPDATE SET room=excluded.room,starts_at=excluded.starts_at,duration_minutes=excluded.duration_minutes',(pid,request.form['room'],request.form['starts_at'],int(request.form['duration_minutes'])))
            elif action=='version':
                version=con.execute('SELECT COALESCE(MAX(version_no),0)+1 FROM paper_versions WHERE paper_id=?',(pid,)).fetchone()[0]
                con.execute('INSERT INTO paper_versions(paper_id,version_no,file_name) VALUES(?,?,?)',(pid,version,request.form['file_name'].strip()))
            con.commit(); flash('Changes saved successfully.','success')
        except (sqlite3.Error,ValueError,KeyError) as e: con.rollback(); flash('Action could not be completed. Check required fields and rules. '+str(e),'error')
    paper=con.execute('''SELECT p.*,t.name track,a.full_name author,a.email,a.affiliation FROM papers p JOIN tracks t ON p.track_id=t.id JOIN authors a ON p.corresponding_author_id=a.id WHERE p.id=?''',(pid,)).fetchone()
    if not paper: con.close(); return ('Paper not found',404)
    reviewers=con.execute('SELECT * FROM reviewers ORDER BY full_name').fetchall()
    assignments=con.execute('''SELECT x.id assignment_id,r.full_name,r.expertise,v.id review_id,v.originality,v.quality,v.clarity,v.recommendation,v.comments FROM assignments x JOIN reviewers r ON x.reviewer_id=r.id LEFT JOIN reviews v ON v.assignment_id=x.id WHERE x.paper_id=?''',(pid,)).fetchall()
    versions=con.execute('SELECT * FROM paper_versions WHERE paper_id=? ORDER BY version_no DESC',(pid,)).fetchall(); decision=con.execute('SELECT * FROM decisions WHERE paper_id=?',(pid,)).fetchone(); slot=con.execute('SELECT * FROM presentation_slots WHERE paper_id=?',(pid,)).fetchone(); con.close()
    return render_template('paper_detail.html',paper=paper,reviewers=reviewers,assignments=assignments,versions=versions,decision=decision,slot=slot,active='papers')

@app.route('/reviewers',methods=['GET','POST'])
def reviewers_page():
    con=connect()
    if request.method=='POST':
        try: con.execute('INSERT INTO reviewers(full_name,email,expertise) VALUES(?,?,?)',(request.form['full_name'].strip(),request.form['email'].strip().lower(),request.form['expertise'].strip())); con.commit(); flash('Reviewer added.','success')
        except sqlite3.Error as e: con.rollback(); flash('Reviewer not added. Email must be unique. '+str(e),'error')
    rows=con.execute('''SELECT r.*,COUNT(DISTINCT a.id) assigned,COUNT(v.id) reviewed FROM reviewers r LEFT JOIN assignments a ON a.reviewer_id=r.id LEFT JOIN reviews v ON v.assignment_id=a.id GROUP BY r.id ORDER BY r.full_name''').fetchall(); con.close(); return render_template('reviewers.html',reviewers=rows,active='reviewers')

@app.route('/schedule')
def schedule():
    con=connect(); rows=con.execute('''SELECT s.*,p.submission_code,p.title,a.full_name author FROM presentation_slots s JOIN papers p ON p.id=s.paper_id JOIN authors a ON a.id=p.corresponding_author_id ORDER BY s.starts_at''').fetchall(); con.close(); return render_template('schedule.html',slots=rows,active='schedule')

@app.route('/reports')
def reports():
    con=connect(); statuses=con.execute('SELECT status,COUNT(*) total FROM papers GROUP BY status ORDER BY status').fetchall(); tracks=con.execute('SELECT t.name,COUNT(p.id) total FROM tracks t LEFT JOIN papers p ON p.track_id=t.id GROUP BY t.id ORDER BY total DESC').fetchall(); workload=con.execute('''SELECT r.full_name,COUNT(DISTINCT a.id) assigned,COUNT(v.id) completed,ROUND(AVG((v.originality+v.quality+v.clarity)/3.0),2) avg_score FROM reviewers r LEFT JOIN assignments a ON a.reviewer_id=r.id LEFT JOIN reviews v ON v.assignment_id=a.id GROUP BY r.id ORDER BY assigned DESC''').fetchall(); scores=con.execute('''SELECT p.id,p.submission_code,p.title,ROUND(AVG((v.originality+v.quality+v.clarity)/3.0),2) avg_score,COUNT(v.id) review_count FROM papers p LEFT JOIN assignments a ON a.paper_id=p.id LEFT JOIN reviews v ON v.assignment_id=a.id GROUP BY p.id ORDER BY avg_score DESC''').fetchall(); con.close(); return render_template('reports.html',statuses=statuses,tracks=tracks,workload=workload,scores=scores,active='reports')

@app.route('/export.csv')
def export_csv():
    con=connect(); rows=con.execute('SELECT p.submission_code,p.title,t.name track,a.full_name author,p.status,p.submitted_at FROM papers p JOIN tracks t ON t.id=p.track_id JOIN authors a ON a.id=p.corresponding_author_id ORDER BY p.id').fetchall(); con.close()
    output=io.StringIO(); writer=csv.writer(output); writer.writerow(['Submission Code','Title','Track','Author','Status','Submitted At']); writer.writerows([tuple(r) for r in rows]); data=io.BytesIO(output.getvalue().encode('utf-8-sig')); data.seek(0); return send_file(data,mimetype='text/csv',as_attachment=True,download_name='conference_paper_report.csv')

@app.route('/health')
def health(): return {'status':'ok','database':'SQLite','application':'Conference Review System'}

init_db()
if __name__=='__main__': app.run(debug=True, port=5000)
