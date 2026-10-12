"""Command-line application for the local grading backend (no frontend required)."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

from .engine import aggregate,load_rubric,validate_rubric,require
from .documents import SUPPORTED
from .transport import Configuration
from .workflow import Backend


def _config(args):
    return Configuration.load(getattr(args,'config',None),getattr(args,'credentials',None))


def _compact(job):
    result=job.get('result') or {}
    return {k:v for k,v in dict(job_id=job['id'],submission_id=job['submission_id'],state=job['state'],revision=job['revision'],
                                suggested_score=result.get('suggested_score'),score_interval=result.get('score_interval'),
                                blocking_flags=result.get('blocking_flags'),error=job.get('error')).items() if v is not None}


def parser():
    p=argparse.ArgumentParser(description='计算机系统实验报告批阅后端：导入、解析、DeepSeek评分、复核与导出')
    p.add_argument('--data-root',type=Path,default=Path('runtime'),help='数据库及证据保存目录')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('validate')
    check=sub.add_parser('doctor');check.add_argument('--config');check.add_argument('--credentials')
    score=sub.add_parser('score')
    for flag in ('experiment','context','judgments','output'):score.add_argument('--'+flag,required=True)
    imp=sub.add_parser('import');imp.add_argument('path',type=Path);imp.add_argument('--experiment',required=True);imp.add_argument('--student-id')
    select=sub.add_parser('select');select.add_argument('submission_id');select.add_argument('--actor',required=True);select.add_argument('--reason',required=True)
    job=sub.add_parser('prepare');job.add_argument('submission_id');job.add_argument('--config');job.add_argument('--credentials')
    retry=sub.add_parser('retry-extraction');retry.add_argument('job_id')
    recovery=sub.add_parser('recover');recovery.add_argument('job_id');recovery.add_argument('--reviewer',required=True);recovery.add_argument('--reason',required=True)
    run=sub.add_parser('run');run.add_argument('job_id')
    recheck=sub.add_parser('recheck');recheck.add_argument('job_id')
    batch=sub.add_parser('batch');batch.add_argument('--experiment');batch.add_argument('--config');batch.add_argument('--credentials')
    batch.add_argument('--limit',type=int,default=5);batch.add_argument('--send',action='store_true',help='实际调用模型；不加时只准备证据')
    status=sub.add_parser('status');status.add_argument('job_id',nargs='?');status.add_argument('--submissions',action='store_true')
    resolve=sub.add_parser('resolve');resolve.add_argument('job_id');resolve.add_argument('--reviewer',required=True);resolve.add_argument('--reason',required=True)
    resolve.add_argument('--verify-identity',action='store_true');resolve.add_argument('--clear-flag',action='append',default=[])
    resolve.add_argument('--output-id-match',choices=['true','false'])
    review=sub.add_parser('review');review.add_argument('job_id');review.add_argument('--decisions',type=Path)
    review.add_argument('--reviewer',required=True);review.add_argument('--reason',required=True);review.add_argument('--revision',required=True,type=int)
    pub=sub.add_parser('publish');pub.add_argument('job_id');pub.add_argument('--review-id',required=True);pub.add_argument('--revision',required=True,type=int)
    exp=sub.add_parser('export');exp.add_argument('output',type=Path)
    return p


def execute(args):
    """Dispatch explicit actions; import/prepare never imply a paid model call."""
    if args.command=='validate':
        return {'rubrics':16,'criteria':sum(validate_rubric(load_rubric(f'exp{i:02}')) for i in range(1,17)),'each_total':100,'status':'PASS'}
    if args.command=='doctor':
        config=_config(args)
        try:config.credential();credential=True
        except (OSError,ValueError):credential=False
        return {'dependencies':{m:bool(importlib.util.find_spec(m)) for m in ('pypdfium2','PIL')},
                'credential_configured':credential,'endpoint':config.endpoint,'model':config.model,'simulation':config.simulation,
                'word_requirement':'Windows桌面安装Microsoft Word可读取doc/docx；其他系统请传PDF'}
    if args.command=='score':
        result=aggregate(load_rubric(args.experiment),json.loads(Path(args.judgments).read_text('utf-8-sig')),json.loads(Path(args.context).read_text('utf-8-sig')))
        with Path(args.output).open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
        return {'output':str(Path(args.output).resolve())}
    backend=Backend(args.data_root)
    if args.command=='import':
        paths=sorted(p for p in args.path.rglob('*') if p.is_file() and p.suffix.lower() in SUPPORTED and not p.name.startswith('~$')) if args.path.is_dir() else [args.path]
        require(not args.student_id or len(paths)==1,'student-id override is only valid for one file')
        rows=[]
        for path in paths:
            try:
                s=backend.import_report(path,args.experiment,args.student_id)
                rows.append({k:s[k] for k in ('id','student_key','created','selected')})
            except (OSError,ValueError) as exc:rows.append({'file':path.name,'error':str(exc)})
        selected={s['id']:bool(s['selected']) for s in backend.store.list_submissions()}
        for row in rows:
            if 'id' in row:row['selected']=selected[row['id']]
        return {'imported':rows}
    if args.command=='select':backend.store.select(args.submission_id,args.actor,args.reason);return {'selected':args.submission_id}
    if args.command=='prepare':return _compact(backend.prepare(backend.create_job(args.submission_id,_config(args))['id']))
    if args.command=='retry-extraction':return _compact(backend.prepare(args.job_id))
    if args.command=='recover':return _compact(backend.recover(args.job_id,reviewer=args.reviewer,reason=args.reason))
    if args.command=='run':return _compact(backend.run(args.job_id))
    if args.command=='recheck':return _compact(backend.recheck(args.job_id))
    if args.command=='status':
        if args.submissions:return backend.store.list_submissions()
        return _compact(backend.store.job(args.job_id)) if args.job_id else backend.store.list_jobs()
    if args.command=='batch':
        require(args.limit>0,'limit must be positive')
        config=_config(args)
        if args.send:config.credential()
        rows=[]
        for s in backend.store.list_submissions():
            if args.experiment and s['experiment_id']!=args.experiment:continue
            if not s['selected']:continue
            jobs=[j for j in backend.store.list_jobs() if j['submission_id']==s['id']]
            if jobs:
                j=backend.store.job(jobs[-1]['id'])
                if j['state'] not in ('received','extraction_failed','ready','retryable_failed','model_failed'):continue
            else:j=backend.create_job(s['id'],config)
            try:
                if j['state'] in ('received','extraction_failed'):j=backend.prepare(j['id'])
                if args.send:j=backend.run(j['id'])
                rows.append(_compact(j))
            except Exception as exc:rows.append({'job_id':j['id'],'error':str(exc)[:300]})
            print(json.dumps({'progress':rows[-1]},ensure_ascii=False),flush=True,file=sys.stderr)
            if len(rows)>=args.limit:break
        return {'processed':rows,'sent_to_model':args.send}
    if args.command=='resolve':
        return _compact(backend.resolve_context(args.job_id,reviewer=args.reviewer,reason=args.reason,
                            identity_status='verified' if args.verify_identity else None,clear_flags=args.clear_flag,
                            output_id_match=None if args.output_id_match is None else args.output_id_match=='true'))
    if args.command=='review':
        decisions=json.loads(args.decisions.read_text('utf-8-sig')) if args.decisions else []
        return backend.review(args.job_id,decisions,reviewer=args.reviewer,reason=args.reason,expected_revision=args.revision)
    if args.command=='publish':return backend.publish(args.job_id,review_id=args.review_id,expected_revision=args.revision)
    if args.command=='export':return backend.export(args.output)
    raise ValueError('unknown command')


def main():
    args=parser().parse_args()
    try:result=execute(args)
    except Exception as exc:
        print(json.dumps({'status':'error','type':type(exc).__name__,'message':str(exc)[:400]},ensure_ascii=False),file=sys.stderr)
        raise SystemExit(2)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
