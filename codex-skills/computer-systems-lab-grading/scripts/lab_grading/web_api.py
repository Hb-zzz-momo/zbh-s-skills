"""Loopback-only HTTP adapter; no arbitrary file paths or client-written grades."""
from contextlib import asynccontextmanager
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .engine import load_rubric, require
from .transport import Configuration
from .web_service import TeachingService
from .web_worker import TaskWorker, OwnerLock
from .web_backup import create_backup
from .web_store import identifier


class Input(BaseModel):
    model_config=ConfigDict(extra='forbid')

class Group(Input):
    id:str
    name:str=Field(min_length=1,max_length=120)
    term:str=Field(default='',max_length=100)
    assignments:list[str]=Field(max_length=16)
    demo:bool=False
    sourceGroupIds:list[str]=Field(default_factory=list,max_length=1000)
class Student(Input):
    id:str
    number:str=Field(min_length=1,max_length=64)
    name:str=Field(min_length=1,max_length=80)
    gender:str=Field(default='',max_length=30)
    notes:str=Field(default='',max_length=4000)
    demo:bool=False
class Membership(Input):
    groupId:str
    studentId:str
class CatalogInput(Input):
    groups:list[Group]=Field(max_length=1000)
    students:list[Student]=Field(max_length=20000)
    memberships:list[Membership]=Field(max_length=50000)
    revision:int=Field(ge=0)
    actor:str=Field(default='本地教师',min_length=1,max_length=80)

class RosterInput(Input):
    rows:list[dict]=Field(max_length=20000)
    term:str=Field(default='',max_length=100)
    target_group_id:str|None=None
    source:str=Field(default='花名册',max_length=200)
    actor:str=Field(default='本地教师',min_length=1,max_length=80)

class ActionInput(Input):
    revision:int=Field(ge=0)
    actor:str=Field(default='本地教师',min_length=1,max_length=80)
    reason:str=Field(min_length=1,max_length=4000)

class BindInput(ActionInput):
    student_id:str
    target_group_id:str|None=None
class TaskInput(ActionInput):
    action:str
    request_id:str
class JobInput(Input):
    report_revision:int=Field(ge=0)
    job_revision:int=Field(ge=0)
    actor:str=Field(min_length=1,max_length=80)
    reason:str=Field(min_length=1,max_length=4000)
class ResolveInput(JobInput):
    identity_status:str|None=None
    clear_flags:list[str]=Field(default_factory=list,max_length=100)
    output_id_match:bool|None=None
class Decision(Input):
    criterion_id:str
    verdict:str
    evidence_ids:list[str]=Field(max_length=5000)
    observation:str=Field(min_length=1,max_length=12000)
    reason:str=Field(min_length=1,max_length=12000)
    missing:bool
class ReviewInput(JobInput):
    decisions:list[Decision]=Field(max_length=1000)
    accept_estimates:bool=False
class ImportConfirmInput(Input):
    group_id:str
    experiment_id:str
    student_id:str|None=None
    reason:str=Field(default='',max_length=4000)
    actor:str=Field(default='本地教师',min_length=1,max_length=80)
    defer_match:bool=False
class PublishInput(JobInput):review_id:str
class SettingsInput(Input):
    configuration:dict
    revision:int=Field(ge=0)
    actor:str=Field(default='本地教师',min_length=1,max_length=80)

class CalibrationInput(Input):
    group_id:str
    experiment_id:str
    policy:dict
    revision:int=Field(default=0,ge=0)
    actor:str=Field(default='本地教师',min_length=1,max_length=80)
    reason:str=Field(default='调整本实验统一评分政策',min_length=1,max_length=1000)

class MigrationInput(Input):
    groups:list[dict]=Field(max_length=1000)
    students:list[dict]=Field(max_length=20000)
    memberships:list[dict]=Field(max_length=50000)


def create_app(root,frontend=None,seed=None,*,start_worker=True,testing=False):
    service=TeachingService(root,seed)
    worker=TaskWorker(service)
    owner=OwnerLock(service.store.path('.owner.lock'))
    sessions={}
    @asynccontextmanager
    async def lifespan(app):
        owner.acquire()
        try:
            if start_worker:worker.start()
            yield
        finally:
            worker.close();owner.close()
    app=FastAPI(title='阅实 · 本机批阅服务',docs_url=None,redoc_url=None,openapi_url=None,lifespan=lifespan)
    app.state.service=service;app.state.worker=worker
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost']+(['testserver'] if testing else []))

    @app.middleware('http')
    async def local_session(request,call_next):
        if request.headers.get('sec-fetch-site') in ('cross-site','same-site'):
            return JSONResponse({'error':'仅允许从本机工作台访问'},403)
        origin=request.headers.get('origin')
        if origin and origin!=str(request.base_url).rstrip('/'):
            return JSONResponse({'error':'访问来源不一致，请从工作台操作'},403)
        if request.url.path.startswith('/api/'):
            if request.method not in ('GET','HEAD'):
                length=request.headers.get('content-length','')
                if not length.isdigit() or int(length)>66*1024*1024:
                    return JSONResponse({'error':'请求过大或缺少长度'},413)
            if request.url.path!='/api/session':
                token=request.cookies.get('lab_session')
                if token not in sessions:return JSONResponse({'error':'会话已失效，请刷新页面'},401)
                if request.method not in ('GET','HEAD') and not secrets.compare_digest(request.headers.get('x-csrf-token',''),sessions[token]):
                    return JSONResponse({'error':'请求校验失效，请刷新页面'},403)
        response=await call_next(request)
        if response.headers.get('content-type')=='application/json':
            response.headers['Content-Type']='application/json; charset=utf-8'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='same-origin'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Cache-Control']='no-store' if request.url.path.startswith('/api/') else 'no-cache'
        response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        return response

    @app.exception_handler(ValueError)
    async def validation_error(request,exc):return JSONResponse({'error':str(exc)[:800]},409 if any(x in str(exc) for x in ('revision','已更新','已被修改','正在处理','concurrent')) else 400)
    @app.exception_handler(sqlite3.IntegrityError)
    async def integrity_error(request,exc):return JSONResponse({'error':'存在重复或冲突记录，请刷新并核对分组、学号与任务'},409)

    @app.get('/api/session')
    def session(request:Request):
        token=request.cookies.get('lab_session')
        if token not in sessions:
            if len(sessions)>200:sessions.clear()
            token=secrets.token_urlsafe(32);sessions[token]=secrets.token_urlsafe(32)
        response=JSONResponse({'csrf':sessions[token],'mode':'local-owner','version':'0.4.0'})
        response.set_cookie('lab_session',token,httponly=True,samesite='strict',path='/')
        return response

    @app.get('/api/workspace')
    def workspace():return service.workspace()
    @app.get('/api/rubrics')
    def rubrics():return [load_rubric(f'exp{i:02}') for i in range(1,17)]
    @app.put('/api/catalog')
    def catalog(value:CatalogInput):
        data=value.model_dump()
        with service.lock:return service.store.replace_catalog(data['groups'],data['students'],data['memberships'],value.revision,value.actor)
    @app.post('/api/roster')
    def roster(value:RosterInput):
        with service.lock:return service.store.import_roster(**value.model_dump())
    @app.post('/api/catalog/migrate')
    def migrate(value:MigrationInput):
        with service.lock:return service.migrate_catalog(value.model_dump())

    @app.post('/api/imports/inspect')
    async def inspect_upload(request:Request):
        from .intake import inspect_file
        async with request.form(max_files=1,max_fields=0,max_part_size=64*1024*1024) as form:
            require(set(form)=={'file'},'识别阶段只需选择报告文件')
            file=form.get('file');require(file and hasattr(file,'filename'),'缺少报告文件')
            name=file.filename or ''
            require(name==Path(name).name and not re.search(r'[\\/:\x00-\x1f]',name) and len(name)<=200,'文件名无效')
            require(Path(name).suffix.lower() in ('.pdf','.doc','.docx'),'仅支持Word/PDF')
            ticket_id=uuid.uuid4().hex;folder=service.store.path('intake/'+ticket_id);folder.mkdir(parents=True)
            path=folder/name
            require(os.name!='nt' or len(str(path))<240,'文件名或数据目录过长，请缩短文件名后重试')
            total=0
            try:
                with path.open('xb') as out:
                    while chunk:=await file.read(1024*1024):
                        total+=len(chunk);require(total<=64*1024*1024,'文件超过64MB');out.write(chunk)
                return await run_in_threadpool(inspect_file,service,path,name,ticket_id)
            except BaseException:
                path.unlink(missing_ok=True)
                # Remove only bounded files created in this request's UUID directory.
                for item in folder.iterdir():
                    if item.is_file():item.unlink()
                folder.rmdir()
                raise

    @app.post('/api/imports/{ticket_id}/confirm')
    def confirm_upload(ticket_id:str,value:ImportConfirmInput):
        from .intake import confirm_file
        return confirm_file(service,ticket_id,**value.model_dump())

    @app.post('/api/reports')
    async def upload(request:Request):
        async with request.form(max_files=1,max_fields=7,max_part_size=64*1024*1024) as form:
            require(set(form)<= {'file','group_id','experiment_id','student_id','reason','actor','defer_match'},'未知上传字段')
            require(form.get('defer_match','false') in ('true','false'),'匹配设置无效')
            file=form.get('file');require(file and hasattr(file,'filename'),'缺少报告文件')
            name=file.filename or ''
            require(name==Path(name).name and not re.search(r'[\\/:\x00-\x1f]',name) and len(name)<=200,'文件名无效')
            require(Path(name).suffix.lower() in ('.pdf','.doc','.docx'),'仅支持Word/PDF')
            folder=service.store.path('originals/'+uuid.uuid4().hex);folder.mkdir(parents=True)
            path=folder/name
            try:
                require(os.name!='nt' or len(str(path))<240,'文件名或数据目录过长，请缩短文件名后重试')
                total=0
                with path.open('xb') as out:
                    while chunk:=await file.read(1024*1024):
                        total+=len(chunk);require(total<=64*1024*1024,'文件超过64MB');out.write(chunk)
                result=await run_in_threadpool(service.ingest,path,name,str(form.get('group_id','')),str(form.get('experiment_id','')),form.get('student_id') or None,str(form.get('reason','')),str(form.get('actor','本地教师')),defer_match=form.get('defer_match')=='true')
                if result['duplicate']:path.unlink();folder.rmdir()
                return result
            except BaseException:
                # Only delete this request's uncommitted UUID staging file.
                with service.store.connect() as db:used=db.execute('SELECT 1 FROM reports WHERE stored_file=?',(str(path.relative_to(service.store.root)),)).fetchone()
                if not used:
                    path.unlink(missing_ok=True);folder.rmdir()
                raise

    @app.get('/api/reports/{rid}')
    def detail(rid:str):return service.detail(rid)
    @app.get('/api/reports/{rid}/original')
    def original(rid:str):
        path,name=service.original(rid);return FileResponse(path,filename=name,media_type='application/octet-stream')
    @app.get('/api/reports/{rid}/evidence/{eid}')
    def evidence(rid:str,eid:str):return FileResponse(service.evidence(rid,eid))
    @app.post('/api/reports/{rid}/bind')
    def bind(rid:str,value:BindInput):return service.bind(rid,**value.model_dump())
    @app.post('/api/reports/{rid}/select')
    def select(rid:str,value:ActionInput):return service.select(rid,**value.model_dump())
    @app.post('/api/reports/{rid}/delete')
    def delete_report(rid:str,value:ActionInput):return service.delete(rid,**value.model_dump())
    @app.post('/api/reports/{rid}/restore')
    def restore_report(rid:str,value:ActionInput):return service.restore(rid,**value.model_dump())
    @app.post('/api/reports/{rid}/tasks')
    def tasks(rid:str,value:TaskInput):return worker.enqueue(rid,**value.model_dump())
    @app.post('/api/reports/{rid}/resolve')
    def resolve(rid:str,value:ResolveInput):return service.job_operation(rid,'resolve',value.model_dump())
    @app.post('/api/reports/{rid}/review')
    def review(rid:str,value:ReviewInput):return service.job_operation(rid,'review',value.model_dump())
    @app.post('/api/reports/{rid}/publish')
    def publish(rid:str,value:PublishInput):return service.job_operation(rid,'publish',value.model_dump())
    @app.get('/api/settings')
    def settings():return service.settings()
    @app.get('/api/calibration')
    def calibration(group_id:str,experiment_id:str):return service.calibration_preview(group_id,experiment_id)
    @app.post('/api/calibration/preview')
    def calibration_preview(value:CalibrationInput):return service.calibration_preview(value.group_id,value.experiment_id,value.policy)
    @app.post('/api/calibration/recommend')
    def calibration_recommend(value:CalibrationInput):return service.calibration_preview(value.group_id,value.experiment_id,value.policy,True)
    @app.put('/api/calibration')
    def save_calibration(value:CalibrationInput):
        service.store.group_scope(value.group_id)
        return service.save_calibration(value.experiment_id,value.policy,value.revision,value.actor,value.reason)
    @app.put('/api/settings')
    def save_settings(value:SettingsInput):return service.save_settings(value.configuration,value.revision,value.actor)
    @app.get('/api/doctor')
    def doctor():
        config=Configuration(**service.settings()['configuration'])
        try:config.credential();credential=True
        except (OSError,ValueError):credential=False
        word=False
        if os.name=='nt':
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,r'Word.Application\CLSID'):word=True
            except OSError:pass
        return dict(credential_configured=credential,word_registered=word,word_note='已注册不代表转换必成功，请用报告验证',dependencies={m:bool(importlib.util.find_spec(m)) for m in ('pypdfium2','PIL')},active_tasks=len(service.store.active()),storage=str(service.store.root),model=config.model,endpoint=config.endpoint)
    @app.get('/api/export')
    def export(group_id:str,experiment_id:str):return Response(service.export_csv(group_id,experiment_id),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="grades.csv"'})
    @app.get('/api/export/details')
    def export_details(group_id:str,experiment_id:str):
        service.store.group_scope(group_id);load_rubric(experiment_id)
        rows,_=service.store.reports(group_id,limit=100000)
        result=[service.detail(r['id']) for r in rows if r['experiment_id']==experiment_id]
        return Response(json.dumps(result,ensure_ascii=False,indent=2),media_type='application/json',headers={'Content-Disposition':'attachment; filename="grade-details.json"'})
    @app.post('/api/backups')
    def backup():return create_backup(service)
    @app.get('/api/backups/{bid}')
    def download_backup(bid:str):
        identifier(bid);path=service.store.path('backups/'+bid+'.zip');require(path.is_file(),'备份不存在')
        return FileResponse(path,filename='lab-grading-backup-'+bid+'.zip')
    if frontend and Path(frontend).is_dir():app.mount('/',StaticFiles(directory=str(frontend),html=True),name='frontend')
    return app
