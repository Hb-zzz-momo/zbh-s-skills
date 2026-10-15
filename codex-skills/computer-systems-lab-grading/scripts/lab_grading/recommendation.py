"""Rubric-tier proposals and a short impact-prioritized teacher review queue.

Proposals are separate from strict model results. Only explicit teacher acceptance
can turn their uncertain items into a reviewed grade.
"""
import copy
from .engine import binding, fingerprint, require, validate_context

DEFAULT_POLICY=dict(item_points=6,group_points=10,max_groups=3)
FIELDS=('criterion_id','verdict','evidence_ids','observation','reason','missing')


def review_policy(value=None):
    value=value or {}
    require(isinstance(value,dict) and set(value)<=set(DEFAULT_POLICY),'重点复核设置字段无效')
    result={**DEFAULT_POLICY,**value}
    for key in ('item_points','group_points'):
        require(type(result[key]) in (int,float) and 1<=result[key]<=100,'重点复核分值应在1至100之间')
    require(type(result['max_groups']) is int and 1<=result['max_groups']<=5,'重点复核组数应在1至5之间')
    return result


def proposal(rubric,context,result,source_judgments=None,policy=None):
    validate_context(context,rubric)
    require(result.get('binding')==binding(context),'建议分不能跨报告或版本引用')
    rules={c['id']:c for s in rubric['sections'] for c in s['criteria']}
    evidence={e['id']:e for e in context['evidence']}
    packets={p['criterion_id']:p for p in context.get('evidence_plan',{}).get('criteria',[])}
    source={r['criterion_id']:r for r in (source_judgments or result.get('source_judgments',[])) if r.get('criterion_id') in rules}
    policy=review_policy(policy)
    rows=[];groups={};blockers=list(context.get('blocking_flags',[]));estimates=[];required=[]
    hard_reasons={'guarded_invalid_tiers':'存在未核实的评分档位','guarded_unreadable_claims':'存在不可读的原始证据','guarded_invalid_facts':'存在格式异常的事实记录'}
    hard={cid for flag in hard_reasons for cid in result.get(flag,[])}
    if not context['extraction_complete']:blockers.append('extraction_incomplete')
    if context['identity_status']!='verified':blockers.append('identity_'+context['identity_status'])
    for original in result['rows']:
        row=copy.deepcopy(original);cid=row['criterion_id'];rule=rules[cid]
        row['estimated']=False
        if row['verdict']=='unresolved' and rule['evidence_type']=='identity':
            blockers.append('identity_item_unresolved')
        elif row['verdict']=='unresolved' and cid in hard:
            # A conservative quarantine must not reappear as full/partial/zero
            # through the separate convenience proposal layer.
            required.append(cid);row.update(required_review=True,impact_points=rule['max_points'])
            blockers.extend(label for flag,label in hard_reasons.items() if cid in result.get(flag,[]))
            if 'required' not in groups:
                groups['required']=dict(key='required',title='评分依据必须核对',criterion_ids=[],impact_points=0,max_item_points=0,required=True)
            group=groups['required'];group['criterion_ids'].append(cid)
            group['impact_points']=round(group['impact_points']+rule['max_points'],2)
            group['max_item_points']=max(group['max_item_points'],rule['max_points'])
        elif row['verdict']=='unresolved':
            raw=source.get(cid,{})
            candidates=list(dict.fromkeys([*raw.get('evidence_ids',[]),*row['evidence_ids'],
                *packets.get(cid,{}).get('candidate_evidence_ids',[])]))
            candidates=[e for e in candidates if e in evidence and evidence[e]['readable']]
            student=[e for e in candidates if evidence[e].get('role')=='student_answer' or
                     ('evidence_plan' not in context and evidence[e]['kind']!='identity')]
            tentative=[e for e in candidates if evidence[e].get('role')=='ambiguous']
            verdict=raw.get('verdict','unresolved')
            if verdict not in ('full','minor','partial','zero'):verdict='partial' if student or tentative else 'zero'
            if verdict=='minor' and rule.get('minor_points') is None:verdict='partial'
            if verdict in ('full','minor'):
                if not student or cid in result.get('guarded_fact_claims',[]):verdict='partial' if student or tentative else 'zero'
                if rule.get('evidence_mode')=='both' and not (
                    any(evidence[e]['kind']=='image' for e in student) and
                    any(evidence[e]['kind'] in ('text','code','terminal') for e in student)):verdict='partial' if student or tentative else 'zero'
                if rule['evidence_type']=='execution' and rule.get('evidence_mode') not in ('both','either') and not any(evidence[e]['kind'] in ('image','terminal') for e in student):verdict='partial' if student or tentative else 'zero'
            if verdict=='partial' and rule['partial_points'] is None:verdict='zero'
            refs=student or tentative
            row.update(verdict=verdict,evidence_ids=refs,missing=False,estimated=True,
                awarded_points={'full':rule['max_points'],'minor':rule.get('minor_points'),'partial':rule['partial_points'],'zero':0}[verdict],
                original_verdict='unresolved',original_reason=original['reason'],
                reason=('AI推定建议：按冻结评分标准的'+{'full':'满分','minor':'轻微不足','partial':'部分分','zero':'暂按未体现采分点'}[verdict]+'档计分；尚未逐项人工核实。'+
                        ('已配对原始作答候选，内容仍需按本项核对。' if student else '作答来源或覆盖仍有疑点。')))
            estimates.append(cid)
            key='facts' if cid in result.get('guarded_fact_claims',[]) else 'absence' if cid in result.get('guarded_absence_claims',[]) else 'source' if cid in result.get('guarded_context_claims',[]) else 'other'
            if key not in groups:groups[key]=dict(key=key,title={'facts':'关键命令或解释','absence':'可能漏读或缺答','source':'作答来源归属','other':'其他证据疑点'}[key],criterion_ids=[],impact_points=0,max_item_points=0)
            groups[key]['criterion_ids'].append(cid)
            # Maximum possible change from the proposed legal tier.
            impact=max(row['awarded_points'],rule['max_points']-row['awarded_points'])
            row['impact_points']=impact
            groups[key]['impact_points']=round(groups[key]['impact_points']+impact,2)
            groups[key]['max_item_points']=max(groups[key]['max_item_points'],impact)
        rows.append(row)
    ordered=sorted(groups.values(),key=lambda g:(not g.get('required',False),-g['impact_points'],g['key']))
    eligible=[g for g in ordered if g.get('required') or g['max_item_points']>=policy['item_points'] or g['impact_points']>=policy['group_points']]
    priority=eligible[:policy['max_groups']]
    priority_keys={g['key'] for g in priority}
    advisories=[g for g in ordered if g['key'] not in priority_keys]
    score=round(sum(r['awarded_points'] or 0 for r in rows),2)
    output=dict(binding=binding(context),score=score if all(r['awarded_points'] is not None for r in rows) else None,
        rows=rows,estimated_items=estimates,has_estimates=bool(estimates),required_review_items=required,priority_groups=priority,
        advisory_groups=advisories,advisory_count=sum(len(g['criterion_ids']) for g in advisories),
        priority_count=len(priority),blocking_flags=sorted(set(blockers)),policy=policy,
        method='frozen-rubric-tiers',status='priority_review' if priority or blockers else 'suggested')
    output['proposal_sha256']=fingerprint(output)
    return output
