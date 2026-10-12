"""Single-owner teaching application; the existing engine is the grade authority."""
import csv
import io
import json
from pathlib import Path
import re
import threading
import uuid

from .documents import sha256_file, validate_document
from .engine import load_rubric, require
from .intake import identity_candidate, new_version_hint
from .provider import response_problem
from .storage import now
from .transport import Configuration
from .web_store import CatalogStore, clean, identifier
from .workflow import Backend, _csv_safe


STATES = {'received':'received','extracting':'running','ready':'ready','judging':'running',
          'needs_review':'needs_review','ready_for_teacher_review':'scored','reviewed':'reviewed',
          'published':'published','extraction_failed':'error','retryable_failed':'error','model_failed':'error'}
STATUS_LABELS = {'received':'已接收','ready':'证据就绪','running':'处理中','needs_review':'待复核','scored':'已有建议','reviewed':'已复核','published':'已发布','error':'处理失败','unmatched':'待匹配','superseded':'历史版本','duplicate':'待选版本'}


class TeachingService:
    def __init__(self, root, seed=None):
        self.store = CatalogStore(root)
        self.lock = threading.RLock()
        self._engines={}
        self._recommendations={}
        if seed and Path(seed).is_file() and not self.store.catalog()['groups']:
            value=json.loads(Path(seed).read_text('utf-8-sig'))
            self.store.import_roster(value['rows'],term=value.get('term',''),source=value.get('source','初始名单'))

    def backend(self, group_id):
        identifier(group_id)
        require(any(g['id']==group_id for g in self.store.catalog()['groups']), '分组不存在')
        with self.lock:
            if group_id not in self._engines:self._engines[group_id]=Backend(self.store.path('engines/'+group_id))
            return self._engines[group_id]

    def settings(self):
        with self.store.connect() as db:
            row=db.execute('SELECT * FROM settings WHERE id=1').fetchone()
        value=json.loads(row['value']) if row else Configuration(max_retries=0).snapshot()
        return dict(configuration=value,revision=row['revision'] if row else 0,target=85)

    def save_settings(self, value, revision, actor):
        config=Configuration(**value)
        require(not config.simulation,'正式服务不接受模拟模型配置')
        require(config.max_retries==0,'正式服务关闭自动网络重试；失败后由教师决定重试')
        with self.lock,self.store.connect(True) as db:
            row=db.execute('SELECT revision FROM settings WHERE id=1').fetchone()
            require((row[0] if row else 0)==revision,'配置已被修改，请刷新')
            db.execute('INSERT INTO settings VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET value=excluded.value,revision=excluded.revision',
                       (json.dumps(config.snapshot()),revision+1))
            self.store.event(db,'settings_saved',None,actor,'保存模型配置（不含密钥）')
        return self.settings()

    def calibration_preview(self,group_id,experiment_id,policy=None,recommend_weights=False):
        from .calibration import default_policy,preview,recommend
        self.store.group_scope(group_id)
        settings=self.settings()
        saved=settings['configuration'].get('scoring_policies',{}).get(experiment_id)
        rows,_=self.store.reports(group_id,limit=100000)
        reports=[self.describe(r) for r in rows if r['experiment_id']==experiment_id]
        result=(recommend if recommend_weights else preview)(reports,load_rubric(experiment_id),policy if policy is not None else saved or default_policy())
        return {**result,'revision':settings['revision'],'saved_policy':saved,'scope':'同一实验的所有分组统一使用，历史任务保持冻结规则'}

    def save_calibration(self,experiment_id,policy,revision,actor,reason):
        from .calibration import validate_policy
        require(clean(actor) and clean(reason),'保存校准需要操作者和理由')
        p=validate_policy(policy,experiment_id)
        with self.lock:
            config=self.settings()['configuration']
            config['scoring_policies']={**config.get('scoring_policies',{}),experiment_id:p}
            result=self.save_settings(config,revision,actor)
            with self.store.connect(True) as db:
                self.store.event(db,'calibration_saved',None,actor,reason,{'experiment_id':experiment_id,'policy':p})
        return result

    def match(self, filename, group_id):
        c=self.store.catalog()
        require(any(g['id']==group_id for g in c['groups']),'分组不存在')
        ids={m['studentId'] for m in c['memberships'] if m['groupId']==group_id}
        students=[s for s in c['students'] if s['id'] in ids]
        stem=clean(Path(filename).stem)
        matches=[s for s in students if re.search(r'(?<![A-Za-z0-9])'+re.escape(s['number'])+r'(?![A-Za-z0-9])',stem)]
        if len(matches)==1:
            student=matches[0]
            other_names=[s['name'] for s in students if s['name']!=student['name'] and s['name'] in stem]
            if other_names and student['name'] not in stem:
                return None,'文件名中的学号与姓名冲突，需人工确认'
            return student['id'],'按完整学号匹配'
        if matches:return None,'文件名包含多个学号，需人工确认'
        if re.search(r'\d{5,}',stem):return None,'文件名学号不在当前分组，需人工确认'
        names=[s for s in students if s['name'] in stem]
        if len(names)==1:return names[0]['id'],'按分组内唯一姓名匹配'
        return None,'姓名重复或未找到学生，需人工确认'

    def member(self, group_id, student_id):
        c=self.store.catalog()
        require(dict(groupId=group_id,studentId=student_id) in c['memberships'],'学生不属于当前分组')
        return next(s for s in c['students'] if s['id']==student_id)

    def submission_group(self,group_id,student_id,target_group_id=None):
        """Aggregate groups are views; matched work belongs to one source group."""
        c=self.store.catalog();self.member(group_id,student_id)
        group=next(g for g in c['groups'] if g['id']==group_id)
        candidates=[gid for gid in (group['sourceGroupIds'] or [group_id]) if dict(groupId=gid,studentId=student_id) in c['memberships']]
        if target_group_id:
            require(target_group_id in candidates,'指定班级不在汇总来源中或学生不属于该班')
            return target_group_id
        return candidates[0] if len(candidates)==1 else None

    def migrate_catalog(self,legacy):
        """Merge old browser identities into server IDs, retaining original browser data."""
        c=self.store.catalog();groups={};students={}
        for old in legacy['groups']:
            if old.get('demo'):continue
            target=next((g for g in c['groups'] if g['name']==clean(old['name']) and g['term']==clean(old.get('term'))),None)
            if not target:
                target=dict(id=uuid.uuid4().hex,name=clean(old['name']),term=clean(old.get('term')),assignments=old.get('assignments',[]));c['groups'].append(target)
            else:target['assignments']=list(dict.fromkeys(target['assignments']+old.get('assignments',[])))
            groups[old['id']]=target['id']
        for old in legacy['students']:
            if old.get('demo'):continue
            target=next((s for s in c['students'] if s['number']==clean(old['number'])),None)
            require(target is None or target['name']==clean(old['name']),'旧名单同一学号姓名不一致，请先核对')
            if not target:
                target=dict(id=uuid.uuid4().hex,number=clean(old['number']),name=clean(old['name']),gender=clean(old.get('gender')),notes=old.get('notes',''));c['students'].append(target)
            elif old.get('notes') and old['notes'] not in target['notes']:
                target['notes']=(target['notes']+'\n旧版备注：'+old['notes']).strip()
            students[old['id']]=target['id']
        for m in legacy['memberships']:
            if m['groupId'] in groups and m['studentId'] in students:
                relation=dict(groupId=groups[m['groupId']],studentId=students[m['studentId']])
                if relation not in c['memberships']:c['memberships'].append(relation)
        self.store.replace_catalog(c['groups'],c['students'],c['memberships'],c['revision'],'本地教师')
        return dict(groups=len(groups),students=len(students))

    def ingest(self, path, filename, group_id, experiment_id, student_id=None, reason='',actor='本地教师',*,defer_match=False,allow_experiment_override=False,version_hint=None):
        """The HTTP layer writes a bounded upload first. Never trust a client hash."""
        load_rubric(experiment_id)
        path=Path(path).resolve()
        require(path.is_relative_to(self.store.path('originals')),'上传路径越界')
        validate_document(path)
        require(0<path.stat().st_size<=64*1024*1024,'文件为空或超过64MB')
        hint=re.search(r'实验\s*0?(\d+)',Path(filename).stem)
        require(not hint or int(hint[1])==int(experiment_id[-2:]) or (allow_experiment_override and clean(reason)),'文件名实验编号与所选实验不一致')
        with self.lock:
            imported_group_id=group_id
            matched,match_reason=self.match(filename,group_id)
            require(not (defer_match and student_id),'暂缓匹配时不能同时指定学生')
            if defer_match:matched,match_reason=None,'教师选择暂不指定，待人工匹配'
            if student_id:
                self.member(group_id,student_id)
                require(student_id==matched or clean(reason),'人工匹配必须填写原因')
                matched=student_id
                if reason:match_reason='人工指定：'+reason
            if matched:
                owner=self.submission_group(group_id,matched)
                if owner:
                    if owner!=group_id:match_reason+='；从汇总分组归入原班级'
                    group_id=owner
                else:matched=None;match_reason='学生属于多个来源班级，请人工指定学生和班级'
            digest=sha256_file(path)
            student=self.member(group_id,matched) if matched else None
            marker=version_hint or new_version_hint(filename,student_name=student['name'] if student else identity_candidate(filename)['name'])
            with self.store.connect() as db:
                existing=db.execute('SELECT id FROM reports WHERE deleted_at IS NULL AND group_id=? AND experiment_id=? AND student_id IS ? AND sha256=?',
                                    (group_id,experiment_id,matched,digest)).fetchone()
                retired=db.execute('SELECT id,revision FROM reports WHERE deleted_at IS NOT NULL AND group_id=? AND experiment_id=? AND student_id IS ? AND sha256=? ORDER BY deleted_at DESC LIMIT 1',
                                    (group_id,experiment_id,matched,digest)).fetchone() if not existing else None
            if retired:
                self.restore(retired['id'],retired['revision'],actor,'教师重新导入已删除的同一原件')
                existing=retired
            if existing:
                r=self.store.report(existing[0])
                if marker.get('is_new') and not self.version_hint(r,student).get('is_new'):
                    if matched:self.require_scope_idle(group_id,matched,experiment_id)
                    with self.store.connect(True) as db:
                        db.execute('UPDATE reports SET version_hint=?,revision=revision+1 WHERE id=?',(json.dumps(marker,ensure_ascii=False),r['id']))
                        self.store.event(db,'version_marker_added',r['id'],actor,'相同内容以带“新”标记的文件名再次导入，原件去重保留',marker)
                    if matched:self.resolve_versions(r,actor)
                return dict(report=self.detail(r['id']),duplicate=True)
            if matched:self.require_scope_idle(group_id,matched,experiment_id)
            engine_sid=None
            if matched:
                student=self.member(group_id,matched)
                engine_sid=self.backend(group_id).import_report(path,experiment_id,student['number'],experiment_override_reason=reason if allow_experiment_override else '')['id']
            rid=uuid.uuid4().hex
            with self.store.connect(True) as db:
                if matched:
                    count=db.execute('SELECT COUNT(*) FROM reports WHERE deleted_at IS NULL AND group_id=? AND student_id=? AND experiment_id=?',
                                     (group_id,matched,experiment_id)).fetchone()[0]
                else:count=0
                db.execute('''INSERT INTO reports(id,group_id,student_id,experiment_id,filename,stored_file,sha256,size,active,engine_submission_id,match_reason,created_at,version_hint)
                              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                           (rid,group_id,matched,experiment_id,filename,str(path.relative_to(self.store.root)),digest,path.stat().st_size,int(not count),engine_sid,match_reason,now(),json.dumps(marker,ensure_ascii=False)))
                self.store.event(db,'report_imported',rid,actor,'保存报告原件；'+match_reason,{'sha256':digest,'import_group_id':imported_group_id,'experiment_confirmation':reason if allow_experiment_override else ''})
            if matched:self.resolve_versions(self.store.report(rid),actor)
            return dict(report=self.describe(self.store.report(rid)),duplicate=False)

    @staticmethod
    def version_hint(r,student=None):
        hint=json.loads(r.get('version_hint') or '{}')
        return hint or new_version_hint(r['filename'],student_name=student['name'] if student else identity_candidate(r['filename'])['name'])

    def resolve_versions(self,r,actor):
        """Apply the teacher's unique-new policy without editing grading history."""
        if not r['student_id']:return
        scope=(r['group_id'],r['student_id'],r['experiment_id'])
        backend=self.backend(r['group_id']);student=self.member(r['group_id'],r['student_id'])
        with self.store.connect() as db:
            versions=[dict(v) for v in db.execute('SELECT * FROM reports WHERE deleted_at IS NULL AND group_id=? AND student_id=? AND experiment_id=?',scope)]
            manual=db.execute('''SELECT e.resource_id FROM events e JOIN reports v ON v.id=e.resource_id
                WHERE e.kind='version_selected' AND v.deleted_at IS NULL AND v.group_id=? AND v.student_id=? AND v.experiment_id=? ORDER BY e.id DESC LIMIT 1''',scope).fetchone()
        picked=next((v for v in versions if manual and v['id']==manual[0]),None)
        reason='保留教师明确选择的最终报告'
        if picked is None:
            picked=next((v for v in versions if v['active'] and v['job_id'] and backend.store.job(v['job_id'])['state']=='published'),None)
            reason='保留已发布成绩的当前报告，新提交需教师明确切换'
        if picked is None:
            distinct={v['sha256'] for v in versions}
            marked=[v for v in versions if self.version_hint(v,student).get('is_new')]
            if len({v['sha256'] for v in marked})==1:picked=next((v for v in marked if v['active']),marked[0]);reason='按教师规则，唯一带明确“新”标记的报告作为最终报告'
            elif len(distinct)==1:picked=next((v for v in versions if v['active']),versions[0]);reason='当前仅一份不同内容的有效报告，自动采用'
            else:reason='多份报告无唯一“新”标记，请教师选择最终报告'
        selected_id=picked['id'] if picked else None
        changed=any(bool(v['active'])!=(v['id']==selected_id) for v in versions)
        if picked:
            engine_changed=not backend.store.selected(backend.store.submission(picked['engine_submission_id']))
            if engine_changed:backend.store.select(picked['engine_submission_id'],actor,reason)
        else:
            engine_changed=any(backend.store.selected(backend.store.submission(v['engine_submission_id'])) for v in [*versions,r] if v.get('engine_submission_id'))
            if engine_changed:backend.store.clear_selection(r['engine_submission_id'],actor,reason)
        if changed or engine_changed:
            with self.store.connect(True) as db:
                db.execute('''UPDATE reports SET active=(id IS ?),revision=revision+1
                    WHERE deleted_at IS NULL AND group_id=? AND student_id=? AND experiment_id=? AND active!=(id IS ?)''',
                    (selected_id,*scope,selected_id))
                self.store.event(db,'version_auto_selected' if picked else 'version_choice_required',selected_id or r['id'],actor,reason,{'selected_id':selected_id})

    def require_scope_idle(self, group_id,student_id,experiment_id):
        with self.store.connect() as db:
            active=db.execute("SELECT 1 FROM tasks t JOIN reports r ON r.id=t.report_id WHERE t.state IN ('queued','running') AND r.group_id=? AND r.student_id=? AND r.experiment_id=?",(group_id,student_id,experiment_id)).fetchone()
        require(not active,'该学生本实验正在处理，请等待任务结束')

    def check_report(self,rid,revision):
        r=self.store.report(rid)
        require(not r['deleted_at'],'报告已删除，请先恢复后操作')
        require(r['revision']==revision,'报告已更新，请刷新后操作')
        require(not self.store.active(rid),'报告正在处理，请稍后操作')
        return r

    def bind(self,rid,student_id,revision,actor,reason,target_group_id=None):
        require(clean(actor) and clean(reason),'人工匹配需要操作者和原因')
        with self.lock:
            r=self.check_report(rid,revision)
            require(not r['engine_submission_id'],'已有评分身份的报告不能改绑；请重新导入正确版本')
            original_group=r['group_id']
            group=next(g for g in self.store.catalog()['groups'] if g['id']==original_group)
            if target_group_id and not group['sourceGroupIds']:
                student=self.member(target_group_id,student_id)
                owner=self.submission_group(target_group_id,student_id)
                require(owner==target_group_id,'请指定学生所属的原班级')
            else:
                student=self.member(r['group_id'],student_id)
                owner=self.submission_group(r['group_id'],student_id,target_group_id)
            require(owner,'学生属于多个来源班级，请选择报告所属班级')
            r['group_id']=owner
            self.require_scope_idle(r['group_id'],student_id,r['experiment_id'])
            sid=self.backend(r['group_id']).import_report(self.store.path(r['stored_file']),r['experiment_id'],student['number'],experiment_override_reason=reason)['id']
            with self.store.connect(True) as db:
                others=db.execute('SELECT id FROM reports WHERE deleted_at IS NULL AND id!=? AND group_id=? AND student_id=? AND experiment_id=?',(rid,r['group_id'],student_id,r['experiment_id'])).fetchall()
                db.execute('UPDATE reports SET group_id=?,student_id=?,engine_submission_id=?,active=?,revision=revision+1,match_reason=? WHERE id=?',(owner,student_id,sid,int(not others),'人工指定：'+reason,rid))
                self.store.event(db,'identity_bound',rid,actor,reason,{'student_id':student_id,'original_group_id':original_group,'group_id':owner})
            self.resolve_versions(self.store.report(rid),actor)
            return self.detail(rid)

    def select(self,rid,revision,actor,reason):
        require(clean(actor) and clean(reason),'版本选择需要操作者和原因')
        with self.lock:
            r=self.check_report(rid,revision)
            require(r['student_id'],'请先匹配学生')
            self.require_scope_idle(r['group_id'],r['student_id'],r['experiment_id'])
            self.backend(r['group_id']).store.select(r['engine_submission_id'],actor,reason)
            with self.store.connect(True) as db:
                db.execute('UPDATE reports SET active=(id=?),revision=revision+1 WHERE deleted_at IS NULL AND group_id=? AND student_id=? AND experiment_id=?',(rid,r['group_id'],r['student_id'],r['experiment_id']))
                self.store.event(db,'version_selected',rid,actor,reason)
            return self.detail(rid)

    def delete(self,rid,revision,actor,reason):
        require(clean(actor) and clean(reason),'删除需要操作者和原因')
        with self.lock:
            r=self.check_report(rid,revision)
            require(self.describe(r)['canDelete'],'该报告不能删除；已发布成绩或正在处理的报告需先完成原流程')
            if r['student_id']:self.require_scope_idle(r['group_id'],r['student_id'],r['experiment_id'])
            with self.store.connect(True) as db:
                db.execute('UPDATE reports SET deleted_at=?,revision=revision+1 WHERE id=?',(now(),rid))
                self.store.event(db,'report_deleted',rid,actor,reason,{'preserved_original':True})
            self.resolve_versions(r,actor)
            return self.detail(rid)

    def restore(self,rid,revision,actor,reason):
        require(clean(actor) and clean(reason),'恢复需要操作者和原因')
        with self.lock:
            r=self.store.report(rid)
            require(r['revision']==revision,'报告已更新，请刷新后操作')
            require(r['deleted_at'],'报告未删除')
            require(not self.store.active(rid),'报告正在处理，请稍后操作')
            if r['student_id']:self.require_scope_idle(r['group_id'],r['student_id'],r['experiment_id'])
            path=self.store.path(r['stored_file'])
            require(path.is_file() and sha256_file(path)==r['sha256'],'原件缺失或已改变，无法恢复')
            with self.store.connect(True) as db:
                db.execute('UPDATE reports SET deleted_at=NULL,active=0,revision=revision+1 WHERE id=?',(rid,))
                self.store.event(db,'report_restored',rid,actor,reason)
            self.resolve_versions(self.store.report(rid),actor)
            return self.detail(rid)

    def describe(self,r,catalog=None,detail=False):
        c=catalog or self.store.catalog()
        student=next((s for s in c['students'] if s['id']==r['student_id']),None)
        group=next(g for g in c['groups'] if g['id']==r['group_id'])
        job=self.backend(r['group_id']).store.job(r['job_id']) if r['job_id'] else None
        ctx=(job or {}).get('context') or {}
        result=(job or {}).get('result')
        recommendation=None
        if job and result and result.get('rows') and result.get('binding'):
            from .engine import binding, fingerprint
            if result['binding']==binding(ctx):
                policy=self.settings()['configuration'].get('review_policy',{})
                key=(job['id'],job['revision'],result.get('result_sha256'),fingerprint(policy))
                if key not in self._recommendations:
                    self._recommendations[key]=self.backend(r['group_id']).recommendation(job,policy=policy)
                    if len(self._recommendations)>2000:self._recommendations={key:self._recommendations[key]}
                recommendation=self._recommendations[key]
        review=publication=None
        if job:
            with self.backend(r['group_id']).store.connect() as db:
                row=db.execute('SELECT * FROM reviews WHERE job_id=? ORDER BY revision DESC LIMIT 1',(job['id'],)).fetchone()
                if row:review={**dict(row),'result':json.loads(row['result'])}
                row=db.execute('SELECT * FROM publications WHERE job_id=? ORDER BY created_at DESC LIMIT 1',(job['id'],)).fetchone()
                if row:publication=dict(row)
        active=self.store.active(r['id'])
        with self.store.connect() as db:
            latest=db.execute('SELECT * FROM tasks WHERE report_id=? ORDER BY created_at DESC LIMIT 1',(r['id'],)).fetchone()
            latest=dict(latest) if latest else None
            manual=db.execute('''SELECT e.resource_id FROM events e JOIN reports v ON v.id=e.resource_id
                WHERE e.kind='version_selected' AND v.deleted_at IS NULL AND v.group_id=? AND v.student_id=? AND v.experiment_id=? ORDER BY e.id DESC LIMIT 1''',
                (r['group_id'],r['student_id'],r['experiment_id'])).fetchone() if student else None
        status=STATES.get(job['state'],'error') if job else 'received'
        if status in ('needs_review','scored') and recommendation:
            status='needs_review' if recommendation['priority_count'] or recommendation['blocking_flags'] else 'scored'
        if not student:status='unmatched'
        elif not r['active']:
            with self.store.connect() as db:
                selected=db.execute('SELECT 1 FROM reports WHERE deleted_at IS NULL AND group_id=? AND student_id=? AND experiment_id=? AND active=1',(r['group_id'],r['student_id'],r['experiment_id'])).fetchone()
            status='superseded' if selected else 'duplicate'
        elif active:status='running'
        elif latest and latest['state'] in ('failed','interrupted') and status not in ('scored','needs_review','reviewed','published'):status='error'
        if r['deleted_at']:status='deleted'
        def rows(value):
            return [{**x,'id':x['criterion_id'],'evidence':', '.join(x['evidence_ids'])} for x in (value or {}).get('rows',[])]
        dto=dict(id=r['id'],groupId=r['group_id'],studentId=r['student_id'],name=student['name'] if student else '未匹配',student=student['number'] if student else '',className=group['name'],exp=r['experiment_id'],filename=r['filename'],size=r['size'],sha256=r['sha256'],status=status,engineState=job['state'] if job else None,revision=r['revision'],jobRevision=job['revision'] if job else None,jobId=r['job_id'],rows=rows(result),reviewRows=rows(review['result']) if review else None,suggestedScore=(result or {}).get('suggested_score'),scoreInterval=(result or {}).get('score_interval'),reviewScore=review['result']['suggested_score'] if review else None,publishedScore=publication['score'] if publication else None,reviewId=review['id'] if review else None,created=r['created_at'],matchReason=r['match_reason'],demo=False,active=bool(r['active']),identityFlag=ctx.get('identity_status','verified')!='verified',blockingFlags=ctx.get('blocking_flags',[]),error=job['error'] if job else None,task=active[0] if active else None,pages=len([e for e in ctx.get('evidence',[]) if e.get('role')=='page_context']),images=len([e for e in ctx.get('evidence',[]) if e['kind']=='image']))
        dto['pages']=(ctx.get('evidence_plan') or {}).get('coverage',{}).get('page_count',len([e for e in ctx.get('evidence',[]) if e['kind']=='image' and (e.get('role')=='page_context' or not e.get('role'))]))
        dto['lastTask']=latest
        dto.update(deletedAt=r['deleted_at'],isNewVersion=bool(self.version_hint(r,student).get('is_new')),
                   versionHint=self.version_hint(r,student),
                   manualFinalReportId=manual[0] if manual else None,
                   canDelete=not r['deleted_at'] and not active and not publication and status in ('received','error','unmatched','duplicate','superseded'))
        dto.update(verifiedSuggestedScore=(result or {}).get('suggested_score'),hasEstimates=bool(recommendation and recommendation['has_estimates']),reviewPriorityCount=recommendation['priority_count'] if recommendation else 0,advisoryCount=recommendation['advisory_count'] if recommendation else 0)
        if recommendation:dto['suggestedScore']=recommendation['score']
        dto['scopeGroupIds']=[r['group_id'],*[g['id'] for g in c['groups'] if r['group_id'] in g['sourceGroupIds']]]
        dto['error']=dto['error'] or (latest['error'] if latest and latest['state'] in ('failed','interrupted') else None)
        if detail:
            dto['candidateStudent']=identity_candidate(r['filename']) if not student else None
            dto.update(context=ctx,result=result,recommendation=recommendation,review=review,publication=publication,rubric=job['rubric'] if job else load_rubric(r['experiment_id']),history=self.store.events(r['id']))
            with self.store.connect() as db:
                dto['tasks']=[dict(t) for t in db.execute('SELECT * FROM tasks WHERE report_id=? ORDER BY created_at DESC',(r['id'],))]
                dto['versions']=[{**dict(v),'isNewVersion':bool(self.version_hint(dict(v),student).get('is_new'))} for v in db.execute('SELECT id,filename,active,created_at,version_hint FROM reports WHERE deleted_at IS NULL AND group_id=? AND student_id IS ? AND experiment_id=?',(r['group_id'],r['student_id'],r['experiment_id']))] if student else []
            if job:
                with self.backend(r['group_id']).store.connect() as db:
                    dto['attempts']=[dict(created_at=t[0],metadata=json.loads(t[1])) for t in db.execute('SELECT created_at,metadata FROM attempts WHERE job_id=? ORDER BY created_at',(job['id'],))]
                    dto['responseProblem']=response_problem(dto['attempts'][-1]['metadata'].get('visible_response')) if job['state']=='model_failed' and dto['attempts'] else None
                    dto['jobs']=[dict(j) for j in db.execute('SELECT id,state,revision,created_at FROM jobs WHERE submission_id=? ORDER BY created_at',(r['engine_submission_id'],))]
        return dto

    def detail(self,rid):return self.describe(self.store.report(rid),detail=True)

    def workspace(self):
        c=self.store.catalog()
        rows,total=self.store.reports(limit=100000)
        deleted,_=self.store.reports(limit=100000,deleted=True)
        return {**c,'reports':[self.describe(r,c) for r in rows],'deletedReports':[self.describe(r,c) for r in deleted],'reportCount':total,'settings':self.settings(),'rosterImports':[],'schema':3}

    def job_operation(self,rid,kind,payload):
        with self.lock:
            r=self.check_report(rid,payload['report_revision'])
            require(r['active'] and r['job_id'],'请选择已创建任务的有效版本')
            backend=self.backend(r['group_id']);job=backend.store.job(r['job_id'])
            require(job['revision']==payload['job_revision'],'评分任务已更新，请刷新')
            actor,reason=payload['actor'],payload['reason']
            require(clean(actor) and clean(reason),'请输入操作者和操作理由')
            if kind=='resolve':
                result=backend.resolve_context(job['id'],reviewer=actor,reason=reason,identity_status=payload.get('identity_status'),clear_flags=payload.get('clear_flags',[]),output_id_match=payload.get('output_id_match'))
            elif kind=='review':
                result=backend.review(job['id'],payload['decisions'],reviewer=actor,reason=reason,expected_revision=job['revision'],accept_estimates=payload.get('accept_estimates',False))
            elif kind=='publish':
                result=backend.publish(job['id'],review_id=payload['review_id'],expected_revision=job['revision'])
            else:raise ValueError('未知操作')
            with self.store.connect(True) as db:
                db.execute('UPDATE reports SET revision=revision+1 WHERE id=?',(rid,))
                self.store.event(db,kind,rid,actor,reason,{'job_id':job['id']})
            return result

    def original(self,rid):
        r=self.store.report(rid);path=self.store.path(r['stored_file'])
        require(path.is_file() and sha256_file(path)==r['sha256'],'报告原件缺失或校验失败')
        return path,r['filename']

    def evidence(self,rid,eid):
        r=self.store.report(rid)
        require(r['job_id'],'尚未提取证据')
        backend=self.backend(r['group_id']);ctx=backend.store.job(r['job_id'])['context'] or {}
        entry=next((e for e in ctx.get('evidence',[]) if e['id']==eid),None)
        require(entry and entry['kind']=='image','图片证据不存在')
        path=backend.store.path(str(Path(ctx['extraction_dir'])/entry['file']))
        require(path.is_file() and sha256_file(path)==entry['sha256'],'证据图片缺失或校验失败')
        return path

    def export_csv(self,group_id,experiment_id):
        c=self.store.catalog();self.store.group_scope(group_id);load_rubric(experiment_id)
        roster=[s for s in c['students'] if dict(groupId=group_id,studentId=s['id']) in c['memberships']]
        raw,_=self.store.reports(group_id,limit=100000)
        reports=[self.describe(r,c) for r in raw if r['experiment_id']==experiment_id and r['active']]
        output=io.StringIO(newline='');writer=csv.writer(output)
        writer.writerow(['学号','姓名','实验','状态','模型建议','教师复核','正式成绩','报告文件','报告指纹','原班级'])
        for s in roster:
            matches=[r for r in reports if r['studentId']==s['id']]
            # Distinct source-group grades stay distinct if a student joins both.
            for r in matches or [{}]:
                names='、'.join(g['name'] for g in c['groups'] if not g['sourceGroupIds'] and g['id'] in self.store.group_scope(group_id) and dict(groupId=g['id'],studentId=s['id']) in c['memberships'])
                writer.writerow([_csv_safe(x) for x in [s['number'],s['name'],experiment_id,STATUS_LABELS.get(r.get('status'),'未交或版本待选'),r.get('suggestedScore'),r.get('reviewScore'),r.get('publishedScore'),r.get('filename'),r.get('sha256'),r.get('className',names)]])
        return ('\ufeff'+output.getvalue()).encode('utf-8')
