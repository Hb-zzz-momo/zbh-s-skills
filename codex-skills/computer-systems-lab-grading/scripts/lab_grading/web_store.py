"""Durable teaching registry. The grading engine retains its own immutable ledger."""
import contextlib
import json
from pathlib import Path
import sqlite3
import unicodedata
import uuid

from .engine import require, load_rubric
from .storage import now


def clean(value):
    return unicodedata.normalize('NFKC', str(value or '')).strip()


def identifier(value):
    import re
    require(isinstance(value,str) and re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',value), 'invalid resource ID')
    return value


class CatalogStore:
    def __init__(self, root):
        self.root=Path(root).resolve()
        self.root.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            INSERT OR IGNORE INTO metadata VALUES('schema','1');
            INSERT OR IGNORE INTO metadata VALUES('catalog_revision','0');
            CREATE TABLE IF NOT EXISTS groups(id TEXT PRIMARY KEY,name TEXT NOT NULL,term TEXT NOT NULL,assignments TEXT NOT NULL,UNIQUE(name,term));
            CREATE TABLE IF NOT EXISTS group_sources(group_id TEXT REFERENCES groups(id),source_group_id TEXT REFERENCES groups(id),PRIMARY KEY(group_id,source_group_id));
            CREATE TABLE IF NOT EXISTS students(id TEXT PRIMARY KEY,number TEXT NOT NULL UNIQUE,name TEXT NOT NULL,gender TEXT NOT NULL,notes TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS memberships(group_id TEXT REFERENCES groups(id),student_id TEXT REFERENCES students(id),PRIMARY KEY(group_id,student_id));
            CREATE TABLE IF NOT EXISTS reports(
              id TEXT PRIMARY KEY,group_id TEXT NOT NULL REFERENCES groups(id),student_id TEXT REFERENCES students(id),
              experiment_id TEXT NOT NULL,filename TEXT NOT NULL,stored_file TEXT NOT NULL,sha256 TEXT NOT NULL,size INTEGER NOT NULL,
              active INTEGER NOT NULL DEFAULT 1,engine_submission_id TEXT,job_id TEXT,match_reason TEXT NOT NULL,
              revision INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS report_scope ON reports(group_id,student_id,experiment_id);
            CREATE TABLE IF NOT EXISTS tasks(
              id TEXT PRIMARY KEY,report_id TEXT NOT NULL REFERENCES reports(id),action TEXT NOT NULL,state TEXT NOT NULL,
              actor TEXT NOT NULL,reason TEXT NOT NULL,owner_pid INTEGER,error TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
            CREATE UNIQUE INDEX IF NOT EXISTS active_task ON tasks(report_id) WHERE state IN ('queued','running');
            CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,resource_id TEXT,actor TEXT NOT NULL,reason TEXT NOT NULL,payload TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1),value TEXT NOT NULL,revision INTEGER NOT NULL DEFAULT 0);
            ''')
            require(db.execute("SELECT value FROM metadata WHERE key='schema'").fetchone()[0]=='1','unsupported teaching database')
            columns={r['name'] for r in db.execute('PRAGMA table_info(reports)')}
            if 'version_hint' not in columns:db.execute("ALTER TABLE reports ADD COLUMN version_hint TEXT NOT NULL DEFAULT '{}'")
            if 'deleted_at' not in columns:db.execute('ALTER TABLE reports ADD COLUMN deleted_at TEXT')

    @contextlib.contextmanager
    def connect(self, write=False):
        db=sqlite3.connect(self.root/'teaching.sqlite3',timeout=30)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            if write: db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally: db.close()

    def path(self, relative):
        result=(self.root/relative).resolve()
        require(result.is_relative_to(self.root),'path outside workspace')
        return result

    @staticmethod
    def event(db,kind,resource_id,actor,reason,payload=None):
        db.execute('INSERT INTO events(kind,resource_id,actor,reason,payload,created_at) VALUES(?,?,?,?,?,?)',
                   (kind,resource_id,actor,reason,json.dumps(payload or {},ensure_ascii=False),now()))

    def catalog(self):
        with self.connect() as db:
            groups=[{**dict(g),'assignments':json.loads(g['assignments']),'demo':False} for g in db.execute('SELECT * FROM groups ORDER BY term,name')]
            students=[{**dict(s),'demo':False} for s in db.execute('SELECT * FROM students ORDER BY number')]
            memberships=[dict(groupId=m['group_id'],studentId=m['student_id']) for m in db.execute('SELECT * FROM memberships')]
            sources=[tuple(r) for r in db.execute('SELECT group_id,source_group_id FROM group_sources ORDER BY source_group_id')]
            revision=int(db.execute("SELECT value FROM metadata WHERE key='catalog_revision'").fetchone()[0])
        for g in groups:
            g['sourceGroupIds']=[s for parent,s in sources if parent==g['id']]
            if g['sourceGroupIds']:
                g['assignments']=sorted({exp for child in groups if child['id'] in g['sourceGroupIds'] for exp in child['assignments']})
                memberships.extend(dict(groupId=g['id'],studentId=s) for s in sorted({m['studentId'] for m in memberships if m['groupId'] in g['sourceGroupIds']}))
        return dict(groups=groups,students=students,memberships=memberships,revision=revision)

    def replace_catalog(self, groups,students,memberships, expected_revision,actor):
        """Bounded bulk catalog edit with optimistic locking; grades are not accepted."""
        require(len(groups)<=1000 and len(students)<=20000 and len(memberships)<=50000,'catalog too large')
        gids,sids,numbers=set(),set(),set()
        for g in groups:
            require(set(('id','name','term','assignments'))<=set(g) and isinstance(g['assignments'],list),'invalid group fields')
            identifier(g['id']); require(g['id'] not in gids,'duplicate group ID');gids.add(g['id'])
            require(clean(g['name']) and len(g['name'])<=120 and len(g['term'])<=100,'invalid group name/term')
            require(len(g['assignments'])==len(set(g['assignments'])),'duplicate assignments')
            for exp in g['assignments']:load_rubric(exp)
        for s in students:
            require(set(('id','number','name','gender','notes'))<=set(s),'invalid student fields')
            identifier(s['id']); require(s['id'] not in sids,'duplicate student ID');sids.add(s['id'])
            number=clean(s['number'])
            import re
            require(bool(re.fullmatch(r'[A-Za-z0-9._-]{1,64}',number)) and number not in numbers,'duplicate/invalid student number');numbers.add(number)
            require(clean(s['name']) and len(s['name'])<=80 and len(s['gender'])<=30 and len(s['notes'])<=4000,'invalid student profile')
        require(all(set(('groupId','studentId'))<=set(m) for m in memberships),'invalid membership fields')
        relations={(m['groupId'],m['studentId']) for m in memberships}
        require(len(relations)==len(memberships) and all(g in gids and s in sids for g,s in relations),'invalid membership')
        by_id={g['id']:g for g in groups}
        sources={g['id']:g.get('sourceGroupIds',[]) for g in groups}
        for gid,children in sources.items():
            require(isinstance(children,list) and len(children)==len(set(children)),'汇总来源不能重复')
            require(not children or len(children)>=2,'汇总分组至少包含两个班级')
            require(all(child in gids and child!=gid and not sources[child] for child in children),'汇总来源必须是已有普通分组，不能嵌套或引用自己')
            require(all(clean(by_id[child]['term'])==clean(by_id[gid]['term']) for child in children),'汇总分组与来源班级必须属于同一届别/学期')
            allowed={s for g,s in relations if g in children}
            require(all(s in allowed for g,s in relations if g==gid) if children else True,'请在原班级添加学生，汇总名单自动更新')
        direct_relations={(g,s) for g,s in relations if not sources[g]}
        with self.connect(True) as db:
            revision=int(db.execute("SELECT value FROM metadata WHERE key='catalog_revision'").fetchone()[0])
            require(revision==expected_revision,'stale catalog revision; reload')
            oldg={r[0] for r in db.execute('SELECT id FROM groups')}
            olds={r['id']:r['number'] for r in db.execute('SELECT id,number FROM students')}
            oldrelations={(r[0],r[1]) for r in db.execute('SELECT group_id,student_id FROM memberships')}
            require(oldg<=gids and set(olds)<=sids and oldrelations<=direct_relations,'deletion requires dedicated archival workflow')
            oldsources=[tuple(r) for r in db.execute('SELECT group_id,source_group_id FROM group_sources')]
            for gid in oldg:
                previous={s for parent,s in oldsources if parent==gid}
                require(bool(sources[gid])==bool(previous) and previous<=set(sources[gid]),
                        '已有分组的类型和已纳入的来源不可移除；汇总分组仅可补充来源班级')
            require(all(s['id'] not in olds or olds[s['id']]==clean(s['number']) for s in students),'student number change requires identity migration')
            for g in groups:
                db.execute('INSERT INTO groups VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,term=excluded.term,assignments=excluded.assignments',
                           (g['id'],clean(g['name']),clean(g['term']),json.dumps(g['assignments'])))
            for s in students:
                db.execute('INSERT INTO students VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,gender=excluded.gender,notes=excluded.notes',
                           (s['id'],clean(s['number']),clean(s['name']),clean(s['gender']),s['notes']))
            db.executemany('INSERT OR IGNORE INTO memberships VALUES(?,?)',direct_relations)
            db.executemany('INSERT OR IGNORE INTO group_sources VALUES(?,?)',[(g,s) for g,children in sources.items() for s in children])
            added_sources={(g,s) for g,children in sources.items() for s in children if g in oldg}-set(oldsources)
            for gid in sorted({g for g,_ in added_sources}):
                self.event(db,'group_sources_extended',gid,actor,'补充汇总分组来源，保留原有学生和成绩',
                           {'added_source_group_ids':sorted(s for g,s in added_sources if g==gid)})
            db.execute("UPDATE metadata SET value=? WHERE key='catalog_revision'",(str(revision+1),))
            self.event(db,'catalog_saved',None,actor,'保存名单与分组',{'groups':len(groups),'students':len(students)})
        return self.catalog()

    def import_roster(self, rows,term='',target_group_id=None,source='花名册',actor='本地教师'):
        """Reuse identities by student number. A conflicting name rolls back the batch."""
        catalog=self.catalog()
        added=linked=duplicates=0
        for r in rows:
            require(set(('number','name'))<=set(r),'roster missing number/name')
            number,name=clean(r['number']),clean(r['name'])
            if number=='学号' and name=='姓名':continue
            require(number and name,'roster missing number/name')
            g=next((g for g in catalog['groups'] if g['id']==target_group_id),None) if target_group_id else next((g for g in catalog['groups'] if g['name']==clean(r.get('group')) and g['term']==clean(term)),None)
            if target_group_id:require(g is not None,'target group unavailable')
            require(not g or not g.get('sourceGroupIds'),'请向原班级导入花名册，汇总名单会自动更新')
            if g is None:
                require(clean(r.get('group')),'roster missing group')
                g=dict(id=uuid.uuid4().hex,name=clean(r['group']),term=clean(term),assignments=[f'exp{n:02}' for n in range(1,17)])
                catalog['groups'].append(g)
            s=next((s for s in catalog['students'] if s['number']==number),None)
            require(s is None or s['name']==name,'same student number has conflicting names')
            if s is None:
                s=dict(id=uuid.uuid4().hex,number=number,name=name,gender=clean(r.get('gender')),notes='')
                catalog['students'].append(s);added+=1
            relation=dict(groupId=g['id'],studentId=s['id'])
            if relation in catalog['memberships']:duplicates+=1
            else:catalog['memberships'].append(relation);linked+=1
        result=self.replace_catalog(catalog['groups'],catalog['students'],catalog['memberships'],catalog['revision'],actor)
        return dict(catalog=result,added=added,linked=linked,duplicates=duplicates,source=source)

    def report(self,rid):
        identifier(rid)
        with self.connect() as db:row=db.execute('SELECT * FROM reports WHERE id=?',(rid,)).fetchone()
        require(row is not None,'report not found')
        return dict(row)

    def reports(self,group_id=None,limit=200,offset=0,*,deleted=False):
        scope=self.group_scope(group_id) if group_id else []
        where=' WHERE deleted_at IS '+('NOT NULL' if deleted else 'NULL')
        if scope:where+=' AND group_id IN ('+','.join('?' for _ in scope)+')'
        args=scope
        with self.connect() as db:
            total=db.execute('SELECT COUNT(*) FROM reports'+where,args).fetchone()[0]
            rows=[dict(r) for r in db.execute('SELECT * FROM reports'+where+' ORDER BY created_at DESC,id LIMIT ? OFFSET ?',args+[limit,offset])]
        return rows,total

    def group_scope(self,group_id):
        g=next((g for g in self.catalog()['groups'] if g['id']==group_id),None)
        require(g is not None,'分组不存在')
        return [group_id,*g['sourceGroupIds']]

    def events(self,rid):
        with self.connect() as db:
            return [dict(time=e['created_at'],actor=e['actor'],action=e['reason'],kind=e['kind']) for e in db.execute('SELECT * FROM events WHERE resource_id=? ORDER BY id',(rid,))]

    def task(self,tid):
        identifier(tid)
        with self.connect() as db:row=db.execute('SELECT * FROM tasks WHERE id=?',(tid,)).fetchone()
        require(row is not None,'task not found')
        return dict(row)

    def active(self,rid=None):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM tasks WHERE state IN ('queued','running')"+(' AND report_id=?' if rid else ''),[rid] if rid else [])]
