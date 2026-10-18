"""SQLite ledger: immutable submissions, explicit version choice, durable jobs."""
import contextlib
import datetime
import json
from pathlib import Path
import sqlite3
import uuid

from .engine import require


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Store:
    def __init__(self, root):
        """Keep local evidence and grades in one explicit data root, outside source."""
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                INSERT OR IGNORE INTO metadata VALUES('schema_version','1');
                CREATE TABLE IF NOT EXISTS submissions(
                  id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL, student_key TEXT NOT NULL,
                  report_sha256 TEXT NOT NULL, original_name TEXT NOT NULL, original_path TEXT NOT NULL,
                  stored_file TEXT NOT NULL, created_at TEXT NOT NULL,
                  UNIQUE(experiment_id,student_key,report_sha256));
                CREATE TABLE IF NOT EXISTS selections(
                  experiment_id TEXT NOT NULL, student_key TEXT NOT NULL,
                  submission_id TEXT REFERENCES submissions(id), explicit INTEGER NOT NULL DEFAULT 0,
                  PRIMARY KEY(experiment_id,student_key));
                CREATE TABLE IF NOT EXISTS jobs(
                  id TEXT PRIMARY KEY,submission_id TEXT NOT NULL REFERENCES submissions(id),
                  state TEXT NOT NULL,revision INTEGER NOT NULL DEFAULT 0,
                  configuration TEXT NOT NULL, rubric TEXT NOT NULL,
                  context TEXT, result TEXT, error TEXT, worker_token TEXT, started_at TEXT,
                  created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS attempts(
                  id TEXT PRIMARY KEY,job_id TEXT NOT NULL REFERENCES jobs(id),
                  created_at TEXT NOT NULL,metadata TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS reviews(
                  id TEXT PRIMARY KEY,job_id TEXT NOT NULL REFERENCES jobs(id),revision INTEGER NOT NULL,
                  created_at TEXT NOT NULL,reviewer TEXT NOT NULL,reason TEXT NOT NULL,result TEXT NOT NULL,
                  UNIQUE(job_id,revision));
                CREATE TABLE IF NOT EXISTS publications(
                  id TEXT PRIMARY KEY,job_id TEXT NOT NULL REFERENCES jobs(id),review_id TEXT NOT NULL REFERENCES reviews(id),
                  created_at TEXT NOT NULL,score REAL NOT NULL, UNIQUE(job_id,review_id));
                CREATE TABLE IF NOT EXISTS events(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT NOT NULL,kind TEXT NOT NULL,payload TEXT NOT NULL);
            ''')
            require(db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == '1', 'unsupported database schema')

    @contextlib.contextmanager
    def connect(self):
        """Rollback on exceptions; callers never get a half-written grade state."""
        db = sqlite3.connect(self.root/'grading.sqlite3', timeout=30)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def path(self, relative):
        """Even persisted paths are constrained to the chosen data directory."""
        result = (self.root/relative).resolve()
        require(result.is_relative_to(self.root), 'path outside data root')
        return result

    def event(self, db, kind, payload):
        db.execute('INSERT INTO events(created_at,kind,payload) VALUES(?,?,?)', (now(),kind,json.dumps(payload,ensure_ascii=False)))

    def submission(self, sid):
        with self.connect() as db:
            row=db.execute('SELECT * FROM submissions WHERE id=?',(sid,)).fetchone()
            require(row is not None,'submission not found')
            return dict(row)

    def add_submission(self, item):
        """A second distinct version clears implicit selection, never picks latest."""
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old=db.execute('SELECT * FROM submissions WHERE experiment_id=? AND student_key=? AND report_sha256=?',
                           (item['experiment_id'],item['student_key'],item['report_sha256'])).fetchone()
            if old:
                return dict(old),False
            fields=('id','experiment_id','student_key','report_sha256','original_name','original_path','stored_file','created_at')
            db.execute('INSERT INTO submissions VALUES(?,?,?,?,?,?,?,?)',tuple(item[k] for k in fields))
            selection=db.execute('SELECT * FROM selections WHERE experiment_id=? AND student_key=?',
                                 (item['experiment_id'],item['student_key'])).fetchone()
            if selection is None:
                db.execute('INSERT INTO selections VALUES(?,?,?,0)',(item['experiment_id'],item['student_key'],item['id']))
            elif not selection['explicit']:
                db.execute('UPDATE selections SET submission_id=NULL WHERE experiment_id=? AND student_key=?',
                           (item['experiment_id'],item['student_key']))
            self.event(db,'submission_imported',{'submission_id':item['id']})
        return item,True

    def selected(self, submission):
        with self.connect() as db:
            row=db.execute('SELECT submission_id FROM selections WHERE experiment_id=? AND student_key=?',
                           (submission['experiment_id'],submission['student_key'])).fetchone()
            return row is not None and row['submission_id']==submission['id']

    def select(self, sid, actor, reason):
        """Explicit selection is auditable and does not rewrite old grading jobs."""
        require(actor.strip() and reason.strip(),'selection requires actor and reason')
        s=self.submission(sid)
        with self.connect() as db:
            db.execute('UPDATE selections SET submission_id=?,explicit=1 WHERE experiment_id=? AND student_key=?',
                       (sid,s['experiment_id'],s['student_key']))
            self.event(db,'version_selected',{'submission_id':sid,'actor':actor,'reason':reason})

    def clear_selection(self, sid, actor, reason):
        """An ambiguous intake selection cannot leave an old engine version active."""
        require(actor.strip() and reason.strip(),'selection requires actor and reason')
        s=self.submission(sid)
        with self.connect() as db:
            db.execute('UPDATE selections SET submission_id=NULL,explicit=0 WHERE experiment_id=? AND student_key=?',
                       (s['experiment_id'],s['student_key']))
            self.event(db,'version_selection_cleared',{'submission_id':sid,'actor':actor,'reason':reason})

    def create_job(self, sid, rubric, configuration):
        self.submission(sid)
        jid=uuid.uuid4().hex
        with self.connect() as db:
            db.execute('INSERT INTO jobs(id,submission_id,state,configuration,rubric,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',
                       (jid,sid,'received',json.dumps(configuration),json.dumps(rubric,ensure_ascii=False),now(),now()))
            self.event(db,'job_created',{'job_id':jid,'submission_id':sid})
        return self.job(jid)

    def job(self, jid):
        with self.connect() as db:
            row=db.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
            require(row is not None,'job not found')
            result=dict(row)
            for key in ('configuration','rubric','context','result'):
                if result[key] is not None:
                    result[key]=json.loads(result[key])
            return result

    def transition(self, jid, expected_states, state, *, context=None, result=None, error=None, worker_token=None):
        """Compare state inside a write transaction; two workers cannot both claim."""
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old=db.execute('SELECT state,worker_token FROM jobs WHERE id=?',(jid,)).fetchone()
            require(old is not None and old['state'] in expected_states,'job state changed; reload before retry')
            if old['state'] in ('judging','extracting'):
                require(old['worker_token']==worker_token and worker_token,'worker ownership mismatch')
            db.execute('UPDATE jobs SET state=?,context=COALESCE(?,context),result=COALESCE(?,result),error=?,worker_token=?,started_at=?,revision=revision+1,updated_at=? WHERE id=?',
                       (state,json.dumps(context,ensure_ascii=False) if context is not None else None,
                        json.dumps(result,ensure_ascii=False) if result is not None else None,error,
                        worker_token if state in ('judging','extracting') else None,now() if state in ('judging','extracting') else None,now(),jid))
            self.event(db,'job_transition',{'job_id':jid,'from':old['state'],'to':state})
        return self.job(jid)

    def attempt(self, jid, metadata):
        """Store only explicit safe metadata; authorization headers never enter here."""
        aid=uuid.uuid4().hex
        with self.connect() as db:
            db.execute('INSERT INTO attempts VALUES(?,?,?,?)',(aid,jid,now(),json.dumps(metadata,ensure_ascii=False)))
        return aid

    def list_jobs(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT j.id,j.submission_id,j.state,j.revision,j.error,s.experiment_id,s.student_key FROM jobs j JOIN submissions s ON s.id=j.submission_id ORDER BY j.created_at')]

    def list_submissions(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT s.*,v.submission_id=s.id AS selected FROM submissions s LEFT JOIN selections v ON s.experiment_id=v.experiment_id AND s.student_key=v.student_key ORDER BY s.created_at')]
