"""Uniform rubric policies and honest, non-publishing distribution previews."""
import copy
import math
import re
from .engine import fingerprint, load_rubric, require, validate_rubric


def default_policy():
    return dict(dual_ratio=.5, section_weights={}, target_mean=85, target_sd=8, auto_review=True)


def validate_policy(value, experiment_id):
    require(isinstance(value,dict),'评分政策必须为对象')
    require(set(value)<=set(default_policy()),'未知评分政策字段')
    p={**default_policy(),**value}
    for key,lo,hi in [('dual_ratio',0,1),('target_mean',0,100),('target_sd',1,30)]:
        require(type(p[key]) in (int,float) and math.isfinite(p[key]) and lo<=p[key]<=hi,f'{key}超出允许范围')
    require(type(p['auto_review']) is bool,'自动复查开关必须为布尔值')
    r=load_rubric(experiment_id);sections={s['id'] for s in r['sections']}
    require(isinstance(p['section_weights'],dict) and set(p['section_weights'])<=sections,'章节权重包含未知章节')
    require(all(type(v) in (int,float) and math.isfinite(v) and .25<=v<=3 for v in p['section_weights'].values()),'章节倍率须在0.25—3之间')
    return copy.deepcopy(p)


def apply_policy(rubric, value):
    """Allocate 100 integer points, then freeze one dual-evidence set for everyone.

    Positive lower bounds preserve every criterion. Largest remainders and a
    deterministic subset search avoid per-student/rank-dependent adjustments.
    """
    p=validate_policy(value,rubric['experiment_id']);r=copy.deepcopy(rubric)
    items=[c for s in r['sections'] for c in s['criteria']]
    masses=[c['max_points']*p['section_weights'].get(s['id'],1) for s in r['sections'] for c in s['criteria']]
    # Reserve one point per criterion; distribute the remainder proportionally
    # to the weighted entitlement with iterative lower-bound allocation.
    free=set(range(len(items)));alloc={};remaining=100
    while free:
        mass=sum(masses[i] for i in free)
        small=[i for i in free if remaining*masses[i]/mass<1]
        if not small:break
        for i in small:alloc[i]=1;free.remove(i);remaining-=1
    quotas={i:remaining*masses[i]/sum(masses[j] for j in free) for i in free}
    alloc.update({i:math.floor(q) for i,q in quotas.items()})
    for i in sorted(free,key=lambda i:(-(quotas[i]-alloc[i]),i))[:100-sum(alloc.values())]:alloc[i]+=1
    for i,c in enumerate(items):
        old=c['max_points'];new=alloc[i];c['base_max_points']=old;c['max_points']=new
        if c['partial_points'] is not None:
            c['partial_points']=min(new-.5,max(.5,round(c['partial_points']/old*new*2)/2))
        if c.get('minor_points') is not None:
            c['minor_points']=round(new*.85,2)
            if c['minor_points']<=c['partial_points']:c['minor_points']=None
    for s in r['sections']:
        s['max_points']=sum(c['max_points'] for c in s['criteria'])
        s['title']=re.sub(r'（\d+分）$',f"（{s['max_points']}分）",s['title'])
    candidates=sorted((c for c in items if c['evidence_type']!='identity'),
                      key=lambda c:(c['evidence_type'] not in ('execution','code'),c['id']))
    possibilities={0:()}
    for c in candidates:
        for total,ids in list(possibilities.items()):
            possibilities.setdefault(total+c['max_points'],ids+(c['id'],))
    chosen=min(possibilities,key=lambda n:(abs(n-100*p['dual_ratio']),n))
    dual=set(possibilities[chosen])
    for c in items:c['evidence_mode']='identity' if c['evidence_type']=='identity' else 'both' if c['id'] in dual else 'either'
    r['calibration_policy']={**p,'actual_dual_points':chosen,'dual_criterion_ids':sorted(dual),'policy_sha256':fingerprint(p)}
    r['rubric_version']=rubric['rubric_version']+'+policy-'+fingerprint(p)[:10]
    validate_rubric(r)
    return r


def interval_for(rows,rubric):
    """Reweight existing verdicts only: a preview cannot invent missing judgments."""
    by_id={x['criterion_id']:x for x in rows};lo=hi=0
    for s in rubric['sections']:
        for c in s['criteria']:
            verdict=by_id.get(c['id'],{}).get('verdict','unresolved')
            if verdict=='unresolved':hi+=c['max_points'];continue
            value={'full':c['max_points'],'minor':c.get('minor_points'),'partial':c['partial_points'],'zero':0}.get(verdict)
            if value is None:hi+=c['max_points'];continue
            lo+=value;hi+=value
    return [round(lo,2),round(hi,2)]


def distribution(values,mean=85,sd=8):
    bins=[0]*10
    for v in values:bins[min(9,int(v//10))]+=1
    n=len(values);mu=sum(values)/n if n else None
    spread=math.sqrt(sum((v-mu)**2 for v in values)/n) if n else None
    cdf=lambda x:.5*(1+math.erf((x-mean)/(sd*math.sqrt(2))))
    area=cdf(100)-cdf(0)
    expected=[round(n*(cdf(i+10)-cdf(i))/area,3) for i in range(0,100,10)]
    curve=[max(1,n)*10/(sd*math.sqrt(2*math.pi)*area)*math.exp(-((x-mean)**2)/(2*sd*sd)) for x in range(101)]
    return dict(count=n,mean=round(mu,2) if n else None,sd=round(spread,2) if n else None,
                bins=bins,normal_reference=expected,normal_curve=curve,small_sample=n<20,
                note='正态曲线仅为截断到0—100分的参考；小样本不能判断是否服从正态分布。')


def preview(reports,rubric,policy):
    target=apply_policy(rubric,policy);current=[];trial=[];rows=[]
    for report in reports:
        if not report.get('active') or not report.get('rows'):continue
        interval=interval_for(report['rows'],target)
        complete=report['status'] in ('scored','reviewed','published') and report.get('suggestedScore') is not None and interval[0]==interval[1]
        if complete:current.append(report['suggestedScore']);trial.append(interval[0])
        rows.append(dict(id=report['id'],name=report['name'],before=report.get('scoreInterval'),after=interval,
                         included=complete,status=report['status']))
    p=target['calibration_policy']
    return dict(policy=p,rubric=target,rows=rows,current=distribution(current,p['target_mean'],p['target_sd']),
                preview=distribution(trial,p['target_mean'],p['target_sd']),excluded=len(rows)-len(trial),
                notice='仅对已有档位做权重试算。图文比例变化需新建批阅版本；未决区间不取中点，不覆盖教师复核或正式成绩。')


def recommend(reports,rubric,policy):
    """Suggest bounded, uniform chapter weights; never quantile-map individuals."""
    p=validate_policy(policy,rubric['experiment_id'])
    start=preview(reports,rubric,p)
    require(start['preview']['count']>=20,'至少需要20份无未决项的建议分才提供分布权重建议；当前可手动预览，不能据小样本拟合正态。')
    def objective(candidate):
        result=preview(reports,rubric,candidate);d=result['preview'];n=d['count']
        error=((d['mean']-p['target_mean'])/10)**2+((d['sd']-p['target_sd'])/5)**2
        error+=sum(((a-b)/n)**2 for a,b in zip(d['bins'],d['normal_reference']))
        error+=.15*sum(math.log(v)**2 for v in candidate['section_weights'].values())
        return error,result
    best=p;score,result=objective(best)
    for _ in range(8):
        improved=False
        for s in rubric['sections']:
            for delta in (-.25,.25):
                candidate=copy.deepcopy(best);value=candidate['section_weights'].get(s['id'],1)+delta
                if not .5<=value<=2:continue
                candidate['section_weights'][s['id']]=value
                trial,data=objective(candidate)
                if trial<score-1e-6:best,score,result=candidate,trial,data;improved=True
        if not improved:break
    return {**result,'recommended_policy':best,'notice':'这是有限范围的统一章节权重建议，需教师检查教学合理性后保存；不保证分布正态，不按排名换分。'+result['notice']}
