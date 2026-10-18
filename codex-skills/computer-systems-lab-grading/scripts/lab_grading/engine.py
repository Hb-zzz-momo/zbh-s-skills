"""Deterministic scoring of an externally judged, version-bound evidence packet."""
import hashlib
import json
import re
from pathlib import Path

KINDS = {'answer', 'code', 'execution', 'identity'}
VERDICTS = {'full', 'minor', 'partial', 'zero', 'unresolved'}


def fingerprint(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def load_rubric(experiment_id):
    require(isinstance(experiment_id, str) and re.fullmatch(r'exp(0[1-9]|1[0-6])', experiment_id), 'invalid experiment id')
    value = json.loads((Path(__file__).parent / 'rubrics' / (experiment_id + '.json')).read_text('utf-8'))
    validate_rubric(value)
    return value


def validate_rubric(rubric):
    require(rubric['schema_version'] == '1.0', 'unsupported rubric schema')
    require(rubric['max_points'] == 100, 'rubric must total 100')
    ids, total = set(), 0
    for section in rubric['sections']:
        subtotal = 0
        for item in section['criteria']:
            cid, points, partial = item['id'], item['max_points'], item['partial_points']
            require(cid not in ids and cid.startswith(rubric['experiment_id'] + '.'), 'duplicate/mismatched criterion id')
            require(type(points) is int and points > 0, 'invalid points')
            require((partial is None and item['evidence_type'] == 'identity') or
                    (type(partial) in (int, float) and 0 < partial < points and partial * 2 == int(partial * 2)), 'invalid partial points')
            require(item['evidence_type'] in KINDS, 'unknown evidence type')
            if item.get('minor_points') is not None:
                minor=item['minor_points']
                require(item['evidence_type']!='identity' and type(minor) in (int,float) and partial<minor<points and minor==round(points*.85,2),'invalid minor points')
                require(nonempty(item.get('minor_credit')),'missing minor anchor')
            require(all(nonempty(item[k]) for k in ('full_credit', 'partial_credit', 'zero_credit')), 'missing anchors')
            ids.add(cid)
            subtotal += points
        require(subtotal == section['max_points'], 'section total mismatch')
        require(nonempty(section['source_anchor']), 'missing source anchor')
        total += subtotal
    require(total == 100, 'total mismatch')
    return len(ids)


def validate_context(context, rubric):
    """Context is created by the backend, never taken from model JSON."""
    require(context['experiment_id'] == rubric['experiment_id'], 'experiment mismatch')
    require(context['rubric_sha256'] == fingerprint(rubric), 'rubric changed')
    require(bool(context.get('calibration_enabled'))==bool(rubric.get('calibration_policy')),'calibration policy/context mismatch')
    require(bool(re.fullmatch('[0-9a-f]{64}', context['report_sha256'])), 'invalid report hash')
    require(type(context['extraction_complete']) is bool, 'invalid completeness flag')
    require(context['identity_status'] in ('verified', 'conflict', 'unknown'), 'invalid identity status')
    require(isinstance(context['blocking_flags'], list) and all(nonempty(x) for x in context['blocking_flags']), 'invalid flags')
    require(nonempty(context['request_id']) and nonempty(context['model_requested']), 'missing request identity')
    catalog = context['evidence']
    require(isinstance(catalog, list), 'catalog must be a list')
    ids = set()
    for entry in catalog:
        require(nonempty(entry['id']) and entry['id'] not in ids, 'duplicate evidence id')
        ids.add(entry['id'])
        require(entry['kind'] in ('text', 'code', 'image', 'terminal', 'identity'), 'invalid evidence kind')
        require(entry['origin'] == 'student', 'answer key/template cannot be student evidence')
        require(nonempty(entry['locator']), 'evidence needs a page/paragraph/image locator')
        require(bool(re.fullmatch('[0-9a-f]{64}', entry['sha256'])), 'evidence hash missing')
        require(type(entry['readable']) is bool, 'invalid readable flag')
        if entry['kind'] == 'identity':
            require(entry.get('match') in (True, False, None), 'invalid identity evidence')
        else:
            require(nonempty(entry.get('text')) or entry['kind'] == 'image', 'missing evidence text')
            if entry['kind'] != 'image':
                require(hashlib.sha256(entry['text'].encode('utf-8')).hexdigest() == entry['sha256'], 'text content differs from evidence hash')
    require(context['evidence_sha256'] == fingerprint(catalog), 'evidence catalog changed')
    if 'evidence_plan' in context:
        require(context.get('evidence_plan_sha256')==fingerprint(context['evidence_plan']),'evidence plan changed')
        criteria={c['id'] for s in rubric['sections'] for c in s['criteria']}
        packets=context['evidence_plan']['criteria']
        require(len(packets)==len(criteria) and {p['criterion_id'] for p in packets}==criteria,'evidence plan missing/duplicate criteria')
        require(all(set(p['candidate_evidence_ids'])<=ids for p in packets),'evidence plan references unknown evidence')
        require(all(e.get('role') in ('student_answer','question','instruction','example','metadata','ambiguous','page_context') or e['kind']=='identity' for e in catalog),'invalid structured evidence role')


def binding(context):
    keys=('experiment_id', 'rubric_sha256', 'report_sha256', 'evidence_sha256', 'request_id', 'model_requested')
    if 'evidence_plan_sha256' in context:keys+=('evidence_plan_sha256',)
    return {k: context[k] for k in keys}


def aggregate(rubric, result, context, *, absence_audits=None, human_review=False,accepted_estimates=None):
    """Return a suggestion and uncertainty interval; never release a final grade.

    Model omissions/invalid JSON raise ValueError, rather than becoming zero.
    An unresolved item contributes [0,max] to the interval. Trusted extraction
    or identity failures block even a numerically complete suggestion.
    """
    validate_rubric(rubric)
    validate_context(context, rubric)
    require(set(result) == {'binding', 'judgments'}, 'unexpected result fields (model cannot set totals)')
    require(result['binding'] == binding(context), 'stale/cross-report/model result')
    criteria = {c['id']: c for s in rubric['sections'] for c in s['criteria']}
    evidence = {e['id']: e for e in context['evidence']}
    accepted_estimates=accepted_estimates or {}
    require(not accepted_estimates or human_review,'AI汇总不能自行接受推定评分')
    require(set(accepted_estimates)<=set(criteria),'推定评分项不存在')
    require(isinstance(result['judgments'], list), 'judgments must be a list')
    seen, rows, lower, upper = set(), [], 0, 0
    for judgment in result['judgments']:
        require(set(judgment) == {'criterion_id', 'verdict', 'evidence_ids', 'observation', 'reason', 'missing'}, 'invalid judgment fields')
        cid, verdict = judgment['criterion_id'], judgment['verdict']
        require(cid in criteria and cid not in seen, 'duplicate/unknown judgment')
        seen.add(cid)
        require(verdict in VERDICTS, 'invalid verdict')
        require(nonempty(judgment['reason']) and nonempty(judgment['observation']), 'missing reviewable rationale')
        refs = judgment['evidence_ids']
        require(isinstance(refs, list) and all(isinstance(x, str) for x in refs) and len(refs) == len(set(refs)), 'invalid evidence references')
        require(all(r in evidence for r in refs), 'nonexistent evidence')
        missing = judgment['missing']
        require(type(missing) is bool, 'missing must be boolean')
        item = criteria[cid]
        estimated=cid in accepted_estimates
        if estimated:
            require(accepted_estimates[cid]==judgment and item['evidence_type']!='identity' and not missing and verdict!='unresolved','推定接受记录与评分不一致')
        require(verdict!='minor' or item.get('minor_points') is not None,'minor tier unavailable for this frozen criterion')
        if verdict == 'unresolved':
            require(not missing, 'unresolved cannot mean confirmed missing')
            awarded = None
            upper += item['max_points']
        else:
            if missing:
                require(verdict == 'zero' and context['extraction_complete'], 'missing requires complete extraction and zero verdict')
                require(all(e['readable'] for e in evidence.values()), 'unreadable evidence cannot justify absence')
                from .auto_review import absence_verified
                require(((human_review or not context.get('calibration_enabled')) and set(refs)==set(evidence)) or absence_verified(context,cid,(absence_audits or {}).get(cid)), 'absence requires documented search of the complete evidence catalog')
            elif not estimated:
                require(bool(refs) and all(evidence[r]['readable'] for r in refs), 'resolved judgment needs readable evidence')
                if 'evidence_plan' in context:
                    require(any(evidence[r].get('role')=='student_answer' or evidence[r]['kind']=='identity' for r in refs), 'teaching context/page alone cannot support student grade')
                if verdict in ('full','minor') and item.get('evidence_mode')=='both':
                    source=[evidence[r] for r in refs if evidence[r].get('role')=='student_answer']
                    require(any(e['kind']=='image' for e in source) and any(e['kind'] in ('text','code','terminal') for e in source),'joint evidence requires student image and text')
                if verdict in ('full','minor') and item['evidence_type'] == 'execution' and item.get('evidence_mode') not in ('both','either'):
                    require(any(evidence[r]['kind'] in ('image', 'terminal') for r in refs), 'execution credit requires image/terminal evidence')
                    if 'evidence_plan' in context:
                        require(any(evidence[r]['kind'] in ('image','terminal') and evidence[r].get('role')=='student_answer' for r in refs),'execution credit requires student original evidence')
                if item['evidence_type'] == 'identity':
                    identity = [evidence[r] for r in refs if evidence[r]['kind'] == 'identity']
                    require(identity, 'identity must be checked outside the grading model')
                    if verdict == 'full':
                        require(any(e.get('match') is True for e in identity), 'full identity credit requires verified match')
                    require(verdict not in ('partial','minor'), 'ambiguous identity requires unresolved, not partial credit')
            awarded = {'full': item['max_points'], 'minor':item.get('minor_points'), 'partial': item['partial_points'], 'zero': 0}[verdict]
            lower += awarded
            upper += awarded
        rows.append({**judgment, 'max_points': item['max_points'], 'awarded_points': awarded,'estimated':estimated})
    require(seen == set(criteria), 'missing judgments; retry the missing items, never auto-zero')
    blocks = list(context['blocking_flags'])
    if not context['extraction_complete']:
        blocks.append('extraction_incomplete')
    if context['identity_status'] != 'verified':
        blocks.append('identity_' + context['identity_status'])
    unresolved = [r['criterion_id'] for r in rows if r['awarded_points'] is None]
    if unresolved:
        blocks.append('unresolved_items')
    lower,upper=round(lower,2),round(upper,2)
    return {'binding': binding(context), 'rubric_version': rubric['rubric_version'],
            'status': 'needs_review' if blocks else 'ready_for_teacher_review',
            'suggested_score': None if blocks else lower, 'score_interval': [lower, upper],
            'final_score': None, 'release_status': 'not_released',
            'blocking_flags': sorted(set(blocks)), 'unresolved_items': unresolved,
            'rows': rows, 'accepted_estimate_items':sorted(accepted_estimates), 'result_sha256': fingerprint(result)}
