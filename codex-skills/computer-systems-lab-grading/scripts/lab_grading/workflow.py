"""Local backend workflow from immutable document ingestion to reviewable results."""
import csv
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import uuid

from .documents import SUPPORTED, dump_json, extract_document, sha256_file, validate_document
from .engine import aggregate, binding, fingerprint, load_rubric, require, validate_context
from .provider import SYSTEM, ROLE_CONFLICT, FACT_FORMAT_CONFLICT, build_request, parse_response, system_prompt, validate_checks
from .evidence_plan import prepare_word_evidence, VERSION as WORD_PIPELINE_VERSION
from .storage import Store, now
from .transport import Configuration, DeepSeekClient, TransportError


def _csv_safe(value):
    """Spreadsheet opening must not execute formula-like filenames or feedback."""
    text='' if value is None else str(value)
    return "'"+text if text.lstrip().startswith(('=','+','-','@','\t','\r')) else text


def _process_alive(pid):
    """Check ownership conservatively without Windows os.kill's termination risk."""
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
        kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        handle=kernel.OpenProcess(0x1000,False,pid)
        if not handle:return ctypes.get_last_error()!=87
        kernel.CloseHandle(handle)
        return True
    try:os.kill(pid,0)
    except ProcessLookupError:return False
    except PermissionError:return True
    return True


class Backend:
    def __init__(self,data_root):
        self.store=Store(data_root)

    def import_report(self,path,experiment_id,student_id=None,*,experiment_override_reason=''):
        """Copy original bytes under a content identity; never alter submitted files."""
        load_rubric(experiment_id)
        path=Path(path).resolve()
        validate_document(path)
        require(path.is_file() and path.suffix.lower() in SUPPORTED,'unsupported or missing report')
        require(0<path.stat().st_size<=64*1024*1024,'report empty or exceeds 64 MiB')
        hint=re.search(r'实验\s*0?(\d+)',path.stem)
        require(not hint or int(hint.group(1))==int(experiment_id[-2:]) or experiment_override_reason.strip(),'filename experiment mismatch')
        report_hash=sha256_file(path)
        matches=re.findall(r'(?<!\d)\d{9,13}(?!\d)',path.stem)
        if student_id is not None: require(bool(re.fullmatch(r'[A-Za-z0-9._-]{1,64}',student_id)),'student ID must contain 1-64 letters, digits, dots, underscores or hyphens')
        key=student_id or (matches[0] if len(matches)==1 else 'unknown-'+report_hash[:16])
        sid=hashlib.sha256(f'{experiment_id}:{key}:{report_hash}'.encode()).hexdigest()[:24]
        stored=self.store.path(f'originals/{sid}{path.suffix.lower()}')
        stored.parent.mkdir(parents=True,exist_ok=True)
        if not stored.exists():
            # Exclusive destination prevents races from replacing a stored version.
            try:
                with stored.open('xb') as target,path.open('rb') as source: shutil.copyfileobj(source,target)
            except FileExistsError: pass
        require(sha256_file(stored)==report_hash and sha256_file(path)==report_hash,'report changed while importing')
        item=dict(id=sid,experiment_id=experiment_id,student_key=key,report_sha256=report_hash,
                  original_name=path.name,original_path=str(path),stored_file=str(stored.relative_to(self.store.root)),created_at=now())
        result,created=self.store.add_submission(item)
        return {**result,'created':created,'selected':self.store.selected(result)}

    def create_job(self,sid,configuration=None):
        submission=self.store.submission(sid)
        config=configuration or Configuration()
        rubric=load_rubric(submission['experiment_id'])
        if submission['experiment_id'] in config.scoring_policies:
            from .calibration import apply_policy
            rubric=apply_policy(rubric,config.scoring_policies[submission['experiment_id']])
        return self.store.create_job(sid,rubric,config.snapshot())

    def prepare(self,jid):
        """A failed conversion stays failed; it never fabricates a blank report."""
        job=self.store.job(jid)
        require(job['state'] in ('received','extraction_failed'),'job is not awaiting extraction')
        submission=self.store.submission(job['submission_id'])
        require(self.store.selected(submission),'multiple/superseded versions: explicitly select a submission first')
        source=self.store.path(submission['stored_file'])
        require(sha256_file(source)==submission['report_sha256'],'stored original hash changed')
        token=f'{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex}'
        self.store.transition(jid,[job['state']],'extracting',worker_token=token)
        folder=self.store.path(f'jobs/{jid}/extractions/{uuid.uuid4().hex}')
        try:
            tokens=[submission['student_key']]
            parts=Path(submission['original_name']).stem.split('+')
            if len(parts)>=3 and 1<len(parts[1])<30: tokens.append(parts[1])
            manifest=extract_document(source,folder,identity_tokens=tokens)
            cover_ids=manifest['cover_id_candidates']
            status=('verified' if cover_ids==[submission['student_key']] else 'conflict' if cover_ids else 'unknown')
            flags=[]
            raw=(folder/'local-text.txt').read_text('utf-8')
            normal=re.sub(r'\s+','',raw)
            target=re.sub(r'\s+','',job['rubric']['title'])
            if target not in normal:
                flags.append('experiment_title_needs_review')
            if manifest['rotation_review_required']: flags.append('rotated_page_privacy_review')
            evidence=manifest['evidence']
            plan=None
            if source.suffix.lower()!='.pdf':
                evidence,plan,structure_flags=prepare_word_evidence(folder,manifest,job['rubric'],tokens)
                flags.extend(structure_flags)
            if submission['experiment_id']=='exp15':
                # Cover identity does not prove ID appears in the exploit output.
                evidence.append(dict(id='identity-output',kind='identity',origin='student',locator='实验15演示输出身份待人工比对',
                                     sha256=fingerprint({'match':None}),readable=True,match=None))
            context=dict(experiment_id=submission['experiment_id'],report_sha256=submission['report_sha256'],
                         rubric_sha256=fingerprint(job['rubric']),evidence_sha256=fingerprint(evidence),request_id=uuid.uuid4().hex,
                         model_requested=job['configuration']['model'],extraction_complete=manifest['extraction_complete'],
                         identity_status=status,blocking_flags=flags,evidence=evidence,
                         extraction_dir=str(folder.relative_to(self.store.root)),extractor_version=manifest['extractor_version'],
                         prompt_sha256=hashlib.sha256(SYSTEM.encode()).hexdigest())
            if plan:
                context.update(evidence_plan=plan,evidence_plan_sha256=fingerprint(plan),extractor_version=plan['pipeline_version'])
            if job['rubric'].get('calibration_policy'):context['calibration_enabled']=True
            context['prompt_sha256']=hashlib.sha256(system_prompt(context).encode()).hexdigest()
            context['check_prompt_sha256']=hashlib.sha256(system_prompt(context,'evidence_check').encode()).hexdigest()
            if context.get('calibration_enabled'):context['review_prompt_sha256']=hashlib.sha256(system_prompt(context,'auto_review').encode()).hexdigest()
            validate_context(context,job['rubric'])
            dump_json(self.store.path(f'jobs/{jid}/context.json'),context)
            return self.store.transition(jid,['extracting'],'ready',context=context,worker_token=token)
        except Exception as exc:
            self.store.transition(jid,['extracting'],'extraction_failed',error=type(exc).__name__+': '+str(exc)[:300],worker_token=token)
            raise

    def recover(self,jid,*,reviewer,reason):
        """Only release an abandoned local worker; never interrupt a live request."""
        require(reviewer.strip() and reason.strip(),'recovery requires actor and reason')
        job=self.store.job(jid)
        require(job['state'] in ('extracting','judging'),'job is not interrupted work')
        token=job['worker_token']
        require(token and len(token.split(':'))==3,'worker identity unavailable; create a new job')
        host,pid,_=token.split(':')
        require(host==socket.gethostname() and pid.isdigit(),'cannot verify worker on another host')
        require(not _process_alive(int(pid)),'worker is still alive; recovery refused')
        target='extraction_failed' if job['state']=='extracting' else 'retryable_failed'
        result=self.store.transition(jid,[job['state']],target,error='interrupted worker recovered',worker_token=token)
        with self.store.connect() as db:
            self.store.event(db,'worker_recovered',{'job_id':jid,'reviewer':reviewer,'reason':reason,'previous_worker':token})
        return result

    def run(self,jid):
        """Claim one prepared job, bind all images, call the configured real endpoint.

        Evidence/format failures are retained for repair; never take the highest
        of several model scores or replace a failed request with zero.
        """
        job=self.store.job(jid)
        require(job['state'] in ('ready','retryable_failed','model_failed'),'job cannot be run from current state')
        submission=self.store.submission(job['submission_id'])
        require(self.store.selected(submission),'selected submission changed; no network request sent')
        require(sha256_file(self.store.path(submission['stored_file']))==submission['report_sha256'],'stored original hash changed')
        config=Configuration(**job['configuration'])
        config.credential()  # Fail before claiming when credentials are absent.
        context=job['context']
        require(context is not None,'prepare report first')
        if Path(submission['stored_file']).suffix.lower()!='.pdf':
            require(context.get('evidence_plan',{}).get('pipeline_version')==WORD_PIPELINE_VERSION,'Word pipeline changed; prepare a new job before sending')
        token=f'{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex}'
        self.store.transition(jid,[job['state']],'judging',worker_token=token)
        try:
            folder=self.store.path(context['extraction_dir'])
            image_entries=[e for e in context['evidence'] if e['kind']=='image' and e['readable']]
            require(len(image_entries)<=config.max_images,'split/review required: image count exceeds configured limit')
            image_paths={e['id']:self.store.path(str(folder.relative_to(self.store.root)/e['file'])) for e in image_entries}
            sizes=[p.stat().st_size for p in image_paths.values()]
            # Enforce the existing bounds before allocating all bytes/base64.
            require(all(size<=8*1024*1024 for size in sizes) and sum(sizes)<=24*1024*1024,
                    'image packet too large; split/review required before reading images')
            images={eid:path.read_bytes() for eid,path in image_paths.items()}
            require(context['prompt_sha256']==hashlib.sha256(system_prompt(context).encode()).hexdigest(), 'prompt version changed; prepare a new job for auditable rerun')
            checks=None
            if context.get('evidence_plan'):
                require(context.get('check_prompt_sha256')==hashlib.sha256(system_prompt(context,'evidence_check').encode()).hexdigest(),'evidence-check version changed; prepare new job')
                # Reuse only the latest valid fact record bound to this job;
                # recovering a failed grade must not pay to re-observe unchanged input.
                with self.store.connect() as db:
                    attempts=[json.loads(r[0]) for r in db.execute('SELECT metadata FROM attempts WHERE job_id=? ORDER BY created_at DESC',(jid,))]
                latest=next((a for a in attempts if a.get('stage')=='evidence_check'),None)
                if latest and latest.get('visible_response'):
                    try:checks=validate_checks(parse_response(latest['visible_response']),context,job['rubric'],quarantine_roles=True,quarantine_invalid=True)
                    except (ValueError,TypeError,KeyError):checks=None
                if checks is None:
                    request=build_request(job['rubric'],context,images,model=config.model,max_tokens=config.max_tokens,max_images=config.max_images,stage='evidence_check')
                    request['thinking']={'type':config.thinking}
                    fact_response=DeepSeekClient(config).complete(request,lambda metadata:self.store.attempt(jid,{**metadata,'stage':'evidence_check'}))
                    del request  # Release the first image packet before allocating the grading packet.
                    checks=validate_checks(parse_response(fact_response),context,job['rubric'],quarantine_roles=True,quarantine_invalid=True)
                dump_json(self.store.path(f'jobs/{jid}/checked-facts-{uuid.uuid4().hex}.json'),checks)
            request=build_request(job['rubric'],context,images,model=config.model,max_tokens=config.max_tokens,max_images=config.max_images,checks=checks)
            request['thinking']={'type':config.thinking}
            response=DeepSeekClient(config).complete(request,lambda metadata:self.store.attempt(jid,{**metadata,'stage':'grade'}))
            scored=self._save_response(job,response,checks=checks)
            if checks and scored['unresolved_items'] and job['rubric'].get('calibration_policy',{}).get('auto_review'):
                scored=self._automatic_review(job,scored,checks,images,config)
            return self.store.transition(jid,['judging'],scored['status'],result=scored,worker_token=token)
        except TransportError as exc:
            self.store.transition(jid,['judging'],'retryable_failed' if exc.retryable else 'model_failed',error=exc.code,worker_token=token)
            raise
        except Exception as exc:
            self.store.transition(jid,['judging'],'model_failed',error=type(exc).__name__+': '+str(exc)[:300],worker_token=token)
            raise

    def _automatic_review(self,job,initial,checks,images,config):
        """One paid repair pass; failures preserve a usable first suggestion."""
        from .auto_review import review_request,validate_review
        ctx=job['context'];targets=initial['unresolved_items'];summary={'targets':targets,'max_passes':1}
        try:
            require(ctx.get('review_prompt_sha256')==hashlib.sha256(system_prompt(ctx,'auto_review').encode()).hexdigest(),'自动复查规则已更新，请新建批阅版本')
            with self.store.connect() as db:
                attempts=[json.loads(r[0]) for r in db.execute('SELECT metadata FROM attempts WHERE job_id=? ORDER BY created_at DESC',(job['id'],))]
            previous=next((a for a in attempts if a.get('stage')=='auto_review'),None)
            if previous:
                require(previous.get('visible_response'),'本任务已有一次复查调用，失败后不自动重复付费')
                response=previous['visible_response']
            else:
                response=DeepSeekClient(config).complete(review_request(job['rubric'],ctx,images,initial,checks,config),
                    lambda m:self.store.attempt(job['id'],{**m,'stage':'auto_review'}))
            patched,new_facts,audits=validate_review(response,job['rubric'],ctx,targets)
            fields=('criterion_id','verdict','evidence_ids','observation','reason','missing')
            merged={r['criterion_id']:{k:r[k] for k in fields} for r in initial['rows']}
            merged.update({r['criterion_id']:r for r in patched})
            facts={c['criterion_id']:c for c in checks['checks']};facts.update({c['criterion_id']:c for c in new_facts})
            combined=copy.deepcopy(response)
            combined['choices'][0]['message']['content']=json.dumps({'binding':binding(ctx),'judgments':list(merged.values())},ensure_ascii=False)
            scored=self._save_response(job,combined,checks={'binding':binding(ctx),'checks':list(facts.values())},absence_audits=audits,
                composition={'first_response_id':initial.get('response_id'),'review_response_id':response.get('id'),'changed_criteria':targets})
            summary.update(status='completed',resolved=[cid for cid in targets if cid not in scored['unresolved_items']])
        except (ValueError,TypeError,KeyError,TransportError) as exc:
            scored=initial;summary.update(status='failed',error=str(exc)[:500],resolved=[])
        scored['automatic_review']=summary
        dump_json(self.store.path(f"jobs/{job['id']}/automatic-review-{uuid.uuid4().hex}.json"),summary)
        return scored

    def _save_response(self,job,response,checks=None,absence_audits=None,composition=None):
        """Unsafe absence claims become unresolved, never fabricated evidence or zero."""
        raw=parse_response(response)
        result=copy.deepcopy(raw)
        context=job['context']
        catalog={e['id'] for e in context['evidence']}
        guarded=[]
        guarded_context=[]
        guarded_facts=[]
        guarded_invalid_tiers=[]
        guarded_unreadable_claims=[]
        guarded_invalid_facts=[]
        modality_adjustments=[]
        criteria={c['id']:c for s in job['rubric']['sections'] for c in s['criteria']}
        evidence={e['id']:e for e in context['evidence']}
        if checks is not None:checks=validate_checks(checks,context,job['rubric'],quarantine_roles=True,quarantine_invalid=True)
        facts={c['criterion_id']:c for c in checks['checks']} if checks else {}
        requirements={p['criterion_id']:p.get('verification_requirements',{}) for p in context.get('evidence_plan',{}).get('criteria',[])}
        for item in result.get('judgments',[]):
            cid=item.get('criterion_id')
            if any(x.startswith(FACT_FORMAT_CONFLICT) for x in facts.get(cid,{}).get('contradictions',[])):
                guarded_invalid_facts.append(cid)
                item.update(verdict='unresolved',missing=False,reason='事实记录格式或引用异常，本项尚未核实，不能用普通推定代替核对。原理由：'+str(item.get('reason','')))
            if cid in criteria and item.get('verdict')=='minor' and criteria[cid].get('minor_points') is None:
                guarded_invalid_tiers.append(cid)
                item.update(verdict='unresolved',missing=False,reason='模型使用了本项未设置的minor档位，未自动换成满分、部分分或零分；本项待核对。原理由：'+str(item.get('reason','')))
            refs=item.get('evidence_ids')
            if item.get('verdict') in ('full','minor','partial','zero') and item.get('missing') is False and isinstance(refs,list) and all(isinstance(r,str) and r in evidence for r in refs) and any(not evidence[r]['readable'] for r in refs):
                guarded_unreadable_claims.append(cid)
                item.update(verdict='unresolved',missing=False,reason='所引用原图不可直接核验（可能含裁剪或旋转），本项保留原引用待页面核对，不据此给分或扣零。原理由：'+str(item.get('reason','')))
            if any(x.startswith(ROLE_CONFLICT) for x in facts.get(cid,{}).get('contradictions',[])) and item.get('verdict')!='unresolved':
                guarded_facts.append(cid)
                item.update(verdict='unresolved',missing=False,reason='本项命令引用的材料归属未确认，保留本项待复核；其他项目继续批阅。原理由：'+str(item.get('reason','')))
            refs=item.get('evidence_ids')
            if item.get('missing') is True and item.get('verdict')=='zero' and isinstance(refs,list) and all(isinstance(r,str) for r in refs) and len(refs)==len(set(refs)) and set(refs)<=catalog:
                from .auto_review import absence_verified
                covered=absence_verified(context,item.get('criterion_id'),(absence_audits or {}).get(item.get('criterion_id')))
                if ((set(refs)!=catalog or context.get('calibration_enabled')) and not covered) or not context['extraction_complete'] or not all(e['readable'] for e in context['evidence']):
                    guarded.append(item.get('criterion_id'))
                    item.update(verdict='unresolved',missing=False,reason='后台拦截未经完整证据检索支持的缺答扣分，须人工复核。模型原理由：'+str(item.get('reason','')))
            if context.get('evidence_plan') and item.get('verdict') in ('full','minor','partial','zero') and item.get('missing') is False and isinstance(refs,list) and all(isinstance(r,str) for r in refs) and set(refs)<=catalog:
                if not any(evidence[r].get('role')=='student_answer' or evidence[r]['kind']=='identity' for r in refs):
                    guarded_context.append(item.get('criterion_id'))
                    item.update(verdict='unresolved',reason='后台拦截仅以题面/示例/页面上下文计分，缺少学生作答证据。原理由：'+str(item.get('reason','')))
            if facts and item.get('verdict') in ('full','minor','partial'):
                cid=item.get('criterion_id');rule=requirements.get(cid,{});fact=facts.get(cid,{})
                commands=[c['command'] for c in fact.get('observed_commands',[])]
                policy=criteria.get(cid,{}).get('evidence_mode')
                conflict=(rule.get('student_explanation_required') and policy!='either' and not fact.get('student_explanation','').strip())
                if rule.get('command_pattern'):conflict=conflict or not any(re.search(rule['command_pattern'],c) for c in commands)
                if item['verdict'] in ('full','minor') and rule.get('full_command_patterns'):
                    conflict=conflict or not all(any(re.search(pattern,c) for c in commands) for pattern in rule['full_command_patterns'])
                if conflict:
                    guarded_facts.append(cid)
                    item.update(verdict='unresolved',missing=False,reason='后台拦截给分与独立证据核对记录冲突：所需命令或学生解释未被观察到。原理由：'+str(item.get('reason','')))
            rule=criteria.get(item.get('criterion_id'),{})
            if rule.get('evidence_mode')=='both' and item.get('verdict') in ('full','minor') and isinstance(refs,list) and all(isinstance(r,str) and r in evidence for r in refs):
                source=[evidence[r] for r in refs if evidence[r].get('role')=='student_answer']
                if not (any(e['kind']=='image' for e in source) and any(e['kind'] in ('text','code','terminal') for e in source)):
                    modality_adjustments.append(item['criterion_id'])
                    item.update(verdict='partial',missing=False,reason='本项要求图文共同支持；目前仅一种证据，按部分档计分。原理由：'+str(item.get('reason','')))
        scored=aggregate(job['rubric'],result,context,absence_audits=absence_audits)
        scored['source_judgments']=raw.get('judgments',[])
        scored.update(absence_audits=absence_audits or {},modality_adjustments=modality_adjustments,composition=composition)
        scored.update(simulation=job['configuration']['simulation'],model_returned=response.get('model'),response_id=response.get('id'),usage=response.get('usage'),
                      guarded_absence_claims=guarded,guarded_context_claims=guarded_context,source_authenticity='not_verified: screenshots are submitted evidence, not proof of original execution')
        scored.update(guarded_fact_claims=guarded_facts,fact_check_sha256=fingerprint(checks) if checks else None)
        scored.update(guarded_invalid_tiers=guarded_invalid_tiers,guarded_unreadable_claims=guarded_unreadable_claims,guarded_invalid_facts=guarded_invalid_facts)
        out_dir=self.store.path(f"jobs/{job['id']}/results/{uuid.uuid4().hex}")
        out_dir.mkdir(parents=True)
        dump_json(out_dir/'model-judgments.json',raw)
        dump_json(out_dir/'judgments.json',result)
        dump_json(out_dir/'suggestion.json',scored)
        return scored

    def recheck(self,jid):
        """Revalidate the last stored visible response without another paid request."""
        job=self.store.job(jid)
        require(job['state'] in ('model_failed','needs_review'),'only failed model responses or pending automatic reviews can be rechecked')
        submission=self.store.submission(job['submission_id'])
        require(self.store.selected(submission),'selected submission changed')
        require(sha256_file(self.store.path(submission['stored_file']))==submission['report_sha256'],'stored original changed')
        if job['state']=='needs_review':
            with self.store.connect() as db:
                attempts=[json.loads(r[0]) for r in db.execute('SELECT metadata FROM attempts WHERE job_id=? ORDER BY created_at DESC',(jid,))]
            stages={stage:next((a for a in attempts if a.get('stage')==stage),{}) for stage in ('grade','evidence_check','auto_review')}
            require(all(a.get('visible_response') for a in stages.values()),'没有可重新校验的完整自动复查响应；不会新增模型调用')
            checks=validate_checks(parse_response(stages['evidence_check']['visible_response']),job['context'],job['rubric'],quarantine_roles=True,quarantine_invalid=True)
            initial=self._save_response(job,stages['grade']['visible_response'],checks=checks)
            scored=self._automatic_review(job,initial,checks,{},Configuration(**job['configuration'])) if initial['unresolved_items'] else initial
            return self.store.transition(jid,['needs_review'],scored['status'],result=scored)
        with self.store.connect() as db:
            row=db.execute('SELECT metadata FROM attempts WHERE job_id=? ORDER BY created_at DESC LIMIT 1',(jid,)).fetchone()
        require(row is not None,'no recorded model response')
        response=json.loads(row['metadata']).get('visible_response')
        if job['context'].get('evidence_plan'):
            require(json.loads(row['metadata']).get('stage')=='grade','structured recheck requires completed grading response')
        checks=None
        if job['context'].get('evidence_plan'):
            with self.store.connect() as db:
                attempts=[json.loads(r[0]) for r in db.execute('SELECT metadata FROM attempts WHERE job_id=? ORDER BY created_at DESC',(jid,))]
            latest=next((a for a in attempts if a.get('stage')=='evidence_check'),None)
            require(latest and latest.get('visible_response'),'no recorded evidence checks')
            checks=parse_response(latest['visible_response'])
        require(response is not None,'last attempt has no visible response')
        scored=self._save_response(job,response,checks=checks)
        return self.store.transition(jid,['model_failed'],scored['status'],result=scored)

    def resolve_context(self,jid,*,reviewer,reason,identity_status=None,clear_flags=(),output_id_match=None):
        """Record an explicit local resolution; never silently erase review blockers."""
        require(reviewer.strip() and reason.strip(),'resolution requires reviewer and reason')
        job=self.store.job(jid)
        require(job['state'] in ('ready','needs_review','ready_for_teacher_review','model_failed','retryable_failed'),'cannot resolve context in current state')
        context=job['context']
        require(context is not None,'prepare first')
        if identity_status is not None:
            require(identity_status=='verified','only explicit verified identity resolution supported')
            context['identity_status']=identity_status
        require(set(clear_flags)<=set(context['blocking_flags']),'unknown flag requested for removal')
        context['blocking_flags']=[f for f in context['blocking_flags'] if f not in clear_flags]
        if output_id_match is not None:
            require(type(output_id_match) is bool,'identity match must be boolean')
            entries=[e for e in context['evidence'] if e['kind']=='identity']
            require(len(entries)==1,'no output identity checkpoint in this experiment')
            entries[0].update(match=output_id_match,sha256=fingerprint({'match':output_id_match}))
            context['evidence_sha256']=fingerprint(context['evidence'])
        validate_context(context,job['rubric'])
        # Binding change requires new judgment/review; old suggestions remain auditable.
        target='ready' if output_id_match is not None else job['state']
        updated=self.store.transition(jid,[job['state']],target,context=context)
        with self.store.connect() as db:
            self.store.event(db,'context_resolved',{'job_id':jid,'reviewer':reviewer,'reason':reason,'identity_status':identity_status,'cleared_flags':list(clear_flags),'output_id_match':output_id_match})
        return updated

    def recommendation(self,job,*,policy=None):
        from .recommendation import proposal
        source=job['result'].get('source_judgments')
        if source is None:
            # Old jobs retain raw model judgments on disk. Read only same-bound files.
            candidates=sorted(self.store.path(f"jobs/{job['id']}/results").glob('*/model-judgments.json'),key=lambda p:p.stat().st_mtime,reverse=True)
            for path in candidates:
                value=json.loads(path.read_text('utf-8'))
                if value.get('binding')==binding(job['context']):source=value.get('judgments',[]);break
        return proposal(job['rubric'],job['context'],job['result'],source,policy)

    def review(self,jid,decisions,*,reviewer,reason,expected_revision,accept_estimates=False):
        """Teacher confirms or overrides named items against the same frozen rubric.

        Full/partial/zero verdicts and evidence are validated by the scoring
        engine again; a free-form total cannot bypass unresolved items.
        """
        require(reviewer.strip() and reason.strip(),'reviewer and review reason required')
        job=self.store.job(jid)
        require(job['state'] in ('needs_review','ready_for_teacher_review','reviewed'),'job has no reviewable result')
        require(type(expected_revision) is int and job['revision']==expected_revision,'stale review revision')
        require(isinstance(decisions,list),'review decisions must be a list')
        require(job['result'] is not None,'no suggested judgments to review')
        baseline=job['result']
        if job['state']=='reviewed':
            with self.store.connect() as db:
                previous=db.execute('SELECT result FROM reviews WHERE job_id=? ORDER BY revision DESC LIMIT 1',(jid,)).fetchone()
                require(previous is not None,'review history missing')
                baseline=json.loads(previous['result'])
        original={r['criterion_id']:{k:r[k] for k in ('criterion_id','verdict','evidence_ids','observation','reason','missing')} for r in baseline['rows']}
        changed=set()
        for item in decisions:
            require(item['criterion_id'] in original and item['criterion_id'] not in changed,'duplicate or unknown review criterion')
            require(item['reason'].strip(),'every change needs a reason')
            original[item['criterion_id']]=item;changed.add(item['criterion_id'])
        aggregate_input={'binding':binding(job['context']),'judgments':list(original.values())}
        accepted={}
        if accept_estimates:
            proposed=self.recommendation(job)
            for row in proposed['rows']:
                cid=row['criterion_id']
                if row['estimated'] and all(original[cid][k]==row[k] for k in ('verdict','evidence_ids','missing')):
                    accepted[cid]={k:original[cid][k] for k in ('criterion_id','verdict','evidence_ids','observation','reason','missing')}
            # A previously accepted item remains explicitly recorded when re-reviewing.
            for cid in baseline.get('accepted_estimate_items',[]):
                previous=next(r for r in baseline['rows'] if r['criterion_id']==cid)
                if all(original[cid][k]==previous[k] for k in ('verdict','evidence_ids','missing')):
                    accepted[cid]=original[cid]
        result=aggregate(job['rubric'],aggregate_input,job['context'],absence_audits=baseline.get('absence_audits'),human_review=True,accepted_estimates=accepted)
        require(result['suggested_score'] is not None,'review still has unresolved items or context blockers')
        result.update(simulation=job['configuration']['simulation'],reviewer=reviewer,review_reason=reason,absence_audits=baseline.get('absence_audits',{}),estimate_acceptance='教师明确接受AI推定项目' if accepted else None)
        rid=uuid.uuid4().hex
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current=db.execute('SELECT revision,state FROM jobs WHERE id=?',(jid,)).fetchone()
            require(current['revision']==expected_revision and current['state']==job['state'],'review lost concurrent update')
            s=self.store.submission(job['submission_id'])
            selected=db.execute('SELECT submission_id FROM selections WHERE experiment_id=? AND student_key=?',(s['experiment_id'],s['student_key'])).fetchone()
            require(selected['submission_id']==s['id'],'review targets superseded submission')
            db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?)',(rid,jid,expected_revision+1,now(),reviewer,reason,json.dumps(result,ensure_ascii=False)))
            db.execute('UPDATE jobs SET state=?,revision=revision+1,updated_at=? WHERE id=?',('reviewed',now(),jid))
            self.store.event(db,'teacher_reviewed',{'job_id':jid,'review_id':rid,'changed_criteria':sorted(changed)})
        return {'review_id':rid,'job_id':jid,'score':result['suggested_score'],'revision':expected_revision+1}

    def publish(self,jid,*,review_id,expected_revision):
        """Publish only the selected, reviewed version; simulation is never official."""
        job=self.store.job(jid)
        require(not job['configuration']['simulation'],'simulation grades cannot be published')
        submission=self.store.submission(job['submission_id'])
        require(sha256_file(self.store.path(submission['stored_file']))==submission['report_sha256'],'stored original changed')
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current=db.execute('SELECT revision,state FROM jobs WHERE id=?',(jid,)).fetchone()
            require(current['state']=='reviewed' and current['revision']==expected_revision,'publish requires current reviewed revision')
            review=db.execute('SELECT * FROM reviews WHERE id=? AND job_id=? AND revision=?',(review_id,jid,expected_revision)).fetchone()
            require(review is not None,'review is not the current job revision')
            selection=db.execute('SELECT submission_id FROM selections WHERE experiment_id=? AND student_key=?',(submission['experiment_id'],submission['student_key'])).fetchone()
            require(selection['submission_id']==submission['id'],'selected submission changed')
            result=json.loads(review['result'])
            require(not result.get('simulation',True),'simulation review cannot be published')
            require(not result['blocking_flags'] and result['suggested_score'] is not None,'review still blocked')
            pid=uuid.uuid4().hex
            db.execute('INSERT INTO publications VALUES(?,?,?,?,?)',(pid,jid,review_id,now(),result['suggested_score']))
            db.execute('UPDATE jobs SET state=?,revision=revision+1,updated_at=? WHERE id=?',('published',now(),jid))
            self.store.event(db,'grade_published',{'job_id':jid,'publication_id':pid,'review_id':review_id})
        return {'publication_id':pid,'score':result['suggested_score']}

    def export(self,output_dir):
        """Export a consistent ledger snapshot; omit fake zero scores for failures."""
        output=Path(output_dir).resolve()
        require(not output.exists(),'export directory exists; choose a new path')
        output.mkdir(parents=True)
        with self.store.connect() as db:
            db.execute('BEGIN')
            records=[dict(r) for r in db.execute('''SELECT j.*,s.experiment_id,s.student_key,s.original_name,
                (v.submission_id=s.id) AS is_selected FROM jobs j JOIN submissions s ON s.id=j.submission_id
                LEFT JOIN selections v ON v.experiment_id=s.experiment_id AND v.student_key=s.student_key ORDER BY j.created_at''')]
            reviews={r['job_id']:dict(r) for r in db.execute('SELECT * FROM reviews ORDER BY created_at')}
            publications={r['job_id']:dict(r) for r in db.execute('SELECT * FROM publications ORDER BY created_at')}
        summary,details=[],[]
        for row in records:
            result=json.loads(row['result']) if row['result'] else None
            review=reviews.get(row['id'])
            publication=publications.get(row['id'])
            reviewed=json.loads(review['result']) if review else None
            summary.append(dict(job_id=row['id'],experiment=row['experiment_id'],student_id=row['student_key'],
                                submission_id=row['submission_id'],selected=bool(row['is_selected']),status=row['state'],
                                suggested_score=result.get('suggested_score') if result else None,
                                score_lower=result['score_interval'][0] if result else None,score_upper=result['score_interval'][1] if result else None,
                                reviewed_score=reviewed['suggested_score'] if reviewed else None,
                                published_score=publication['score'] if publication else None,error=row['error'] or '',
                                simulation=json.loads(row['configuration'])['simulation']))
            if result:
                for item in result['rows']:
                    details.append(dict(job_id=row['id'],criterion_id=item['criterion_id'],verdict=item['verdict'],
                                        points=item['awarded_points'],max_points=item['max_points'],evidence_ids=';'.join(item['evidence_ids']),
                                        observation=item['observation'],reason=item['reason']))
            if reviewed: dump_json(output/(row['id']+'-reviewed.json'),reviewed)
            if result: dump_json(output/(row['id']+'-suggestion.json'),result)
        for name,rows,columns in [('scores.csv',summary,['job_id','experiment','student_id','submission_id','selected','status','suggested_score','score_lower','score_upper','reviewed_score','published_score','error','simulation']),
                                   ('criteria.csv',details,['job_id','criterion_id','verdict','points','max_points','evidence_ids','observation','reason'])]:
            with (output/name).open('w',encoding='utf-8-sig',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
                for row in rows: writer.writerow({k:_csv_safe(row[k]) for k in columns})
        dump_json(output/'summary.json',summary)
        return {'directory':str(output),'jobs':len(summary),'criteria':len(details)}
