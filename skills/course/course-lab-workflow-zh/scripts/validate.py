#!/usr/bin/env python3
"""Read-only checks for this skill package and its optional evidence register.

Python 3.9+, standard library only. No network, shell execution, or file changes.
A successful check establishes schema/consistency only, NOT evidence authenticity,
course compliance, runtime correctness, or document visual quality.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

EXECUTION = {'not_started', 'attempted', 'passed', 'failed', 'blocked', 'not_applicable'}
EVIDENCE_STATES = {'verified', 'user_reported', 'unverified', 'example', 'missing'}
KINDS = {'screenshot', 'log', 'output', 'source', 'user_statement', 'example'}
RUN_KINDS = {'screenshot', 'log', 'output'}


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def inside(base: Path, relative: str) -> Path:
    """Resolve a portable relative path; reject absolute paths and traversal."""
    if '\\' in relative or re.match(r'^[A-Za-z]:', relative):
        raise ValueError('use a portable relative path with / separators')
    p = Path(relative)
    if p.is_absolute():
        raise ValueError('absolute paths are not allowed')
    target = (base / p).resolve()
    try:
        target.relative_to(base.resolve())
    except ValueError as exc:
        raise ValueError('path escapes the evidence/package directory') from exc
    return target


def validate_package(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    main = root / 'SKILL.md'
    if not main.is_file():
        return {'errors': ['SKILL.md not found'], 'warnings': [], 'summary': {}}
    content = main.read_text(encoding='utf-8-sig')
    match = re.match(r'^---\r?\n(.*?)\r?\n---(?:\r?\n|$)', content, re.S)
    if not match:
        errors.append('SKILL.md must start with YAML frontmatter delimited by ---')
    else:
        # Checks the simple single-line name/description format used in this package.
        # This is intentionally not a full YAML parser or a universal spec validator.
        header = match.group(1)
        fields = {}
        for key in ('name', 'description'):
            found = re.findall(r'^' + key + r':\s*(.*?)\s*$', header, flags=re.M)
            if len(found) != 1:
                errors.append(f'frontmatter requires exactly one {key}')
            else:
                fields[key] = found[0].strip('"\'')
        name = fields.get('name', '')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or len(name) > 64:
            errors.append('invalid skill name')
        if name != root.name:
            errors.append('skill name must match the parent directory name')
        description = fields.get('description', '')
        if not 1 <= len(description) <= 1024:
            errors.append('description length must be between 1 and 1024 characters')
    lines = len(content.splitlines())
    if lines > 500:
        warnings.append('SKILL.md exceeds 500 lines; consider moving details to references')
    links = 0
    for source in root.rglob('*.md'):
        body = source.read_text(encoding='utf-8-sig')
        for raw in re.findall(r'\[[^\]]*\]\(([^)]+)\)', body):
            dest = raw.strip().split('#', 1)[0]
            if not dest or '://' in dest or dest.startswith('mailto:'):
                continue
            # Package uses link paths without optional Markdown titles/spaces.
            try:
                target = (source.parent / dest).resolve()
                target.relative_to(root.resolve())
            except ValueError:
                errors.append(f'{source.relative_to(root)}: link escapes package: {dest}')
                continue
            links += 1
            if not target.is_file():
                errors.append(f'{source.relative_to(root)}: missing linked file: {dest}')
    case_path = root / 'evals' / 'cases.json'
    case_count = 0
    if case_path.is_file():
        try:
            cases = json.loads(case_path.read_text(encoding='utf-8-sig'))
            values = cases.get('cases', []) if isinstance(cases, dict) else []
            seen: set[str] = set()
            for case in values:
                if not isinstance(case, dict) or not text(case.get('id')):
                    errors.append('eval case is missing a valid id')
                    continue
                if case['id'] in seen:
                    errors.append(f'duplicate eval case: {case["id"]}')
                seen.add(case['id'])
                if not text(case.get('prompt')) or not case.get('must'):
                    errors.append(f'incomplete eval case: {case["id"]}')
            case_count = len(values)
            if not case_count:
                errors.append('no behavior evaluation cases found')
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f'cannot parse eval cases: {exc}')
    else:
        errors.append('evals/cases.json missing')
    return {'errors': errors, 'warnings': warnings,
            'summary': {'skill_lines': lines, 'local_links_checked': links,
                        'behavior_cases_defined': case_count,
                        'behavior_cases_executed_by_this_check': 0}}


def validate_record(data: Any, base: Path, *, check_files: bool = False,
                    require_ready: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return {'errors': ['register must be a JSON object'], 'warnings': [], 'summary': {}}
    for field in ('lab_id', 'attempt_id'):
        if not text(data.get(field)):
            errors.append(f'{field} must be non-empty')
        elif str(data[field]).startswith('replace-with-'):
            warnings.append(f'{field} still contains the template value')
    if data.get('schema_version') != '1.0':
        errors.append('schema_version must be "1.0"')
    report_status = data.get('report_status')
    if not isinstance(report_status, str) or report_status not in {'draft', 'ready_for_review'}:
        errors.append('report_status must be draft or ready_for_review')
    required_ready = require_ready or report_status == 'ready_for_review'
    requirements = data.get('requirements')
    evidence = data.get('evidence')
    if not isinstance(requirements, list) or not requirements:
        errors.append('requirements must be a non-empty array')
        requirements = []
    if not isinstance(evidence, list):
        errors.append('evidence must be an array')
        evidence = []

    by_id: dict[str, dict[str, Any]] = {}
    checked = 0
    for i, item in enumerate(evidence):
        prefix = f'evidence[{i}]'
        if not isinstance(item, dict):
            errors.append(f'{prefix} must be an object')
            continue
        eid = item.get('id')
        if not text(eid):
            errors.append(f'{prefix}.id must be non-empty')
            continue
        if eid in by_id:
            errors.append(f'duplicate evidence id: {eid}')
        by_id[eid] = item
        for key in ('lab_id', 'attempt_id'):
            if item.get(key) != data.get(key):
                errors.append(f'{eid}: {key} does not match this register')
        state, kind = item.get('verification'), item.get('kind')
        if not isinstance(state, str) or state not in EVIDENCE_STATES:
            errors.append(f'{eid}: invalid verification')
            state = None
        if not isinstance(kind, str) or kind not in KINDS:
            errors.append(f'{eid}: invalid kind')
            kind = None
        if not text(item.get('description')):
            errors.append(f'{eid}: description must say what the evidence supports')
        if kind == 'example' and state != 'example':
            errors.append(f'{eid}: example evidence must be marked example')
        if kind == 'user_statement' and state != 'user_reported':
            errors.append(f'{eid}: a user statement cannot be marked independently verified')
        path = item.get('path', '')
        if not isinstance(path, str):
            errors.append(f'{eid}: path must be a string')
            path = ''
        if state == 'verified' and kind in RUN_KINDS | {'source'} and not path:
            errors.append(f'{eid}: verified file evidence requires a local relative path')
        if path:
            try:
                target = inside(base, path)
                if check_files:
                    if not target.is_file() or target.stat().st_size == 0:
                        errors.append(f'{eid}: evidence file is missing or empty: {path}')
                    else:
                        checked += 1
            except (ValueError, OSError) as exc:
                errors.append(f'{eid}: {exc}')
        elif kind == 'user_statement' and not text(item.get('locator')):
            errors.append(f'{eid}: user statement needs a message/source locator')

    rids: set[str] = set()
    ready_ids, pending_ids = [], []
    required_count = 0
    for i, req in enumerate(requirements):
        prefix = f'requirements[{i}]'
        if not isinstance(req, dict):
            errors.append(f'{prefix} must be an object')
            continue
        rid = req.get('id')
        if not text(rid):
            errors.append(f'{prefix}.id must be non-empty')
            continue
        if rid in rids:
            errors.append(f'duplicate requirement id: {rid}')
        rids.add(rid)
        for field in ('title', 'validation'):
            if not text(req.get(field)):
                errors.append(f'{rid}: {field} is required')
        if not isinstance(req.get('required'), bool):
            errors.append(f'{rid}: required must be boolean')
        required = req.get('required') is True
        required_count += int(required)
        execution, state = req.get('execution_status'), req.get('evidence_status')
        if not isinstance(execution, str) or execution not in EXECUTION:
            errors.append(f'{rid}: invalid execution_status')
            execution = None
        if not isinstance(state, str) or state not in EVIDENCE_STATES:
            errors.append(f'{rid}: invalid evidence_status')
            state = None
        ids = req.get('evidence_ids')
        if not isinstance(ids, list) or any(not text(x) for x in ids):
            errors.append(f'{rid}: evidence_ids must be an array of non-empty strings')
            ids = []
        if len(ids) != len(set(ids)):
            errors.append(f'{rid}: duplicate evidence references')
        linked = []
        for eid in ids:
            if eid not in by_id:
                errors.append(f'{rid}: unknown evidence reference: {eid}')
            else:
                linked.append(by_id[eid])
        if state == 'missing' and ids:
            errors.append(f'{rid}: missing evidence state conflicts with referenced evidence')
        if state not in {'missing', None} and not ids and execution != 'not_applicable':
            errors.append(f'{rid}: evidence state requires a source reference')
        if state == 'verified':
            if not linked or any(e.get('verification') != 'verified' for e in linked):
                errors.append(f'{rid}: verified status requires all cited evidence to be verified')
        if execution in {'passed', 'failed'} and not text(req.get('actual_result')):
            errors.append(f'{rid}: a completed verdict requires actual_result')
        if execution == 'passed':
            if state in {'missing', 'example', None}:
                errors.append(f'{rid}: a pass cannot be justified by missing/example evidence')
            if state == 'verified' and not any(isinstance(e.get('kind'), str) and e['kind'] in RUN_KINDS for e in linked):
                errors.append(f'{rid}: source code alone does not prove a verified run')
            if state == 'user_reported' and not any(e.get('kind') == 'user_statement' for e in linked):
                errors.append(f'{rid}: user_reported pass needs a user statement')
        na_ok = execution == 'not_applicable' and text(req.get('na_reason'))
        if execution == 'not_applicable' and not na_ok:
            errors.append(f'{rid}: not_applicable requires a reason grounded in course scope')
        ready = na_ok or (execution == 'passed' and state == 'verified')
        if required:
            (ready_ids if ready else pending_ids).append(rid)
            if required_ready and not ready:
                errors.append(f'{rid}: required item is not ready for review')
    if required_ready:
        if not required_count:
            errors.append('ready-for-review register needs at least one required item')
        for field in ('lab_id', 'attempt_id'):
            if str(data.get(field, '')).startswith('replace-with-'):
                errors.append(f'{field}: replace the template value before review')
    if pending_ids and not required_ready:
        warnings.append('required items remain pending: ' + ', '.join(pending_ids))
    if not check_files:
        warnings.append('file existence and content have not been inspected')
    warnings.append('authenticity, technical correctness, course approval and document layout need separate review')
    return {'errors': errors, 'warnings': warnings,
            'summary': {'required_items': required_count, 'ready_ids': ready_ids,
                        'pending_ids': pending_ids, 'evidence_files_checked': checked}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--evidence', type=Path, help='optional evidence-register JSON file')
    parser.add_argument('--check-files', action='store_true', help='check referenced local files exist and are non-empty')
    parser.add_argument('--require-ready', action='store_true', help='reject unverified/incomplete required items')
    args = parser.parse_args()
    results: dict[str, Any] = {}
    try:
        results['package'] = validate_package(args.skill_root.resolve())
        if args.evidence:
            path = args.evidence.resolve()
            data = json.loads(path.read_text(encoding='utf-8-sig'))
            results['register'] = validate_record(data, path.parent, check_files=args.check_files,
                                                  require_ready=args.require_ready)
        elif args.check_files or args.require_ready:
            parser.error('--check-files and --require-ready require --evidence')
    except (OSError, UnicodeError, ValueError) as exc:
        results['input_error'] = {'errors': [str(exc)], 'warnings': [], 'summary': {}}
    ok = all(not value['errors'] for value in results.values())
    print(json.dumps({'ok': ok, 'meaning': 'structural and consistency checks only',
                      'results': results}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
