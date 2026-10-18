"""Durable sequential jobs. A server crash never implies permission to call again."""
import os
import threading
import uuid

from .engine import require
from .storage import now
from .transport import Configuration
from .web_store import identifier
from .workflow import _process_alive


class TaskWorker:
    def __init__(self,service):
        self.service=service
        self.stop_event=threading.Event()
        self.wake=threading.Event()
        self.thread=None

    def start(self):
        with self.service.store.connect(True) as db:
            running=db.execute("SELECT * FROM tasks WHERE state='running'").fetchall()
            for task in running:
                require(not task['owner_pid'] or not _process_alive(task['owner_pid']),'另一个评分服务仍在运行')
                db.execute("UPDATE tasks SET state='interrupted',error=?,updated_at=? WHERE id=?",('服务中断；请核对调用记录并手动恢复',now(),task['id']))
        self.thread=threading.Thread(target=self.loop,name='lab-grading-worker',daemon=True)
        self.thread.start()

    def close(self):
        self.stop_event.set();self.wake.set()
        if self.thread:self.thread.join(timeout=2)

    def enqueue(self,rid,action,revision,actor,reason,request_id):
        require(action in ('prepare','run','retry','recheck','recover','new-run'),'未知任务动作')
        require(actor.strip() and reason.strip(),'请填写操作者和理由')
        identifier(request_id)
        s=self.service
        with s.lock:
            with s.store.connect() as db:
                old=db.execute('SELECT * FROM tasks WHERE id=?',(request_id,)).fetchone()
            if old:
                require(old['report_id']==rid and old['action']==action,'请求编号已用于其他操作')
                return dict(old)
            r=s.check_report(rid,revision)
            require(r['active'] and r['student_id'],'请先匹配学生并选择报告版本')
            s.require_scope_idle(r['group_id'],r['student_id'],r['experiment_id'])
            s.require_unpublished_submission(r)
            backend=s.backend(r['group_id'])
            state=backend.store.job(r['job_id'])['state'] if r['job_id'] else 'received'
            allowed={'prepare':('received','extraction_failed'), 'run':('received','ready','extraction_failed'),
                     'retry':('extraction_failed','retryable_failed','model_failed'), 'recheck':('model_failed','needs_review'),
                     'recover':('extracting','judging'), 'new-run':('received','needs_review','ready_for_teacher_review','reviewed','model_failed','retryable_failed','extraction_failed','ready')}
            require(state in allowed[action],'当前状态不能执行该动作')
            if action in ('new-run','recheck'):
                current=s.describe(r)
                flag,reason_field=('canRegrade','regradeBlockedReason') if action=='new-run' else ('canRecheck','recheckBlockedReason')
                require(current[flag],current[reason_field] or '当前状态不能执行该动作')
            if action in ('run','retry','new-run'):
                config=Configuration(**(backend.store.job(r['job_id'])['configuration'] if r['job_id'] and action!='new-run' else s.settings()['configuration']))
                try:config.credential()
                except (OSError,ValueError):raise ValueError('尚未配置可用的模型密钥，请到系统设置检查') from None
            backend.store.select(r['engine_submission_id'],actor,reason)
            with s.store.connect(True) as db:
                db.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?)',(request_id,rid,action,'queued',actor,reason,None,None,now(),now()))
                db.execute('UPDATE reports SET revision=revision+1 WHERE id=?',(rid,))
                s.store.event(db,'task_queued',rid,actor,reason,{'task_id':request_id,'action':action})
            self.wake.set()
            return s.store.task(request_id)

    def execute_one(self):
        s=self.service
        with s.lock,s.store.connect(True) as db:
            row=db.execute("SELECT * FROM tasks WHERE state='queued' ORDER BY created_at LIMIT 1").fetchone()
            if not row:return False
            task=dict(row)
            db.execute("UPDATE tasks SET state='running',owner_pid=?,updated_at=? WHERE id=?",(os.getpid(),now(),task['id']))
        try:
            with s.lock:
                r=s.store.report(task['report_id']);require(r['active'],'任务所选版本已改变')
                s.require_unpublished_submission(r)
                backend=s.backend(r['group_id'])
                if not r['job_id'] or task['action']=='new-run':
                    job=backend.create_job(r['engine_submission_id'],Configuration(**s.settings()['configuration']))
                    with s.store.connect(True) as db:
                        db.execute('UPDATE reports SET job_id=?,revision=revision+1 WHERE id=?',(job['id'],r['id']))
                        if task['action']=='new-run':
                            s.store.event(db,'regrade_started',r['id'],task['actor'],task['reason'],
                                          {'previous_job_id':r['job_id'],'job_id':job['id'],'task_id':task['id']})
                else:job=backend.store.job(r['job_id'])
            action=task['action']
            if action=='recover':backend.recover(job['id'],reviewer=task['actor'],reason=task['reason'])
            elif action=='recheck':backend.recheck(job['id'])
            else:
                if job['state'] in ('received','extraction_failed'):job=backend.prepare(job['id'])
                if action!='prepare':backend.run(job['id'])
            state,error='done',None
        except Exception as exc:
            # Transport exceptions contain codes, never credentials. Avoid repr/config dumps.
            state,error='failed',(type(exc).__name__+': '+str(exc))[:600]
        with s.lock,s.store.connect(True) as db:
            db.execute('UPDATE tasks SET state=?,error=?,updated_at=? WHERE id=?',(state,error,now(),task['id']))
            db.execute('UPDATE reports SET revision=revision+1 WHERE id=?',(task['report_id'],))
            s.store.event(db,'task_'+state,task['report_id'],task['actor'],error or '任务完成',{'task_id':task['id']})
        return True

    def loop(self):
        while not self.stop_event.is_set():
            if not self.execute_one():
                self.wake.wait(2);self.wake.clear()


class OwnerLock:
    """OS lock releases after process death. PID files alone cannot enforce ownership."""
    def __init__(self,path):self.path=path;self.file=None
    def acquire(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.file=self.path.open('a+b');self.file.seek(0)
        if self.file.read(1)==b'':self.file.write(b'0');self.file.flush()
        self.file.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.file.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            self.file.close();self.file=None
            raise ValueError('数据目录已被另一个服务使用') from None
    def close(self):
        if self.file:self.file.close();self.file=None
